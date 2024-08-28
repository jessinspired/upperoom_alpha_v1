from django.contrib import admin
from .models import (
    Client,
    Creator,
    ClientProfile,
    CreatorProfile,
    User
)

from .admin_models import (
    UserAdmin,
    CreatorAdmin,
    ClientAdmin,
)

admin.site.register(User, UserAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Creator, CreatorAdmin)

admin.site.register(ClientProfile)
admin.site.register(CreatorProfile)
