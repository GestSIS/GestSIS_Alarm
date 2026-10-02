import time

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.test import APIClient, APIRequestFactory

from mail_parser.models import Alarm, Sis
from .exceptions import custom_exception_handler


class FakeUser:
    """
    Minimal stand-in for admin_panel.models.TokenUser, used with
    force_authenticate() to exercise views without going through real JWTs.
    """

    is_authenticated = True

    def __init__(self, is_admin=False, sis_permissions=None):
        self.is_admin = is_admin
        self._sis_permissions = sis_permissions or []

    def get_sis_for_permissions(self, permissions):
        return self._sis_permissions


class CustomExceptionHandlerTest(TestCase):
    def test_wraps_plain_detail_into_message(self):
        response = custom_exception_handler(
            PermissionDenied("nope"), {"request": APIRequestFactory().get("/")}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {"message": "nope"})

    def test_wraps_not_found_detail_into_message(self):
        response = custom_exception_handler(
            NotFound(), {"request": APIRequestFactory().get("/")}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"message": "Not found."})

    def test_wraps_field_errors_into_message_and_errors(self):
        response = custom_exception_handler(
            ValidationError({"has_been_read": ["Missing/Invalid has_been_read in body"]}),
            {"request": APIRequestFactory().get("/")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"], {
            "has_been_read": ["Missing/Invalid has_been_read in body"]
        })
        self.assertIn("message", response.data)

    def test_returns_none_when_default_handler_does_not_handle_exception(self):
        self.assertIsNone(
            custom_exception_handler(Exception("boom"), {"request": None})
        )


class AlarmViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.sis_a = Sis.objects.create(name="SIS A", gestsis_key="a")
        self.sis_b = Sis.objects.create(name="SIS B", gestsis_key="b")

    def test_non_admin_without_permission_on_requested_sis_key_gets_wrapped_message(self):
        user = FakeUser(is_admin=False, sis_permissions=["a"])
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/v1/alarm/", HTTP_SIS_KEY="b")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data,
            {"message": "Insufficient permission to retrieve the SIS data specified"},
        )

    def test_admin_lists_alarms_as_plain_array(self):
        user = FakeUser(is_admin=True)
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/v1/alarm/")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)


class AlarmSetterUpdateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.sis_a = Sis.objects.create(name="SIS A", gestsis_key="a")
        self.alarm = Alarm.objects.create(address="1 rue Test", complement="")
        self.alarm.sis.add(self.sis_a)

    def url(self, pk):
        return f"/api/v1/alarm/{pk}/reading-status/"

    def test_forbidden_when_user_lacks_permission_on_alarm_sis(self):
        user = FakeUser(is_admin=False, sis_permissions=["other"])
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.url(self.alarm.pk), {"has_been_read": True}, format="json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data, {"message": "Invalid permission to access this object"}
        )

    def test_missing_has_been_read_returns_message_and_errors(self):
        user = FakeUser(is_admin=True)
        self.client.force_authenticate(user=user)

        response = self.client.patch(self.url(self.alarm.pk), {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["errors"],
            {"has_been_read": ["Missing/Invalid has_been_read in body"]},
        )
        self.assertIn("message", response.data)

    def test_success_returns_data_without_redundant_message(self):
        user = FakeUser(is_admin=True)
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.url(self.alarm.pk), {"has_been_read": True}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"data": {"id": self.alarm.pk, "has_been_read": True}},
        )

    def test_not_found_returns_wrapped_message(self):
        user = FakeUser(is_admin=True)
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.url(999999), {"has_been_read": True}, format="json"
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("message", response.data)


class JwtAudienceValidationTest(TestCase):
    """
    Régression : sans `AUDIENCE` dans `SIMPLE_JWT`, simplejwt n'exerce
    aucun contrôle sur le claim `aud` (`verify_aud` reste False). GestSIS_Auth
    émet des jetons à portée restreinte (2FA pre-auth/setup, `aud` distinct de
    "GestSIS_API") destinés uniquement à ses propres endpoints 2FA — Alarm
    doit les rejeter comme le fait déjà GestSIS_API, pas les traiter comme un
    jeton d'accès complet.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        cls.public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def setUp(self):
        self.client = APIClient()
        self.sis_a = Sis.objects.create(name="SIS A", gestsis_key="a")

    def _token(self, aud):
        now = int(time.time())
        payload = {
            "iss": "GestSIS_Auth",
            "aud": aud,
            "iat": now,
            "exp": now + 300,
            "data": {"id": 1, "admin": True},
        }
        return jwt.encode(payload, self.private_pem, algorithm="RS256")

    def test_a_full_access_token_is_accepted(self):
        with override_settings(
            SIMPLE_JWT={**settings.SIMPLE_JWT, "VERIFYING_KEY": self.public_pem}
        ):
            response = self.client.get(
                "/api/v1/alarm/",
                HTTP_AUTHORIZATION=f"Bearer {self._token('GestSIS_API')}",
            )

        self.assertEqual(response.status_code, 200)

    def test_a_two_factor_pre_auth_token_is_rejected(self):
        with override_settings(
            SIMPLE_JWT={**settings.SIMPLE_JWT, "VERIFYING_KEY": self.public_pem}
        ):
            response = self.client.get(
                "/api/v1/alarm/",
                HTTP_AUTHORIZATION=f"Bearer {self._token('GestSIS_Auth_2FA')}",
            )

        self.assertEqual(response.status_code, 401)

    def test_a_two_factor_setup_token_is_rejected(self):
        with override_settings(
            SIMPLE_JWT={**settings.SIMPLE_JWT, "VERIFYING_KEY": self.public_pem}
        ):
            response = self.client.get(
                "/api/v1/alarm/",
                HTTP_AUTHORIZATION=f"Bearer {self._token('GestSIS_Auth_2FA_SETUP')}",
            )

        self.assertEqual(response.status_code, 401)
