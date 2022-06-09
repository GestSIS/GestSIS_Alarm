from django.core.management import BaseCommand
from ...tasks.mail_retriever import MailRetriever


class Command(BaseCommand):
    help = "Retrieve PDF from mail server and store it into the pdf folder"

    def add_arguments(self, parser):
        parser.add_argument('mail_server', type=str)
        parser.add_argument('port', type=int)
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('mails_to_whitelist', nargs='+', type=str)

    def handle(self, *args, **options):

        mc = MailRetriever(options["mail_server"], options["port"], options["username"], options["password"], options["mails_to_whitelist"])
        pdf_downloaded = mc.check_for_new_messages()
        print("{} file(s) retrieved".format(len(pdf_downloaded)))
        [print("- {}".format(f)) for f in pdf_downloaded]
