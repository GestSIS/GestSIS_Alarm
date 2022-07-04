from ...tasks.mail_retriever import MailRetriever
from ...tasks.pdf_extraction import PDFExtractor
from ...models import Sis
from ._pdf_handling import PDFCommand
from django.conf import settings

import os

import logging
logger = logging.getLogger("main")


class Command(PDFCommand):
    help = "Retrieve mail from the mail server, extract data from the PDF and add it to the DB. Expected to be used in a cron job"

    def handle(self, *args, **options):
        logger.debug("Running mail_and_extract command")

        server = os.environ.get("GESTSIS_ALARM_MAIL_SERVER")
        port = os.environ.get("GESTSIS_ALARM_MAIL_PORT")
        username = os.environ.get("GESTSIS_ALARM_MAIL_USERNAME")
        password = os.environ.get("GESTSIS_ALARM_MAIL_PASSWORD")
        whitelisted_mails = os.environ.get("GESTSIS_ALARM_MAIL_WHITELIST")

        if None in [server, port, username, password, whitelisted_mails]:
            logger.error("Missing environment variables when retrieving mail")
            self.stderr.write(self.style.ERROR("Missing environment variables, check your .env file !"))
            return

        self.stdout.write("Scanning the mail server...")
        logger.info("Scanning mail server for new mails")

        mc = MailRetriever(server, port, username, password, whitelisted_mails.split(","))
        pdf_downloaded = mc.check_for_new_messages()

        allowed_sis = Sis.objects.values_list("name", flat=True)
        extractor = PDFExtractor(allowed_sis)

        self.stdout.write("Retrieved {} files from the mail server".format(len(pdf_downloaded)))
        logger.info("Retrieved {} files from the mail server".format(len(pdf_downloaded)))

        for pdf_file in pdf_downloaded:
            self.stdout.write(pdf_file)
            self._handle_pdf(pdf_file, os.path.join(settings.MEDIA_ROOT, "pdf", pdf_file), extractor)
