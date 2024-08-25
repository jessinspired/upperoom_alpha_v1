from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta


class EmailVerificationToken(models.Model):
    class Role(models.TextChoices):
        '''defines roles for users
        Args:
            models (TextChoices): Defines the role choices for users
        '''
        CREATOR = 'CREATOR', 'Creator'
        CLIENT = 'CLIENT', 'Client'

    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        null=False,
        blank=False,
        default='DEFAULT'
    )

    uuid_code = models.UUIDField(default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    expiry_date = models.DateTimeField()
    is_verified = models.BooleanField(
        default=False,
    )

    @classmethod
    def create_token(cls, email, role):
        expiry_date = timezone.now() + timedelta(minutes=30)
        token = cls.objects.create(
            email=email,
            expiry_date=expiry_date,
            role=role
        )
        return token

    @staticmethod
    def is_valid_token(uuid_code):
        try:
            token = EmailVerificationToken.objects.get(uuid_code=uuid_code)
            return token.expiry_date > timezone.now()
        except EmailVerificationToken.DoesNotExist:
            return False


# class SocialAuthData(models.Model):
#     class Platform(models.TextChoices):
#         '''defines roles for users
#         Args:
#             models (TextChoices): Defines the role choices for users
#         '''
#         FACEBOOK = 'FACEBOOK', 'Facebook'
#         GOOGLE = 'GOOGLE', 'Google'

#     platform = models.CharField(
#         max_length=50,
#         choices=Platform.choices,
#         null=False,
#         blank=False,
#     )

#     first_name = models.CharField(
#         max_length=50,
#         null=False,
#         blank=False,
#     )

#     last_name = models.CharField(
#         max_length=50,
#         null=False,
#         blank=False,
#     )

#     email = models.EmailField(unique=True, null=False, blank=False)

#     profile_picture_url = models.CharField(
#         max_length=300,
#         null=False,
#         blank=False,
#     )

#     tookan_id = models.CharField(
#         max_length=50,
#         null=False,
#         blank=False,
#     )
