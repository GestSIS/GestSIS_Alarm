from unittest import TestCase
from gestsis_alarm.mail_parser.tasks.pdf_extraction import PDFExtractor, PDFExtractionException
from gestsis_alarm.mail_parser.tasks.utils.pdf_data import PDFData
from pathlib import Path

class TestPDFExtraction(TestCase):
    extractor = None
    pdf_dir = Path(Path(__file__).resolve().parent, "pdf")

    def setUp(self):
        allowed_sis = [
            "SIS Basse-Allaine", "SIS Val-Terbi", "SIS Vendline", "SIS Clos-du-Doubs", "SIS FM Centre", "SIS FM Ouest",
            "SIS Haute-Sorne", "SIS Calabri", "SIS Baroche", "SIS 6/12", "SIS Haut-Plateau", "SIS Mont-Terri"
        ]

        self.extractor = PDFExtractor(allowed_sis)

    def test_invalid_filename(self):
        """Use a filename that doesn't exist"""
        filename = "invalid_name.pdf"

        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_data(filename)

    def test_wrong_pdf(self):
        """Test with a file that doesn't have the correct architecture"""
        filename = Path(self.pdf_dir, "pagelabels.pdf")

        with self.assertRaises(PDFExtractionException):
            self.extractor.extract_data(filename)
