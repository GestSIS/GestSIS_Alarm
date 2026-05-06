from django.core.management import BaseCommand
from django.conf import settings
from ...tasks.mail_retriever import MailRetriever
from ...tasks.pdf_extraction import (
    PDFExtractor,
    PDFExtractionException,
    MeteoSuisseAlarm,
)
from ...models import Sis
import os
import glob
import traceback

import logging

logger = logging.getLogger("main")


class Command(BaseCommand):
    help = "Test PDF parsing without saving to database and report errors"

    def add_arguments(self, parser):
        parser.add_argument(
            "--retrieve-mails",
            action="store_true",
            default=False,
            help="Retrieve emails from mail server before testing PDFs",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number to process: emails if --retrieve-mails is set, otherwise existing PDFs (takes the N most recent files)",
        )
        parser.add_argument(
            "--pattern",
            type=str,
            default=None,
            help="Filter PDF files by pattern (e.g., '2026_05_*'). Ignored if --file is used.",
        )
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Test a specific PDF file (filename only, not full path)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Display detailed information for all files, including successful ones",
        )

    def handle(self, *args, **options):
        # Step 1: Retrieve emails if requested
        if options["retrieve_mails"]:
            self._retrieve_emails(options)

        # Step 2: Get list of PDF files to test
        pdf_files = self._get_pdf_files(options)

        if not pdf_files:
            self.stdout.write(self.style.WARNING("No PDF files found to test"))
            return

        # Step 3: Test each PDF
        results = self._test_pdfs(pdf_files, options["verbose"])

        # Step 4: Display report
        self._display_report(results)

    def _retrieve_emails(self, options):
        """Retrieve emails from mail server"""
        self.stdout.write(self.style.NOTICE("Retrieving emails from mail server..."))

        server = os.environ.get("GESTSIS_ALARM_MAIL_SERVER")
        port = os.environ.get("GESTSIS_ALARM_MAIL_PORT")
        username = os.environ.get("GESTSIS_ALARM_MAIL_USERNAME")
        password = os.environ.get("GESTSIS_ALARM_MAIL_PASSWORD")
        whitelisted_mails = os.environ.get("GESTSIS_ALARM_MAIL_WHITELIST")

        if None in [server, port, username, password, whitelisted_mails]:
            self.stderr.write(
                self.style.ERROR(
                    "Missing environment variables for mail retrieval. Check your .env file!"
                )
            )
            return

        use_starttls = os.environ.get("GESTSIS_ALARM_MAIL_USE_STARTTLS", "false").lower() == "true"

        mc = MailRetriever(
            server,
            port,
            username,
            password,
            whitelisted_mails.split(","),
            use_starttls,
        )

        # Use include_read=True to retrieve already read emails for testing
        pdf_downloaded = mc.check_for_new_messages(
            include_read=True, limit=options["limit"]
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Retrieved {len(pdf_downloaded)} file(s) from mail server"
            )
        )
        for filename in pdf_downloaded:
            self.stdout.write(f"  - {filename}")

    def _get_pdf_files(self, options):
        """Get list of PDF files to test based on options"""
        pdf_dir = os.path.join(settings.MEDIA_ROOT, "pdf")

        # If specific file is requested
        if options["file"]:
            filepath = os.path.join(pdf_dir, options["file"])
            if os.path.exists(filepath):
                return [options["file"]]
            else:
                self.stderr.write(
                    self.style.ERROR(f"File not found: {options['file']}")
                )
                return []

        # Get all PDFs or filtered by pattern
        if options["pattern"]:
            pattern = os.path.join(pdf_dir, options["pattern"])
            files = glob.glob(pattern)
        else:
            pattern = os.path.join(pdf_dir, "*.pdf")
            files = glob.glob(pattern)

        # Convert to relative filenames
        pdf_files = [os.path.basename(f) for f in sorted(files)]

        # Apply limit if specified
        if options["limit"] and not options["retrieve_mails"]:
            # Take the last N files (most recent based on filename timestamp)
            pdf_files = pdf_files[-options["limit"] :]

        return pdf_files

    def _test_pdfs(self, pdf_files, verbose):
        """Test parsing of PDF files and return results"""
        self.stdout.write(
            self.style.NOTICE(f"\nTesting {len(pdf_files)} PDF file(s)...\n")
        )

        allowed_sis = Sis.objects.values_list("name", flat=True)
        results = {"success": [], "failed": [], "skipped": []}

        for i, filename in enumerate(pdf_files, 1):
            filepath = os.path.join(settings.MEDIA_ROOT, "pdf", filename)

            self.stdout.write(f"[{i}/{len(pdf_files)}] Testing {filename}... ", ending="")

            try:
                extractor = PDFExtractor(allowed_sis)
                data = extractor.extract_data(filepath)

                # Extraction successful
                results["success"].append(
                    {
                        "filename": filename,
                        "data": data,
                    }
                )
                self.stdout.write(self.style.SUCCESS("✓ SUCCESS"))

                if verbose:
                    self._display_success_details(data)

            except MeteoSuisseAlarm as e:
                # MeteoSuisse alarm (expected skip)
                results["skipped"].append(
                    {
                        "filename": filename,
                        "error_type": "MeteoSuisseAlarm",
                        "message": e.message,
                    }
                )
                self.stdout.write(self.style.WARNING("⊘ SKIPPED (MeteoSuisse)"))

            except PDFExtractionException as e:
                # Known parsing error
                results["failed"].append(
                    {
                        "filename": filename,
                        "error_type": "PDFExtractionException",
                        "message": e.message,
                        "traceback": None,
                    }
                )
                self.stdout.write(self.style.ERROR("✗ FAILED"))

            except Exception as e:
                # Unexpected error
                results["failed"].append(
                    {
                        "filename": filename,
                        "error_type": type(e).__name__,
                        "message": str(e),
                        "traceback": traceback.format_exc(),
                    }
                )
                self.stdout.write(self.style.ERROR("✗ FAILED (Unexpected)"))

        return results

    def _display_success_details(self, data):
        """Display details for successfully parsed PDF"""
        self.stdout.write(f"    Type: {data.header.alarm_type}")
        self.stdout.write(
            f"    Code: {data.header.message.code} | Couleur: {data.header.message.couleur}"
        )
        self.stdout.write(f"    Address: {data.header.message.event_address}")
        if data.header.message.lv95_coordinate:
            self.stdout.write(f"    LV95: {data.header.message.lv95_coordinate}")

        # Count firefighters
        total_firefighters = 0
        for sis_groups in data.firefighter_coming.values():
            for group_data in sis_groups.values():
                total_firefighters += len(group_data["firefighters"])

        self.stdout.write(f"    Firefighters: {total_firefighters}")

    def _display_report(self, results):
        """Display final test report"""
        total = len(results["success"]) + len(results["failed"]) + len(results["skipped"])

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.NOTICE("TEST REPORT"))
        self.stdout.write("=" * 80 + "\n")

        # Statistics
        self.stdout.write(f"Total files tested: {total}")
        self.stdout.write(
            self.style.SUCCESS(f"✓ Successful:       {len(results['success'])}")
        )
        self.stdout.write(
            self.style.WARNING(f"⊘ Skipped:          {len(results['skipped'])}")
        )
        self.stdout.write(
            self.style.ERROR(f"✗ Failed:           {len(results['failed'])}")
        )

        if total > 0:
            success_rate = (len(results["success"]) / total) * 100
            self.stdout.write(f"\nSuccess rate: {success_rate:.1f}%\n")

        # Display successful files
        if results["success"]:
            self.stdout.write("\n" + "-" * 80)
            self.stdout.write(self.style.SUCCESS("SUCCESSFUL FILES:"))
            self.stdout.write("-" * 80)
            for item in results["success"]:
                data = item["data"]
                self.stdout.write(
                    f"  ✓ {item['filename']}: {data.header.message.code}:{data.header.message.couleur} - {data.header.message.event_address}"
                )

        # Display skipped files
        if results["skipped"]:
            self.stdout.write("\n" + "-" * 80)
            self.stdout.write(self.style.WARNING("SKIPPED FILES (MeteoSuisse):"))
            self.stdout.write("-" * 80)
            for item in results["skipped"]:
                self.stdout.write(f"  ⊘ {item['filename']}")
                self.stdout.write(f"     Reason: {item['message']}")

        # Display failed files with details
        if results["failed"]:
            self.stdout.write("\n" + "-" * 80)
            self.stdout.write(self.style.ERROR("FAILED FILES:"))
            self.stdout.write("-" * 80)
            for item in results["failed"]:
                self.stdout.write(f"\n  ✗ {item['filename']}")
                self.stdout.write(f"     Error Type: {item['error_type']}")
                self.stdout.write(f"     Message: {item['message']}")

                if item["traceback"]:
                    self.stdout.write("\n     Traceback:")
                    for line in item["traceback"].split("\n"):
                        if line.strip():
                            self.stdout.write(f"       {line}")

        self.stdout.write("\n" + "=" * 80 + "\n")

        # Final message
        if results["failed"]:
            self.stdout.write(
                self.style.ERROR(
                    f"⚠ {len(results['failed'])} file(s) failed parsing. Review the details above."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✓ All files parsed successfully!")
            )
