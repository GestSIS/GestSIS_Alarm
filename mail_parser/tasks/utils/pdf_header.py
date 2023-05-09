from dataclasses import dataclass
from .pdf_message import PDFMessage

@dataclass
class PDFHeader:
    alarm_type: str
    date_creation: str
    debut_alarme: str
    fin_alarme: str
    description: str
    message: PDFMessage

    def __str__(self):
        return "Description: {}\nAlarm Type: \nCréation: {}\nDébut alarme: {}\nFin Alarme: {}\nMessage: {}"\
            .format(self.description, self.alarm_type, self.date_creation, self.debut_alarme, self.fin_alarme, self.message)
