from django.core.management import BaseCommand

from ...tasks.pdf_extraction import (
    PDFExtractor,
    PDFExtractionException,
    MeteoSuisseAlarm,
)
from ...models import Alarm, File, Firefighter, Sis, Group
from ...utils.lv95_converter import convert_lv95_to_wgs84

import logging

logger = logging.getLogger("main")


class PDFCommand(BaseCommand):
    """
    BaseCommand class implementing a function to save PDF
    """

    def _handle_pdf(self, filename: str, filepath: str, extractor: PDFExtractor):
        """
        Extract data from a pdf and save it into the database
        :param
            filename: str
              Filename of the mobilisation report
        :param
            filepath: str
              Absolute path of the file (including filename)
        :param
            extractor: PDFExtractor
              Instance of extractor
        """

        if File.objects.filter(filename=filename).exists():
            logger.warning("File {} already exist in the database".format(filename))
            self.stdout.write(self.style.WARNING("File already in database, skipping"))
            return

        try:
            data = extractor.extract_data(filepath)
        except MeteoSuisseAlarm as e:
            logger.warning(
                "Extracted report identified as MeteoSuisse Alarm discarded : {} - {}".format(
                    filename,
                    e.message,
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "WARNING MeteoSuisse Alarm discarded : {} - {}".format(
                        filename,
                        e.message,
                    )
                )
            )
            return
        except PDFExtractionException as e:
            logger.error(
                "The parsing of {} raised an exception : {}".format(filename, e.message)
            )
            self.stderr.write(
                self.style.ERROR("ERROR while parsing: {}".format(e.message))
            )
            return

        wgs84_coord = convert_lv95_to_wgs84(data.header.message.lv95_coordinate)
        if wgs84_coord is None:
            logger.warning(
                "Invalid coordinates given to the converter ({})".format(
                    data.header.message.lv95_coordinate
                )
            )
            self.stderr.write(
                self.style.WARNING(
                    "WARNING Invalid coordinates given to the converter ! (Given: {})".format(
                        data.header.message.lv95_coordinate
                    )
                )
            )

            # Empty the variable to prevent wrong coordinates to be added to the database
            data.header.message.lv95_coordinate = None
        else:
            wgs84_coord = "{},{}".format(str(wgs84_coord[0]), str(wgs84_coord[1]))

        logger.debug("Saving {} in the database".format(filename))
        self.stdout.write(
            "Saving in Database - {} - {}:{}".format(
                data.header.date_creation,
                data.header.message.code,
                data.header.message.couleur,
            ),
            ending="",
        )

        a = Alarm(
            type=data.header.alarm_type,
            date_creation=data.header.date_creation,
            debut_alarme=data.header.debut_alarme,
            fin_alarme=data.header.fin_alarme,
            description=data.header.description,
            # Données du message
            code=data.header.message.code,
            couleur=data.header.message.couleur,
            address=data.header.message.event_address,
            location_lv95=data.header.message.lv95_coordinate,
            location_wgs84=wgs84_coord,
            complement=data.header.message.intervention_complement,
        )

        a.save()

        # Add firefighters into the database
        firefighters = []
        groups = []

        for sis, sis_groups in data.firefighter_coming.items():
            s = Sis.objects.get(name=sis)
            a.sis.add(s)

            for group_name, group_data in sis_groups.items():
                groups.append(
                    Group(sis=s, name=group_name, number=str(group_data["no"]), alarm=a)
                )
                for person in group_data["firefighters"]:
                    firefighters.append(
                        Firefighter(
                            fullname=person["name"],
                            phone=person["phone"],
                            sis=s,
                            group_name=group_name,
                            group_number=str(group_data["no"]),
                            alarm=a,
                        )
                    )

        Firefighter.objects.bulk_create(firefighters)
        Group.objects.bulk_create(groups)

        # Save file in database to prevent from reading it again
        file_obj = File(filename=filename, alarm=a)
        file_obj.save()

        logger.info("Successfully added {} in the database".format(filename))
        self.stdout.write(self.style.SUCCESS(" DONE"))
