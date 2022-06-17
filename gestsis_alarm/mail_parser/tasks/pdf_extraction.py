from pdfminer.high_level import extract_text, extract_text_to_fp, extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTChar, LTFigure, LTLine, LTRect, LTTextLine
from enum import Enum
import re


class ReadingMode(Enum):
    MESSAGE = 1,
    SEARCH_SIS = 2
    SEARCH_FIREFIGHTER = 3


class PDFData:
    alarm_type = None
    lv95_coordinate = None
    event_address = None
    firefighter_coming = {}

    def add_message_info(self, alarm_type, event_address, lv95_coordinate):
        self.alarm_type = alarm_type
        self.lv95_coordinate = lv95_coordinate
        self.event_address = event_address

    def add_firefighters(self, sis, group, firefighters):
        if sis not in self.firefighter_coming:
            self.firefighter_coming[sis] = {}

        if group not in self.firefighter_coming[sis]:
            self.firefighter_coming[sis][group] = [e for e in firefighters]

    def __str__(self):
        return "Alarm Type: {}\nLV95: {}\nAddress: {}\nFirefighters: {}".format(self.alarm_type, self.lv95_coordinate, self.event_address, self.firefighter_coming)


class PDFExtractor:

    def __init__(self):
        self.re_patter_firefighter = re.compile(r"([\w ]+) (SMS|Paging|Téléphone) {2}((?:\+)?\d+) ([a-zA-Zé ]+)", flags=re.UNICODE)

    def extract_data(self, filename: str):

        data_extracted = PDFData()

        # Search for the information given at the first page (Alarm type, address, coordinates, etc.)
        message = self._extract_message(filename)
        data_extracted.add_message_info(message[0], message[1], message[2])

        # The loop here is to found firefighter and there respective group and SIS

        current_sis_found = None
        current_group_found = None
        current_firefighter_found = []

        reading_mode = None

        for page_layout in extract_pages(filename, laparams=LAParams(line_margin=0.5, boxes_flow=1, char_margin=25)):

            for element in page_layout:

                print(element)
                print(type(element))

                if self._filter_garbage(element):
                    continue

                if reading_mode is None:
                    # The list of firefighter only appears after "Statistiques par Service"
                    if isinstance(element, LTTextContainer) and element.get_text() == "Statistiques par Service\n":
                        reading_mode = ReadingMode.SEARCH_SIS
                        continue

                if reading_mode == ReadingMode.SEARCH_SIS:

                    if self._is_it_sis_title(element):
                        print("SIS FOUND")

                        if current_group_found is not None:
                            data_extracted.add_firefighters(current_sis_found, current_group_found, current_firefighter_found)

                        current_group_found, current_sis_found = self._extract_sis_title(title_text=element.get_text())
                        current_firefighter_found = []
                        continue

                    if isinstance(element, LTTextContainer):
                        for el in element:
                            if isinstance(el, LTTextLine):
                                match_firefighter = self.re_patter_firefighter.match(el.get_text().strip())
                                if match_firefighter and match_firefighter.group(4) == "Vient":
                                    current_firefighter_found.append(match_firefighter.group(1))
                                    print(current_firefighter_found)
                                elif self._is_it_sis_title(el):
                                    if current_group_found is not None:
                                        data_extracted.add_firefighters(current_sis_found, current_group_found, current_firefighter_found)
                                    print(el.get_text())
                                    current_group_found, current_sis_found = self._extract_sis_title(title_text=el.get_text())
                                    current_firefighter_found = []

                                print(match_firefighter)

                    print("MODE CHANGED")

        return data_extracted

    def _extract_message(self, filename):
        """
        Search and extract information given in the first page (ie. Alarm type, address, coordinates, ...)
        :param filename: Filename of the PDF
        :return: A tuple containing the information otherwise None if nothing is found
        """
        page_layout = next(extract_pages(filename, maxpages=1, laparams=LAParams(line_margin=2, boxes_flow=0.8)))

        for element in page_layout:
            # Search for the string "Message".
            # With the parameter given to pdfminer.six, the title "Message" and the message content are glued together
            if isinstance(element, LTTextContainer) and element.get_text().startswith("Message\n"):
                return self._extract_info_from_message(element.get_text().replace("Message\n", ""))

        return None

    @staticmethod
    def _extract_info_from_message(text):
        # Remove line return in the middle of the string and split
        cleaned = text.replace("\n", "").split(";")
        cleaned = [element.strip() for element in cleaned]

        if len(cleaned) != 5:
            raise Exception("Invalid message, cannot retrieve informations, aborting...")

        # 0 is Alarm type
        # 1 is address (and complement)
        # 2 is intervention complement
        # 3 is LV95 coordinate
        # 4 is "CET JU"
        return cleaned[0], cleaned[1], cleaned[3]

    @staticmethod
    def _filter_garbage(element):
        if isinstance(element, LTFigure) or isinstance(element, LTLine) or isinstance(element, LTRect):
            return False

        if isinstance(element, LTTextContainer) and re.match(r"Page: \d+", element.get_text()):
            print("FOOTER")
            return True

        return False

    @staticmethod
    def _is_it_sis_title(title_element):
        if isinstance(title_element, LTTextLine):
            first_char = next(title_element.__iter__())
        elif isinstance(title_element, LTTextContainer):
            first_char = next(next(title_element.__iter__()).__iter__())
        else:
            return False

        return round(first_char.size) == 12

    @staticmethod
    def _extract_sis_title(title_text: str):
        a = title_text.split(",")
        if len(a) == 2:
            return [e.strip() for e in a]

        return [e.strip() for e in title_text.split(" - ")]


if __name__ == "__main__":
    extractor = PDFExtractor()
    data = extractor.extract_data("pdf/test_real.pdf")
    print(data)