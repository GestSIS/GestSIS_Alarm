from django.core.management import BaseCommand

from ...tasks.mail_retriever import MailRetriever
from ...tasks.pdf_extraction import PDFExtractor, PDFExtractionException
from ...models import Alarm, File, Firefighter, Sis
from ...utils.lv95_converter import convert_lv95_to_wgs84
from django.conf import settings

import os


class Command(BaseCommand):
    help = "Retrieve mail from the mail server, extract data from the PDF and add it to the DB. Expected to be used in a cron job"

    def handle(self, *args, **options):
        server = os.environ.get("GESTSIS_ALARM_MAIL_SERVER")
        port = os.environ.get("GESTSIS_ALARM_MAIL_PORT")
        username = os.environ.get("GESTSIS_ALARM_MAIL_USERNAME")
        password = os.environ.get("GESTSIS_ALARM_MAIL_PASSWORD")
        whitelisted_mails = os.environ.get("GESTSIS_ALARM_MAIL_WHITELIST")

        if None in [server, port, username, password, whitelisted_mails]:
            self.stderr.write(self.style.ERROR("Missing environment variables, check your .env file !"))
            return

        mc = MailRetriever(server, port, username, password, whitelisted_mails.split(","))
        pdf_downloaded = mc.check_for_new_messages()

        allowed_sis = Sis.objects.values_list("name", flat=True)
        extractor = PDFExtractor(allowed_sis)

        for pdf_file in pdf_downloaded:
            filepath = os.path.join(settings.MEDIA_ROOT, "pdf", pdf_file)
            self._handle_pdf(filepath, extractor)

    def _handle_pdf(self, file: str, extractor: PDFExtractor):

        try:
            data = extractor.extract_data(file)
        except PDFExtractionException as e:
            self.stderr.write(self.style.ERROR("ERROR while parsing : {}".format(e.message)))
            return

        wgs84_coord = convert_lv95_to_wgs84(data.message.lv95_coordinate)

        if wgs84_coord is None:
            self.stderr.write(self.style.ERROR("ERROR while converting the coordinates ! (Given: {})".format(data.message.lv95_coordinate)))
            return

        self.stdout.write("Saving in Database...", ending="")

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

        # Save file in database to prevent from reading it again
        file_obj = File(filename=file, alarm=a)
        file_obj.save()

        self.stdout.write(self.style.SUCCESS("DONE"))
