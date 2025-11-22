from rest_framework import serializers
from .models import Data, ProvinceRequest


class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = '__all__'

class ProvinceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProvinceRequest 
        fields = '__all__'