from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Data
from .serializers import DataSerializer, ProvinceRequestSerializer, PredictSerializer
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import requests
from .util.Ennustaja import predict_func
from .util.Ennustaja2 import ai_predict_hotspots
import json

PROVINCES = {
    1 : "Lapin elinkeino-, liikenne- ja ympäristökeskus",
    2 : "Pohjois-Pohjanmaan elinkeino-, liikenne- ja ympäristökeskus",
    3 : "Kainuun elinkeino-, liikenne- ja ympäristökeskus",
    4 : "Pohjanmaan elinkeino-, liikenne- ja ympäristökeskus",
    5 : "Etelä-Pohjanmaan elinkeino-, liikenne- ja ympäristökeskus",
    6 : "Keski-Suomen elinkeino-, liikenne- ja ympäristökeskus",
    7 : "Pohjois-Savon elinkeino-, liikenne- ja ympäristökeskus",
    8 : "Pohjois-Karjalan elinkeino-, liikenne- ja ympäristökeskus",
    9 : "Satakunnan elinkeino-, liikenne- ja ympäristökeskus",
    10 : "Pirkanmaan elinkeino-, liikenne- ja ympäristökeskus",
    11 : "Hämeen elinkeino-, liikenne- ja ympäristökeskus",
    12 : "Etelä-Savon elinkeino-, liikenne- ja ympäristökeskus",
    13 : "Kaakkois-Suomen elinkeino-, liikenne- ja ympäristökeskus",
    14 : "Varsinais-Suomen elinkeino-, liikenne- ja ympäristökeskus",
    15 : "Uudenmaan elinkeino-, liikenne- ja ympäristökeskus",
}

class DataView(APIView):
    def get(self, request):
        items = Data.objects.all()
        serializer = DataSerializer(items, many=True)

        try:
            response = requests.get("https://rajapinnat.ymparisto.fi/api/kansalaishavainnot/1.0/requests.json?service_code=algaebloom_service_code_201808151546171&extension=true")
        except Exception as e:
            print(e)
            response = ""

        api_data = json.loads(response.text)
        data = []

        for i in api_data:
            data_point = {
                "id": i["service_request_id"],
                "location": "",
                "operator": "",
                "date": i["requested_datetime"],
                "level": i["attributes"].get("algaebloom_singlevaluelist_201808151546174", 0),
                "txt": i["status"],
                "tracking": "",
                "upkeep": i["agency_responsible"],
                "description": i["description"],
                "latitude": i["lat"],
                "longitude": i["long"]
            },
            data.append(data_point[0])

        for i in serializer.data:
            for key, value in PROVINCES.items():
                if value == i["operator"]:
                    i["operator"] = key
                    break
            data.append(i)

        return Response(data, status=200)
    
class ProvinceView(APIView):
    def post(self, request):
        serializer = ProvinceRequestSerializer(data=request.data)
        if serializer.is_valid():
            items = Data.objects.raw(
                f"""
                SELECT * FROM api_data WHERE operator IS "{PROVINCES[serializer.validated_data['province']]}"
                AND date IS "{serializer.validated_data['date'].strftime('%Y-%m-%d')}"
                """
            )
            serializer_data = DataSerializer(items, many=True)
            return Response(serializer_data.data, status=201)
        return Response(serializer_data.error, status=400)    

class AiView(APIView):
    def get(self, request):
        
        try:
            response = requests.get("https://rajapinnat.ymparisto.fi/api/kansalaishavainnot/1.0/requests.json?service_code=algaebloom_service_code_201808151546171&extension=true")
        except Exception as e:
            print(e)
            response = ""

        ai_data = []

        for item in response:
            if (len(ai_data) > 100):
                break
            ai_data.append(item)
        
        load_dotenv()

        try:
    # client etsii API-avaimen automaattisesti ympäristömuuttujasta (GEMINI_API_KEY)
            client = genai.Client(api_key=os.getenv("API_KEY"))
        except Exception:
            print("\nVIRHE: Gemini API-avainta ei löytynyt. Aseta GEMINI_API_KEY (esim. VS Code .env-tiedostoon).")
            exit()

        # 1. PROMPT ENGINEERING (Rajauspromptit)
        # NYT ON VIELÄ VIIKOITTAINEN
        system_prompt = (
            "Olet Suomen Ympäristökeskuksen (SYKE) asiantuntija. Tehtäväsi on laatia tiivistelmä sinilevä tilanteesta."
            "Tiedotteen tulee olla analyyttinen, yleistajuinen ja noudattaa Suomen vesistöjen "
            "virallista tiedotustyyliä. Vastaa AINOASTAAN englanniksi. Vastaa yhtenäisenä, useamman "
            "kappaleen raporttina, maksimissaan 100 sanaa."
        )

        user_prompt = f"""
        Analysoi alla oleva sinilevähavaintoja koskeva data ja laadi siitä tiivis, viikoittaista 
        sinilevätiedotetta vastaava yhteenveto. Muodosta tiedote seuraavien ohjeiden mukaisesti:



        1. Yleistilanne: Aloita kuvaamalla lyhyesti, minkälainen tilanne on sinilevän kanssa. "lat" ja "lon" kohdat ovat kordinaatit. Teenäiden mukaan alue analyysi kuinka missäkin ely-keskuksessa on havantoja.
        Kohdssa "algaebloom_singlevaluelist_201808151546174" on sinilevän tasot. Tasot ovat 0: "Ei levää", 1: "Vähäinen määrä levää", 2: "Runsaasti levää", 3: "Erittäin runsaasti levää".
        2. Alueellinen katsaus: Nimeä ja kuvaile lyhyesti ne ELY-keskusten alueet (2-3 keskeisintä), joissa havaittiin eniten runsaita tai erittäin runsaita leväesiintymiä. Anna alueellinen yhteenveto, älä luettele yksittäisiä paikkoja.
        3. Loppuhuomio: Sisällytä lyhyt yhteenveto.
        4. Ohjeistus: Päätä tiedote lyhyeen ja ytimekkääseen ohjeistukseen toimenpiteistä sinilevän havaitsemisen varalle.

        DATA ALKAA TÄSTÄ:
        {ai_data}
        DATA PÄÄTTYY TÄHÄN.
        """

        # Mallin asetukset
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4, 
        )

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=config,
            )

            return Response(response.text, status=200)

        except Exception as e:
            print(f"VIRHE Geminin kutsussa: {e}")
            return Response(e, status=400)
        
class PredictView(APIView):
    def get(self, request):
        response = ai_predict_hotspots()
        print(response)
        return Response(response, status=200)

    def post(self, request):
        serializer = PredictSerializer(data=request.data)
        if serializer.is_valid():
            response = predict_func(serializer.validated_data["date"], serializer.validated_data["lat"], serializer.validated_data["lon"], serializer.validated_data["name"])
            return Response(response, status=200)
        return Response(serializer.error, status=400)
