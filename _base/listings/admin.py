from django.contrib import admin
from .models import (
    State,
    Region,
    Landmark,
    School,
    Lodge,
    LodgeGroup,
    RoomType,
    RoomProfile,

)

from .admin_models import (
    StateAdmin,
    RegionAdmin,
    LandmarkAdmin,
    SchoolAdmin,
    LodgeAdmin,
    RoomProfileAdmin,
)

admin.site.register(State, StateAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(Landmark, LandmarkAdmin)
admin.site.register(School, SchoolAdmin)

admin.site.register(Lodge, LodgeAdmin)
admin.site.register(RoomType)
admin.site.register(RoomProfile, RoomProfileAdmin)


@admin.register(LodgeGroup)
class LodgeGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'landmark')
    search_fields = ('name',)
    list_filter = ('region', 'landmark')
    prepopulated_fields = {'name': ('name',)}
