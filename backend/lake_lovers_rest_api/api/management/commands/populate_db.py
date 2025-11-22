from django.core.management.base import BaseCommand
from api.models import Data

class Command(BaseCommand):
    help = 'Creates application data'

    def handle(self, *args, **kwargs):

        # create products - name, desc, price, stock, image
        data_set = [
            Data(location = "Ormajärvi (35.792.1.001)/Havaintopaikka 2",
                coordinates = "61° 5' 24.14\" N, 24° 57' 26.17\" E",
                operator = "Hämeen elinkeino-, liikenne- ja ympäristökeskus",
                date = "2025-06-28T17:22:00",
                level = 3,
                txt = "",
                tracking = "-",
                upkeep = "Tavallisen käyttäjän ylläpitämä",
                description = "" ),
        ]

        # create products & re-fetch from DB
        Data.objects.bulk_create(data_set)
        data_set = Data.objects.all()
