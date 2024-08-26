from django.contrib import admin
from .models import (
    State,
    Area,
    Landmark,
    School,
    Lodge,
    RoomType,
    RoomProfile,

)

from .admin_models import (
    StateAdmin,
    AreaAdmin,
    LandmarkAdmin,
    SchoolAdmin,
    LodgeAdmin,
    RoomProfileAdmin,
)

admin.site.register(State, StateAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(Landmark, LandmarkAdmin)
admin.site.register(School, SchoolAdmin)

admin.site.register(Lodge, LodgeAdmin)
admin.site.register(RoomType)
admin.site.register(RoomProfile, RoomProfileAdmin)
