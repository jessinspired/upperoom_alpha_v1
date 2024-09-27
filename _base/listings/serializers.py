from rest_framework import serializers
from .models import LodgeImage, RoomProfileImage


class LodgeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LodgeImage
        fields = '__all__'


class RoomProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomProfileImage
        fields = '__all__'
