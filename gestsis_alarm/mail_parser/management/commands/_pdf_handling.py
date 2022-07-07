from django.core.management import BaseCommand

from ...tasks.pdf_extraction import PDFExtractor, PDFExtractionException
from ...models import Alarm, File, Firefighter, Sis
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
        except PDFExtractionException as e:
            logger.error("The parsing of {} raised an exception : {}".format(filename, e.message))
            self.stderr.write(self.style.ERROR("ERROR while parsing: {}".format(e.message)))
            return

        wgs84_coord = convert_lv95_to_wgs84(data.message.lv95_coordinate)
        if wgs84_coord is None:
            logger.warning("Invalid coordinates given to the converter ({})".format(data.message.lv95_coordinate))
            self.stderr.write(self.style.WARNING("WARNING Invalid coordinates given to the converter ! (Given: {})".format(data.message.lv95_coordinate)))

            # Empty the variable to prevent wrong coordinates to be added to the database
            data.message.lv95_coordinate = None
        else:
            wgs84_coord = "{},{}".format(str(wgs84_coord[0]), str(wgs84_coord[1]))

        logger.debug("Saving {} in the database".format(filename))
        self.stdout.write("Saving in Database...", ending="")

        a = Alarm(
            location_lv95=data.message.lv95_coordinate,
            location_wgs84=wgs84_coord,
            complement=data.message.intervention_complement,
            address=data.message.event_address,
            type=data.message.alarm_type,
        )

        a.save()

        # Add firefighters into the database
        firefighters = []
        firefighters_relations = []

        firefighters_in_db = list(Firefighter.objects.all())

        for sis, groups in data.firefighter_coming.items():
            s = Sis.objects.get(name=sis)
            a.sis.add(s)

            for group_name, group_data in groups.items():
                for person in group_data["firefighters"]:
                    f = Firefighter(fullname=person["name"], phone=person["phone"], sis=s,
                                    group_name=group_name, group_number=str(group_data["no"])
                                    )
                    if f not in firefighters_in_db:
                        firefighters.append(f)
                        firefighters_relations.append(Alarm.firefighter.through(firefighter=f, alarm=a))

        # bulk_create doesn't support many-to-many relationship, so we have to create the entry in the relationship table manually
        Firefighter.objects.bulk_create(firefighters)
        Alarm.firefighter.through.objects.bulk_create(firefighters_relations)

        # Save file in database to prevent from reading it again
        file_obj = File(filename=filename, alarm=a)
        file_obj.save()

        logger.info("Successfully added {} in the database".format(filename))
        self.stdout.write(self.style.SUCCESS("DONE"))
