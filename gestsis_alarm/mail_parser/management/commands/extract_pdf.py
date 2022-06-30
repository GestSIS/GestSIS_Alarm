import sys

import os.path
from django.conf import settings
from ...tasks.pdf_extraction import PDFExtractor, PDFExtractionException
from ...models import Sis
from ...utils.lv95_converter import convert_lv95_to_wgs84
from ._pdf_handling import PDFCommand


class Command(PDFCommand):
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

        allowed_sis = Sis.objects.values_list("name", flat=True)
        extractor = PDFExtractor(allowed_sis)

        try:
            data = extractor.extract_data(options["pdf_file"])
        except PDFExtractionException as e:
            self.stderr.write(self.style.ERROR("ERROR while parsing : {}".format(e.message), file=sys.stderr))
            return

        wgs84_coord = convert_lv95_to_wgs84(data.message.lv95_coordinate)

        if wgs84_coord is None:
            self.stderr.write(self.style.ERROR("ERROR while converting the coordinates ! (Given: {})".format(data.message.lv95_coordinate)))
            return

        self.stdout.write(self.style.SUCCESS("Successfully extracted the following data :"))
        self.stdout.write(data)

