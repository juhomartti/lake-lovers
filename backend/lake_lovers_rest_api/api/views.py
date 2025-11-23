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

class DataView(APIView):
    def get(self, request):
        items = Data.objects.all()
        serializer = DataSerializer(items, many=True)
        return Response(serializer.data)
    
class ProvinceView(APIView):
    def post(self, request):
        serializer = ProvinceRequestSerializer(data=request.data)
        if serializer.is_valid():
            provinces = {
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

            items = Data.objects.raw(
                f"""
                SELECT * FROM api_data WHERE operator IS "{provinces[serializer.validated_data['province']]}"
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
            "Olet Suomen Ympäristökeskuksen (SYKE) asiantuntija. Tehtäväsi on laatia "
            "Tiedotteen tulee olla analyyttinen, yleistajuinen ja noudattaa Suomen vesistöjen "
            "virallista tiedotustyyliä. Vastaa AINOASTAAN englanniksi. Vastaa yhtenäisenä, useamman "
            "kappaleen raporttina, maksimissaan 100 sanaa."
        )

        user_prompt = f"""
        Analysoi alla oleva sinilevähavaintoja koskeva data ja laadi siitä tiivis, viikoittaista 
        sinilevätiedotetta vastaava yhteenveto. Muodosta tiedote seuraavien ohjeiden mukaisesti:



        1. Yleistilanne: Aloita kuvaamalla lyhyesti, minkälainen tilanne on sinilevän kanssa. "lat" ja "lon" kohdat ovat kordinaatit. Teenäiden mukaan alue analyyzi kuinka missäkin ely-keskuksessa on havantoja.
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

            print(response.text)
            return Response(response.model_dump_json())

        except Exception as e:
            print(f"VIRHE Geminin kutsussa: {e}")
            return Response(e)
        
class PredictView(APIView):
    def post(self, request):
        serializer = PredictSerializer(data=request.data)
        if serializer.is_valid():
            response = predict_func(serializer.validated_data["date"], serializer.validated_data["lat"], serializer.validated_data["lon"], serializer.validated_data["name"])
            return Response(response, status=200)
        return Response(serializer.error, status=400)