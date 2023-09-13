from unittest import TestCase
from ..tasks.pdf_extraction import PDFExtractor, PDFExtractionException
from pathlib import Path


class TestPDFExtraction(TestCase):
    extractor = None
    pdf_dir = Path(Path(__file__).resolve().parent, "pdf")

    def setUp(self):
        allowed_sis = [
            "SIS Basse-Allaine",
            "SIS Val-Terbi",
            "SIS Vendline",
            "SIS Clos-du-Doubs",
            "SIS FM Centre",
            "SIS FM Ouest",
            "SIS Haute-Sorne",
            "SIS Calabri",
            "SIS Baroche",
            "SIS 6/12",
            "SIS Haut-Plateau",
            "SIS Mont-Terri",
        ]

        self.extractor = PDFExtractor(allowed_sis)

    def test_invalid_filename(self):
        """Use a filename that doesn't exist"""
        filename = "invalid_name.pdf"

        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_data(filename)

    def test_wrong_pdf(self):
        """Test with a file that doesn't have the correct architecture"""
        filename = Path(self.pdf_dir, "1_pagelabels.pdf")

        with self.assertRaises(PDFExtractionException):
            self.extractor.extract_data(filename)

    def test_message_missing_semicolon(self):
        """The message is almost correctly formed, only one semicolon is missing"""
        filename = Path(self.pdf_dir, "2_test_missing_semicolon.pdf")

        with self.assertRaises(PDFExtractionException) as e:
            self.extractor.extract_data(filename)
        self.assertEqual(
            e.exception.message, "Invalid message (Wrong number of semicolon)"
        )

    def test_message_not_an_intervention(self):
        """When the message received is not an intervention but only an information. This type of message could be received in production"""
        filename = Path(self.pdf_dir, "3_test_not_an_intervention.pdf")

        with self.assertRaises(PDFExtractionException) as e:
            self.extractor.extract_data(filename)
        self.assertEqual(
            e.exception.message, "Invalid message (Wrong number of semicolon)"
        )

    def test_message_extraction(self):
        """Test if the message is correctly extracted (without complement). Frequently occur in production"""
        filename = Path(self.pdf_dir, "4_test_valid.pdf")

        data = self.extractor.extract_data(filename)

        self.assertEqual(data.header.description, "Feu bâtiment")
        self.assertEqual(data.header.date_creation, "07/06/2021 00:35:15")
        self.assertEqual(data.header.debut_alarme, "07/06/2021 00:36:45")
        self.assertEqual(data.header.fin_alarme, "07/06/2021 00:40:37")
        self.assertEqual(data.header.alarm_type, "Alarme réelle")
        self.assertEqual(data.header.message.code, "FEU BAT")
        self.assertEqual(data.header.message.couleur, "ROUGE")
        self.assertEqual(data.header.message.lv95_coordinate, "2580000,1240000")
        self.assertEqual(
            data.header.message.event_address, "2800 Delémont, Vainqueurs 42"
        )
        self.assertEqual(data.header.message.intervention_complement, "")

    def test_message_extraction_complement(self):
        """Test if the message is correctly extracted (with complement)"""
        filename = Path(self.pdf_dir, "5_test_valid_complement.pdf")

        data = self.extractor.extract_data(filename)

        self.assertEqual(data.header.description, "Feu bâtiment")
        self.assertEqual(data.header.date_creation, "07/06/2021 00:35:15")
        self.assertEqual(data.header.debut_alarme, "07/06/2021 00:36:45")
        self.assertEqual(data.header.fin_alarme, "07/06/2021 00:40:37")
        self.assertEqual(data.header.alarm_type, "Alarme réelle")
        self.assertEqual(data.header.message.code, "FEU BAT")
        self.assertEqual(data.header.message.couleur, "ROUGE")
        self.assertEqual(data.header.message.lv95_coordinate, "2580000,1240000")
        self.assertEqual(
            data.header.message.event_address, "2800 Delémont, Vainqueurs 42"
        )
        self.assertEqual(data.header.message.intervention_complement, "Ferme brûlée")

    def test_firefighter_extraction(self):
        """Test if the correct firefighter are retrieve by the script. Check for 3 numbers and names with accents"""
        filename = Path(self.pdf_dir, "4_test_valid.pdf")

        data = self.extractor.extract_data(filename)

        firefighter_to_receive = {
            "SIS Haute-Sorne": {
                "EM": {
                    "no": 90,
                    "firefighters": [
                        {"name": "Couche Emily", "phone": "+41219853643"},
                        {"name": "De Santa Jérome", "phone": "+41806469435"},
                        {"name": "Membrez Lucas", "phone": "+41416011568"},
                        {"name": "Raposo Laëtitia", "phone": "+41431990211"},
                    ],
                },
                "1er secours": {
                    "no": 91,
                    "firefighters": [
                        {"name": "Allimann Gauthier", "phone": "+41422703100"},
                        {"name": "Bocks André", "phone": "+41637919225"},
                        {"name": "Cattin Réane", "phone": "+41919568736"},
                        {"name": "Girardin Joséphine", "phone": "+41463972764"},
                        {"name": "Wermeille Lucie", "phone": "+41358932833"},
                    ],
                },
            },
            "SIS Calabri": {
                "EM": {
                    "no": 90,
                    "firefighters": [
                        {
                            "name": "Tobler Daniel",
                            "phone": "+41258491517 +41838004532 +41792966875",
                        }
                    ],
                }
            },
        }

        self.maxDiff = None  # To have the full difference between the two dictionary if the test fails
        self.assertEqual(data.firefighter_coming, firefighter_to_receive)
