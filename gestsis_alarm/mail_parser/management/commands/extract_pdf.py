from django.core.management import BaseCommand
import os.path
from django.conf import settings
from ...tasks.pdf_extraction import PDFExtractor


class Command(BaseCommand):
    help = "Retrieve PDF from mail server and store it into the pdf folder"

    _required_options = ["server", "port", "username", "password", "whitelisted_mails"]

    def add_arguments(self, parser):

        def file_path(string: str):
            if not os.path.isabs(string):
                string = os.path.join(settings.MEDIA_ROOT, string)

            if os.path.exists(string):
                return string
            else:
                raise FileNotFoundError(string)

        parser.add_argument('pdf_file', type=file_path, help="Path to the pdf file, can be absolute or relative. If relative, the root folder is storage")

    def handle(self, *args, **options):

        if not os.path.isabs(options["pdf_file"]):
            options["pdf_file"] = os.path.join(settings.MEDIA_ROOT, options["pdf_file"])

        extractor = PDFExtractor()
        data = extractor.extract_data(options["pdf_file"])
        print(data)
