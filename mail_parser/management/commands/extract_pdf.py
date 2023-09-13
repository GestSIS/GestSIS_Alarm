import os.path
from django.conf import settings
from ...tasks.pdf_extraction import PDFExtractor
from ...models import Sis
from ._pdf_handling import PDFCommand

import logging

logger = logging.getLogger("main")


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

        parser.add_argument(
            "pdf_file",
            type=file_path,
            help="Path to the pdf file, can be absolute or relative. If relative, the root folder is 'storage'",
        )

    def handle(self, *args, **options):
        logger.debug("Extract pdf information for {}".format(options["pdf_file"]))

        if not os.path.isabs(options["pdf_file"]):
            options["pdf_file"] = os.path.join(settings.MEDIA_ROOT, options["pdf_file"])

        allowed_sis = Sis.objects.values_list("name", flat=True)
        extractor = PDFExtractor(allowed_sis)

        self._handle_pdf(
            os.path.basename(options["pdf_file"]), options["pdf_file"], extractor
        )
