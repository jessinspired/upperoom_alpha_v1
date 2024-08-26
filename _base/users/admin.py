from django.contrib import admin
from .models import (
    User,
    Client,
    Creator,
    ClientProfile,
    CreatorProfile,
)

from .admin_models import (
    CreatorAdmin,
    ClientAdmin,
)

admin.site.register(Client, ClientAdmin)
admin.site.register(Creator, CreatorAdmin)

admin.site.register(ClientProfile)
admin.site.register(CreatorProfile)
