from .pdf_message import PDFMessage

class PDFData:
    """
    Sort of a container to store the information extracted from the PDF
    """
    message = None
    firefighter_coming = {}
    _current_group = None
    _current_sis = None

    def add_message_info(self, message: PDFMessage):
        self.message = message

    def add_firefighter_to_current_group(self, firefighter: str, phone: str):
        """
        Add Firefighter to the current group in the current SIS
        :param
            firefighter: str
              The name of the firefighter
        :param
            phone: str
              The phone number(s) of the firefighter, the string can contain multiple phone number
        :return True if the firefighter has been added, otherwise False
        """
        if not self._current_sis or not self._current_group:
            return False

        f = {
            "name": firefighter,
            "phone": phone
        }

        if f in self.firefighter_coming[self._current_sis][self._current_group]["firefighters"]:
            return False

        self.firefighter_coming[self._current_sis][self._current_group]["firefighters"].append(f)

        return True

    def add_sis(self, name: str):
        """
        Add SIS to the dictionary except if it's already in it.
        The variable current_sis is ALWAYS MODIFIED by each call, even if the SIS is already in the dictionary
        :param
            name: str
              Name of the SIS
        :return: True if the SIS has been added, otherwise False
        """
        self._current_sis = name

        if name in self.firefighter_coming:
            return False

        self.firefighter_coming[name] = {}

        return True

    def add_group(self, num: int, name: str):
        """
        Add a group to the dictionary except if it's already in it.
        The variable current_group is modified ONLY if the group is not in the current SIS.
        :param
            name: str
              Name of the group
        :param
            num: int
              Sort of ID of the group
        :return: True if the group has been added, otherwise False
        """

        if not self._current_sis or name in self.firefighter_coming[self._current_sis]:
            return False

        self.firefighter_coming[self._current_sis][name] = {"no": num, "firefighters": []}
        self._current_group = name

        return True

    def get_current_group(self):
        if not self._current_sis or not self._current_group:
            return None

        return self.firefighter_coming[self._current_sis][self._current_group]["firefighters"]

    def get_current_group_name(self):
        return "{}, {}".format(self._current_sis, self._current_group)

    def __str__(self):
        return "Message: {}\nFirefighters: {}".format(self.message, self.firefighter_coming)
