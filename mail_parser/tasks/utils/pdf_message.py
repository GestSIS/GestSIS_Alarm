from dataclasses import dataclass


@dataclass
class PDFMessage:
    code: str
    couleur: str
    lv95_coordinate: str
    event_address: str
    intervention_complement: str

    def __str__(self):
        return "Alarm Type: {} {}\nLV95 Coordinates: {}\nEvent Address: {}\nIntervention Complement: {}"\
            .format(self.code, self.couleur, self.lv95_coordinate, self.event_address, self.intervention_complement)
