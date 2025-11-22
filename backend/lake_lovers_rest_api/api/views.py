from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Data
from .serializers import DataSerializer

class DataView(APIView):
    def get(self, request):
        items = Data.objects.all()
        serializer = DataSerializer(items, many=True)
        return Response(serializer.data)
