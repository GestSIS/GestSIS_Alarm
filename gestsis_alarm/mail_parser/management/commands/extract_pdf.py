import sys

from django.core.management import BaseCommand
import os.path
from django.conf import settings
from ...tasks.pdf_extraction import PDFExtractor, PDFExtractionException
from ...models import Alarm, File, Firefighter, Sis
from ...utils.lv95_converter import convert_lv95_to_wgs84


class Command(BaseCommand):
    help = "Extract data from the mobilisation report"

    def add_arguments(self, parser):

        def file_path(string: str):
            if not os.path.isabs(string):
                string = os.path.join(settings.MEDIA_ROOT, string)

            if os.path.exists(string):
                return string
            else:
                raise FileNotFoundError(string)

        parser.add_argument('pdf_file', type=file_path,
                            help="Path to the pdf file, can be absolute or relative. If relative, the root folder is 'storage'")

    def handle(self, *args, **options):

        if not os.path.isabs(options["pdf_file"]):
            options["pdf_file"] = os.path.join(settings.MEDIA_ROOT, options["pdf_file"])

        allowed_sis = Sis.objects.values_list("name", flat=True)
        extractor = PDFExtractor(allowed_sis)

        try:
            data = extractor.extract_data(options["pdf_file"])
        except PDFExtractionException as e:
            print("ERROR while parsing : {}".format(e.message), file=sys.stderr)
            return

        wgs84_coord = convert_lv95_to_wgs84(data.message.lv95_coordinate)

        if wgs84_coord is None:
            print("ERROR while converting the coordinates ! (Given: {})".format(data.message.lv95_coordinate))
            return

        print(data)

        print("Saving in Database...", end="")

        a = Alarm(
            location_lv95=data.message.lv95_coordinate,
            location_wgs84="{},{}".format(str(wgs84_coord[0]), str(wgs84_coord[1])),
            complement=data.message.intervention_complement,
            address=data.message.event_address,
            type=data.message.alarm_type,
        )

        a.save()

        firefighters = []
        firefighters_relations = []

        firefighters_in_db = list(Firefighter.objects.all())

        for sis, groups in data.firefighter_coming.items():
            s = Sis.objects.get(name=sis)
            a.sis.add(s)

            for group, people in groups.items():
                for person in people:
                    f = Firefighter(fullname=person["name"], phone=person["phone"], group=group, sis=s)
                    if f not in firefighters_in_db:
                        firefighters.append(f)
                        firefighters_relations.append(Alarm.firefighter.through(firefighter=f, alarm=a))

        # bulk_create doesn't support many-to-many relationship, so we have to create the entry in the relationship table manually
        Firefighter.objects.bulk_create(firefighters)
        Alarm.firefighter.through.objects.bulk_create(firefighters_relations)

        print("DONE")
