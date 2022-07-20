from django.db import models
from django.utils.functional import cached_property


class TokenUser:
    """
    Model used by Simple JWT to map a token to a non-existent user
    """

    is_active = True
    is_authenticated = True

    def __init__(self, token):
        self.token = token

    @cached_property
    def id(self):
        return self.token["data"]["id"]

    @cached_property
    def pk(self):
        return self.id

    @cached_property
    def username(self):
        return self.token["data"]["pseudo"]

    @cached_property
    def email(self):
        return self.token["data"]["email"]

    @cached_property
    def permissions(self):
        return self.token["data"]["permissions"]

    @cached_property
    def mobiles(self):
        return self.token["data"]["mobiles"]

    @cached_property
    def is_admin(self):
        return True  # TODO: Need to be retrieve from the token
