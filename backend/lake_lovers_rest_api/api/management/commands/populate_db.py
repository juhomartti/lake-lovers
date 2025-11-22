from django.core.management.base import BaseCommand
from api.models import Data
import pandas as pd
import re

class Command(BaseCommand):
    help = 'Creates application data'

    def dms_to_dd(self, dms_str):
        """
        Muuntaa koordinaattimerkkijonon (DMS) desimaaliasteiksi (DD).
        """
        if not isinstance(dms_str, str):
            return None
        
        match = re.search(r'(\d+)\D+(\d+)\D+([\d\.]+)\D+([NnSsEeWw])', dms_str)
        
        if match:
            degrees = float(match.group(1))
            minutes = float(match.group(2))
            seconds = float(match.group(3))
            direction = match.group(4).upper()

            decimal_degrees = degrees + minutes / 60 + seconds / 3600

            if direction in ('S', 'W'):
                decimal_degrees *= -1
                
            return decimal_degrees
        return None

    def db_upload(self):
        try:
            df = pd.read_csv("result.csv", sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv("result.csv", sep=';', encoding='iso-8859-1')
        except FileNotFoundError:
            print(f"VIRHE: Tiedostoa ei löytynyt polusta:")
            exit()

        # 2. Koordinaattien muunnos (DMS -> DD)
        df['Koordinaatit_Clean'] = df['Koordinaatit'].str.replace('"', '').str.strip()
        df[['Leveysaste_DMS', 'Pituusaste_DMS']] = df['Koordinaatit_Clean'].str.split(',', expand=True)

        df['Latitude_DD'] = df['Leveysaste_DMS'].apply(self.dms_to_dd)
        df['Longitude_DD'] = df['Pituusaste_DMS'].apply(self.dms_to_dd)

        # 3. Päivämäärän muunnos
        df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'], errors='coerce')

        # 4. Turhien/Puuttuvien sarakkeiden/rivien poisto
        df = df.drop(columns=['Koordinaatit', 'Koordinaatit_Clean', 'Leveysaste_DMS', 'Pituusaste_DMS'])
        # Poistetaan rivit, joissa ei ole päivämäärää tai koordinaatteja
        df = df.dropna(subset=['Päivämäärä', 'Latitude_DD', 'Longitude_DD'])

        print(f"Puhdistetussa datassa on {len(df)} kelvollista havaintoa.")

        data = []

        for index, row in df.iterrows():
            data.append(
                Data(
                    location = row['Havaintopaikka'],
                    operator = row['ELY-keskus'],
                    date = row['Päivämäärä'],
                    level = row['LevätilanneNum'],
                    txt = row['LevätilanneTxt'],
                    tracking = row['Seuranta'],
                    upkeep = row['Ylläpito'],
                    description = row['Lisätiedot'],
                    latitude = row['Latitude_DD'],
                    longitude = row['Longitude_DD'],
                )
            )
        return data

    def handle(self, *args, **kwargs):           

        # create products - name, desc, price, stock, image
        data_set = self.db_upload()

        # create products & re-fetch from DB
        Data.objects.bulk_create(data_set)
        data_set = Data.objects.all()
