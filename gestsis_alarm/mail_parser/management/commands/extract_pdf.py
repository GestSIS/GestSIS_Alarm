import sys

from django.core.management import BaseCommand
import os.path
from django.conf import settings
from ...tasks.pdf_extraction import PDFExtractor, PDFExtractionException


class Command(BaseCommand):
    help = "Extract data from the mobilisation report"

    def add_arguments(self, parser):

        def file_path(string: str):
            if not os.path.isabs(string):
                string = os.path.join(settings.MEDIA_ROOT, string)

            if os.path.exists(string):
                return string
            else:
                raise FileNotFoundError(string)

        parser.add_argument('pdf_file', type=file_path,
                            help="Path to the pdf file, can be absolute or relative. If relative, the root folder is 'storage'")

    def handle(self, *args, **options):

        if not os.path.isabs(options["pdf_file"]):
            options["pdf_file"] = os.path.join(settings.MEDIA_ROOT, options["pdf_file"])

        # The SIS will be retrieve from the database. This variable is just temporary and for test purpose
        allowed_sis = [
            "SIS Basse-Allaine", "SIS Val-Terbi", "SIS Vendline", "SIS Clos-du-Doubs", "SIS FM Centre", "SIS FM Ouest",
            "SIS Haute-Sorne", "SIS Calabri", "SIS Baroche", "SIS 6/12", "SIS Haut-Plateau", "SIS Mont-Terri"
        ]

        extractor = PDFExtractor(allowed_sis)

        try:
            data = extractor.extract_data(options["pdf_file"])
        except PDFExtractionException as e:
            print("ERROR while parsing : {}".format(e.message), file=sys.stderr)
            return

        print(data)
