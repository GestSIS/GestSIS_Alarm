from django.test import SimpleTestCase
from django.core.management import call_command
from ..tasks.mail_retriever import MailRetriever
from io import StringIO


class TestMail(SimpleTestCase):
    mc = None

    def setUp(self):
        self.mc = MailRetriever()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "retrieve_mail",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_ada(self):
        pass
