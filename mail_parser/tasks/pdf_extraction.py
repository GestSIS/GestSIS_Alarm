from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTTextLine
from enum import Enum
import re
from collections import deque
from .utils.pdf_data import PDFData
from .utils.pdf_message import PDFMessage


class PDFExtractionException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ReadingMode(Enum):
    """
    States from the State Machine used for parsing
    """
    SEARCH_SIS = 1
    SEARCH_STATS = 2
    SEARCH_FIREFIGHTER = 3


class PDFExtractor:

    def __init__(self, sis_whitelist: list):
        """
        :param
            sis_whitelist: list
              A list containing the name of the different SIS that will have their data retrieved
        """
        self._sis_whitelist = sis_whitelist

        self.re_pattern_firefighter = re.compile(r"([\w\- ]+) (Téléphone) ((?: (?:(?:\+)?\d+)){1,2}) ([a-zA-Zé ]+)", flags=re.UNICODE)
        self.re_pattern_incomplete_firefighter = re.compile(r"([\w\- ]+) (Téléphone) ((?: (?:(?:\+)?\d+)){2})", flags=re.UNICODE)
        self.re_pattern_phone = re.compile(r"(?:(?:\+)?\d{5,})")

        self.re_pattern_stats_come = re.compile(r"Viennent: (\d+)")
        self.re_pattern_stats_dont_come = re.compile(r"Appelés: \d+ Ne viennent pas: (\d+)")

        self.re_pattern_sis_group = re.compile(r"\*?(\d+) ([\w\- ]+)", flags=re.UNICODE)

        self.data_extracted = PDFData()
        self.current_firefighter_real = None
        self.current_firefighter_stats = None

    def extract_data(self, filename: str):

        # Search for the information given at the first page (Alarm type, address, coordinates, etc.).
        # This needs to need done in a separate extraction
        # because the characters recognition parameters are not the same as the firefighters ones.
        message = self._extract_message(filename)
        self.data_extracted.add_message_info(message)

        # The loop here is to find firefighter and there respective group and SIS
        self._reset_current_stats()

        reading_mode = None
        last_text = None

        # Queue that stores the three last lines that the script has read
        last_lines = deque(maxlen=3)

        for page_layout in extract_pages(filename, laparams=LAParams(line_margin=0.5, boxes_flow=1, char_margin=25)):

            for element in page_layout:

                # Discard lines, figure and image from being processed
                if not isinstance(element, LTTextContainer):
                    continue

                last_lines.append(element.get_text().strip())

                if reading_mode is None:
                    # The list of firefighter only appears after "Statistiques par Service"
                    if element.get_text() == "Statistiques par Service\n":
                        reading_mode = ReadingMode.SEARCH_SIS
                        continue

                # Search for text similar to a title
                # It works because after "Statistiques par Service", the only titles are ones containing a group name
                elif reading_mode == ReadingMode.SEARCH_SIS:

                    for line in element:
                        if isinstance(line, LTTextLine):

                            if self._is_sis_title(line):

                                if self._evaluate_title(line):
                                    reading_mode = ReadingMode.SEARCH_STATS
                                    break

                                continue

                # Extract the number of firefighter coming.
                # It's used for verification when parsing the list of firefighter
                elif reading_mode == ReadingMode.SEARCH_STATS:

                    if self._evaluate_stat_mode(element, last_text):
                        reading_mode = ReadingMode.SEARCH_FIREFIGHTER
                        continue

                    last_text = element.get_text().strip()

                # Extract the list of firefighter that comes to the intervention
                elif reading_mode == ReadingMode.SEARCH_FIREFIGHTER:

                    for line in element:
                        if isinstance(line, LTTextLine):

                            match_firefighter = self.re_pattern_firefighter.match(line.get_text().strip())
                            if match_firefighter:
                                if (label := match_firefighter.group(4)) == "Vient":
                                    # The name is split and join back to back to remove multiple space between name
                                    self.data_extracted.add_firefighter_to_current_group(
                                        " ".join(match_firefighter.group(1).split()),
                                        match_firefighter.group(3).strip()
                                    )

                                if label in ["Pas atteint", "Ne vient pas"]:
                                    self.current_firefighter_real[label] += 1

                            # When a person has three phone numbers, the page layout breaks and the information
                            # are all over the place. Luckily, the pattern is always the same and we need to search
                            # for a phone number that is the only thing on the line
                            elif match := self.re_pattern_phone.match(line.get_text().strip()):
                                # Shouldn't happen, but we check that we have at least 3 lines in the queue
                                if len(last_lines) != 3:
                                    continue

                                self._handle_three_phone_numbers(match.group(0).strip(), last_lines)

                            elif self._is_sis_title(line):

                                self._verify_firefighter_extraction(
                                    self.data_extracted,
                                    self.current_firefighter_real,
                                    self.current_firefighter_stats
                                )

                                if self._evaluate_title(line):
                                    reading_mode = ReadingMode.SEARCH_STATS
                                    continue
                                else:
                                    reading_mode = ReadingMode.SEARCH_SIS
                                    break

        return self.data_extracted

    def _handle_three_phone_numbers(self, first_phone_number: str, last_lines: deque):
        """
        Handle the parsing of a person with three phone numbers
        :param
            first_phone_number: str
              The first phone number parsed by the script
        :param
            last_lines: deque
              A queue containing the last three lines read by the parser
        :return:
        """

        # The last_lines queue is composed has follow :
        # - 0 : Status : Pas atteint/Ne vient pas or Vient
        # - 1 : An incomplete firefighter line composed of the name and two phone numbers
        # - 2 : The third phone number

        # Check if the line before the phone number is an incomplete firefighter line
        if match_firefighter := self.re_pattern_incomplete_firefighter.match(last_lines[1]):
            if last_lines[0] == "Vient":
                self.data_extracted.add_firefighter_to_current_group(
                    " ".join(match_firefighter.group(1).split()),
                    " ".join(match_firefighter.group(3).split()) + " " + first_phone_number
                )
                return

            if (label := last_lines[0]) in ["Pas atteint", "Ne vient pas"]:
                self.current_firefighter_real[label] += 1
                return

    def _reset_current_stats(self):
        """
        Reset array used for statistics
        """
        self.current_firefighter_stats = {"Vient": -1, "Pas atteint": -1, "Ne vient pas": -1}
        self.current_firefighter_real = {"Pas atteint": 0, "Ne vient pas": 0}

    def _extract_message(self, filename: str):
        """
        Search and extract information given in the first page (ie. Alarm type, address, coordinates, ...)
        :param
            filename: str
              Filename of the PDF
        :raise PDFExtractionException If nothing is found
        :return: A tuple containing the information
        """
        page_layout = next(extract_pages(filename, maxpages=1, laparams=LAParams(line_margin=2, boxes_flow=0.8)))

        for element in page_layout:
            # Search for the string "Message".
            # With the parameters given to pdfminer.six, the title "Message" and the message content are glued together
            if isinstance(element, LTTextContainer) and element.get_text().startswith("Message\n"):
                return self._extract_info_from_message(element.get_text().replace("Message\n", ""))

        raise PDFExtractionException("Message not found")

    def _evaluate_title(self, line):
        group, sis = self._extract_sis_title(title_text=line.get_text())

        if sis not in self._sis_whitelist:
            return False

        # Extract the group id if present
        if isinstance(group, tuple):
            id_group, group_name = group
        else:
            id_group, group_name = None, group

        self.data_extracted.add_sis(sis)
        self.data_extracted.add_group(id_group, group_name)

        self._reset_current_stats()

        return True

    def _evaluate_stat_mode(self, element, last_text: str):
        """
        Evaluate the element (line) passed by parameters and see if it's a valid statistic (Come, Don't come, Didn't answer)
        :param
            element:
              The element to evaluate
        :param
            last_text: str
              The previous line in the text
        :param
            current_firefighter_stats: dict
              A dictionary containing the different values, must contains : "Vient", "Pas atteint" and "Ne vient pas"
        :return: True if all the statistics has been found, False otherwise
        """
        text = element.get_text().strip()

        if match_stats_come := self.re_pattern_stats_come.match(text):
            self.current_firefighter_stats["Vient"] = int(match_stats_come.group(1))

        elif match_stats_didnt_come := self.re_pattern_stats_dont_come.match(text):
            self.current_firefighter_stats["Ne vient pas"] = int(match_stats_didnt_come.group(1))

        elif text == "Pas répondus:":
            self.current_firefighter_stats["Pas atteint"] = 0 if not last_text else int(last_text)

        if -1 not in self.current_firefighter_stats.values():
            return True

        return False

    @staticmethod
    def _verify_firefighter_extraction(pdf_data: PDFData, other_data: dict, objective: dict):
        """
        Verify that the number of firefighters extracted in the list is the same as the one given in parameter
        :param
            pdf_data: PDFData
              The data extracted from the PDF
        :param
            other_data: dict
               The other data
        :param
            objective: dict
              The number of firefighter the group should have
        :raise: PDFExtractionException if the number is not the same
        """

        nb_ff = pdf_data.get_current_group()
        if nb_ff is not None:
            if len(nb_ff) == objective["Vient"] \
                    and other_data["Ne vient pas"] == objective["Ne vient pas"] \
                    and other_data["Pas atteint"] == objective["Pas atteint"]:
                print("Stats: Successfully parsed {} ({})".format(pdf_data.get_current_group_name(), objective))
            else:
                raise PDFExtractionException(
                    "Incorrect number of firefighter extracted for {}. (Come: {}/{}, Don't come: {}/{}, Didn't answer: {}/{})".format(
                        pdf_data.get_current_group_name(),
                        len(nb_ff),
                        objective["Vient"],
                        other_data["Ne vient pas"],
                        objective["Ne vient pas"],
                        other_data["Pas atteint"],
                        objective["Pas atteint"]
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
            raise PDFExtractionException("Invalid message (Wrong number of semicolon)")

        # 0 is Alarm type
        # 1 is address (and complement)
        # 2 is intervention complement
        # 3 is LV95 coordinate
        # 4 is "CET JU"
        return PDFMessage(alarm_type=cleaned[0], event_address=cleaned[1], intervention_complement=cleaned[2], lv95_coordinate=cleaned[3])

    @staticmethod
    def _is_sis_title(title_element):
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

    def _extract_sis_title(self, title_text: str):
        """
        Extract the group and SIS names from the string. Works both for comma and dash
        :param
            title_text: str
              The text (string) containing the group and the SIS
        :return: A tuple, with as first a tuple containing the group number and the group name and at second, the SIS.
            If the group name and id couldn't be separated, the first item is a string with the group number and name.
        """

        # Sometimes the separator between the group and the sis is a comma or a dash

        a = title_text.split(",")
        if len(a) == 2:
            title = [e.strip() for e in a]
        else:
            title = [e.strip() for e in title_text.split(" - ")]

        match = self.re_pattern_sis_group.match(title[0])
        if not match:
            return title

        return (int(match.group(1)), match.group(2)), title[1]
