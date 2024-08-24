from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    '''
    Basemodel class
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# class ImageOptimizationModel(models.Model):
#     def save(self, *args, **kwargs):
#         from cloudinary.uploader import upload
#         import os
#         from uuid import uuid4

#         get_file_path = kwargs.pop('get_file_path', None)
#         if self.image:
#             file_name_with_extension = os.path.basename(self.image.name)
#             file_name = os.path.splitext(file_name_with_extension)[0]
#             file_path = get_file_path(self, file_name)
#             public_id = file_path + str(uuid4())

#             response = upload(
#                 self.image,
#                 public_id=public_id,
#                 invalidate=True,
#                 transformation=[
#                     dict(
#                         width=1000,
#                         height=1000,
#                         crop="limit",
#                         fetch_format="auto",
#                         quality="auto:good"
#                     )
#                 ]
#             )

#             self.image = response['secure_url']
#         super().save(*args, **kwargs)

#     class Meta:
#         abstract = True
