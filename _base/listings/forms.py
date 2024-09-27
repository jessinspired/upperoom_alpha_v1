from django import forms
from django.core.validators import RegexValidator

from .models import (
    Lodge,
    RoomProfile,
    State,
    Region,
    Landmark,
    School,
    LodgeImage,
    RoomProfileImage
)


class LodgeRegistrationForm(forms.ModelForm):
    '''set basic info about lodge'''

    name = forms.CharField(
        # help_text="N/B: If lodge has no name, use the alias field below instead",
        required=False
    )

    alias = forms.CharField(
        # help_text=(
        #     '- Use this to identify nameless lodges in your dashboard.<br>'
        #     '- This name, however, would not be rendered for users to see'
        # ),
        required=False
    )

    phone_number = forms.CharField(
        # help_text="Number of lodge agent/caretaker"
    )

    class Meta:
        model = Lodge

        fields = [
            'name',
            'alias',
            'address',
            'phone_number',
            'state',
            'school',
            'region',
            'landmark',
            'room_types',
            # 'info'
        ]

        widgets = {
            'room_types': forms.CheckboxSelectMultiple()
        }

    def save(self, creator, commit=True):
        state_name = self.cleaned_data.get('state')
        state = State.objects.all().filter(name=state_name).first()

        school_name = self.cleaned_data.get('school')
        school = School.objects.all().filter(name=school_name).first()

        region_name = self.cleaned_data.get('region')
        region = Region.objects.all().filter(name=region_name).first()

        landmark_name = self.cleaned_data.get('landmark')
        if landmark_name:
            landmark = Landmark.objects.get(name=landmark_name)
        else:
            landmark = None

        room_types = self.cleaned_data.get('room_types')
        cover_image = self.cleaned_data.get('cover_image')
        rear_image = self.cleaned_data.get('rear_image')

        lodge = super().save(commit=False)
        if lodge.name:
            lodge.name = lodge.name.title()  # capitalize lodge name

        if lodge.alias:
            lodge.alias = lodge.alias.title()

        lodge.creator = creator
        lodge.state = state
        lodge.school = school
        lodge.region = region
        lodge.landmark = landmark

        if commit:
            lodge.save()
            lodge.room_types.set(room_types)

            for room_type in lodge.room_types.all():
                RoomProfile.objects.create(
                    lodge=lodge,
                    room_type=room_type
                )
            if cover_image:
                lodge.cover_image = cover_image

            if rear_image:
                lodge.rear_image = rear_image

        return lodge


class RoomProfileForm(forms.ModelForm):
    class Meta:
        model = RoomProfile
        fields = ['price', 'vacancy']

    def save(self, room_profile, commit=True):
        price = self.cleaned_data.get('price')
        vacancy = self.cleaned_data.get('vacancy')

        room_profile.price = price
        room_profile.vacancy = vacancy

        if vacancy == 0:
            room_profile.is_vacant = False
        elif vacancy > 0:
            room_profile.is_vacant = True

        if commit:
            room_profile.save()

        return room_profile


class LodgeImageForm(forms.ModelForm):
    class Meta:
        model = LodgeImage
        fields = ['lodge', 'image', 'category', 'description']


class RoomProfileImageForm(forms.ModelForm):
    class Meta:
        model = RoomProfileImage
        fields = ['room_profile', 'image']
