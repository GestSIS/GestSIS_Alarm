from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTTextLine
from enum import Enum
import re


class PDFExtractionException(Exception):
    pass


class ReadingMode(Enum):
    SEARCH_SIS = 1
    SEARCH_STATS = 2
    SEARCH_FIREFIGHTER = 3


class PDFData:
    """
    Sort of a container to store the information extracted from the PDF
    """
    alarm_type = None
    lv95_coordinate = None
    event_address = None
    firefighter_coming = {}
    _current_group = None
    _current_sis = None

    def add_message_info(self, alarm_type, event_address, lv95_coordinate):
        self.alarm_type = alarm_type
        self.lv95_coordinate = lv95_coordinate
        self.event_address = event_address

    def add_firefighter_to_current_group(self, firefighter: str):
        if not self._current_sis or not self._current_group:
            return False

        self.firefighter_coming[self._current_sis][self._current_group].append(firefighter)

        return True

    def add_sis(self, name: str):
        self._current_sis = name

        if name in self.firefighter_coming:
            return False

        self.firefighter_coming[name] = {}

        return True

    def add_group(self, name: str):
        if not self._current_sis or name in self.firefighter_coming[self._current_sis]:
            return False

        self.firefighter_coming[self._current_sis][name] = []
        self._current_group = name

        return True

    def get_current_group(self):
        if not self._current_sis or not self._current_group:
            return None

        return self.firefighter_coming[self._current_sis][self._current_group]

    def get_current_group_name(self):
        return "{}, {}".format(self._current_sis, self._current_group)

    def add_firefighters(self, sis, group, firefighters):
        if sis not in self.firefighter_coming:
            self.firefighter_coming[sis] = {}

        if group not in self.firefighter_coming[sis]:
            self.firefighter_coming[sis][group] = [e for e in firefighters]

    def __str__(self):
        return "Alarm Type: {}\nLV95: {}\nAddress: {}\nFirefighters: {}".format(self.alarm_type, self.lv95_coordinate, self.event_address,
                                                                                self.firefighter_coming)


class PDFExtractor:

    def __init__(self):
        self.re_patter_firefighter = re.compile(r"([\w\- ]+) (Téléphone) ((?: (?:(?:\+)?\d+)){1,2}) ([a-zA-Zé ]+)", flags=re.UNICODE)
        self.re_pattern_stats = re.compile(r"Viennent: (\d+)")

    def extract_data(self, filename: str):

        data_extracted = PDFData()

        # Search for the information given at the first page (Alarm type, address, coordinates, etc.)
        # This needs to need done in a separate extraction because the characters recognition parameters are not the same as the firefighters ones.
        message = self._extract_message(filename)
        data_extracted.add_message_info(message[0], message[1], message[2])

        # The loop here is to found firefighter and there respective group and SIS
        current_firefighter_stats = -1

        reading_mode = None

        for page_layout in extract_pages(filename, laparams=LAParams(line_margin=0.5, boxes_flow=1, char_margin=25)):

            for element in page_layout:

                # Discard lines, figure and image from being processed
                if not isinstance(element, LTTextContainer):
                    continue

                if reading_mode is None:
                    # The list of firefighter only appears after "Statistiques par Service"
                    if element.get_text() == "Statistiques par Service\n":
                        reading_mode = ReadingMode.SEARCH_SIS
                        continue

                # Search for text similar to a title
                # It works because after "Statistiques par Service", the only titles are ones containing a group name
                if reading_mode == ReadingMode.SEARCH_SIS:

                    if self._is_it_sis_title(element):
                        current_group, current_sis = self._extract_sis_title(title_text=element.get_text())
                        data_extracted.add_sis(current_sis)
                        data_extracted.add_group(current_group)

                        reading_mode = ReadingMode.SEARCH_STATS
                        continue

                # Extract the number of firefighter coming.
                # It's used for verification when parsing the list of firefighter
                if reading_mode == ReadingMode.SEARCH_STATS:

                    match_stats = self.re_pattern_stats.match(element.get_text().strip())

                    if match_stats:
                        current_firefighter_stats = int(match_stats.group(1))
                        reading_mode = ReadingMode.SEARCH_FIREFIGHTER
                        continue

                # Extract the list of firefighter that comes to the intervention
                if reading_mode == ReadingMode.SEARCH_FIREFIGHTER:

                    for el in element:
                        if isinstance(el, LTTextLine):

                            match_firefighter = self.re_patter_firefighter.match(el.get_text().strip())
                            if match_firefighter and match_firefighter.group(4) == "Vient":
                                # The name is split and join back to back to remove multiple space between name
                                data_extracted.add_firefighter_to_current_group(" ".join(match_firefighter.group(1).split()))

                            elif self._is_it_sis_title(el):
                                self._verify_firefighter_extraction(data_extracted, current_firefighter_stats)

                                current_group, current_sis = self._extract_sis_title(title_text=el.get_text())
                                data_extracted.add_sis(current_sis)
                                data_extracted.add_group(current_group)

                                reading_mode = ReadingMode.SEARCH_STATS
                                continue

        self._verify_firefighter_extraction(data_extracted, current_firefighter_stats)

        return data_extracted

    def _extract_message(self, filename: str):
        """
        Search and extract information given in the first page (ie. Alarm type, address, coordinates, ...)
        :param
            filename: str
              Filename of the PDF
        :return: A tuple containing the information otherwise None if nothing is found
        """
        page_layout = next(extract_pages(filename, maxpages=1, laparams=LAParams(line_margin=2, boxes_flow=0.8)))

        for element in page_layout:
            # Search for the string "Message".
            # With the parameters given to pdfminer.six, the title "Message" and the message content are glued together
            if isinstance(element, LTTextContainer) and element.get_text().startswith("Message\n"):
                return self._extract_info_from_message(element.get_text().replace("Message\n", ""))

        return None

    @staticmethod
    def _verify_firefighter_extraction(pdf_data: PDFData, objective: int):
        """
        Verify that the number of firefighters extracted in the list is the same as the one given in parameter
        :param
            pdf_data: PDFData
              The data extracted from the PDF
        :param
            objective: int
              The number of firefighter the group should have
        :raise: PDFExtractionException if the number is not the same
        """
        nb_ff = pdf_data.get_current_group()
        if nb_ff is not None:
            if len(nb_ff) == objective:
                print("Stats: Successfully parsed {} ({})".format(pdf_data.get_current_group_name(), objective))
            else:
                raise PDFExtractionException("Incorrect number of firefighter extracted for {}. (Objective: {}, Got: {})".format(
                    pdf_data.get_current_group_name(),
                    objective,
                    len(nb_ff)
                ))

    @staticmethod
    def _extract_info_from_message(message: str):
        """
        Return the information contained in the string. It must follow the format used by SAGA:
          Alarm type;address,address complement;intervention complement;LV95 coordinate;CET JU
        :param
            message: str
            The string containing the intervention information
        :return: A tuple containing alarm_type, address (and complement) and LV95 coordinates)
        :raise: PDFExtractionException if the format is not respected
        """
        # Remove line return in the middle of the string and split
        cleaned = message.replace("\n", "").split(";")
        cleaned = [element.strip() for element in cleaned]

        if len(cleaned) != 5:
            raise PDFExtractionException("Invalid message, cannot retrieve informations, aborting...")

        # 0 is Alarm type
        # 1 is address (and complement)
        # 2 is intervention complement
        # 3 is LV95 coordinate
        # 4 is "CET JU"
        return cleaned[0], cleaned[1], cleaned[3]

    @staticmethod
    def _is_it_sis_title(title_element):
        """
        Check if the current text is a title by verifying that the font size of the first character is 12
        :param
            title_element: LTTextLine, LTTextContainer
              Element containing the title
        :return: True if it is a title, otherwise False
        """

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
