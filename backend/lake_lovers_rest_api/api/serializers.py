from rest_framework import serializers
from .models import Data, ProvinceRequest, Predict


class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = '__all__'

class ProvinceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProvinceRequest 
        fields = '__all__'

class PredictSerializer(serializers.ModelSerializer):
    class Meta:
        model = Predict
        fields = '__all__'