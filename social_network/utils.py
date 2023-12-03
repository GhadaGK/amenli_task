from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six

class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )

token_generator = TokenGenerator()

def generate_tokens(user):
    access_token = token_generator.make_token(user)
    refresh_token = token_generator.make_token(user)
    return access_token, refresh_token
