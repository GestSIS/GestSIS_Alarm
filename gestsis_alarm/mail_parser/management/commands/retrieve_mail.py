from django.core.management import BaseCommand
from ...tasks.mail_retriever import MailRetriever

import os


class Command(BaseCommand):
    help = "Retrieve PDF from mail server and store it into the pdf folder"

    _required_options = ["server", "port", "username", "password", "whitelisted_mails"]

    def add_arguments(self, parser):
        parser.add_argument('--server', type=str, default=os.environ["GESTSIS_ALARM_MAIL_SERVER"],
                            help="Url of the mail server")
        parser.add_argument('--port', type=int, default=os.environ["GESTSIS_ALARM_MAIL_PORT"],
                            help="Port of the mail server")
        parser.add_argument('--username', type=str, default=os.environ["GESTSIS_ALARM_MAIL_USERNAME"],
                            help="Can be a username or your email address depending on your email provider")
        parser.add_argument('--password', type=str, default=os.environ["GESTSIS_ALARM_MAIL_PASSWORD"])
        parser.add_argument('--whitelisted-mails', nargs='+', type=str, default=os.environ["GESTSIS_ALARM_MAIL_WHITELIST"].split(","))

    def handle(self, *args, **options):

        for option in self._required_options:
            if not options[option]:
                raise ValueError("'{}' cannot be empty or None ! Specify it with the command line or in the .env file !".format(option))

        mc = MailRetriever(options["server"], options["port"], options["username"], options["password"], options["whitelisted_mails"])
        pdf_downloaded = mc.check_for_new_messages()
        print("{} file(s) retrieved".format(len(pdf_downloaded)))
        [print("- {}".format(f)) for f in pdf_downloaded]
