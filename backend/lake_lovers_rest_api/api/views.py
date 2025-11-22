from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Data
from .serializers import DataSerializer
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json

class DataView(APIView):
    def get(self, request):
        items = Data.objects.all()
        serializer = DataSerializer(items, many=True)
        return Response(serializer.data)
    
class AiView(APIView):
    def get(self, request):
        items = Data.objects.raw(
            """
            SELECT * FROM api_data WHERE date BETWEEN '2025-07-02' AND '2025-07-12';
            """
        )
        serializer = DataSerializer(items, many=True)
        
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
            "viikoittainen sinilevätiedote 20 viimeisimmän päivän havaintojen perusteella. "
            "Tiedotteen tulee olla analyyttinen, yleistajuinen ja noudattaa Suomen vesistöjen "
            "virallista tiedotustyyliä. Vastaa AINOASTAAN suomeksi. Vastaa yhtenäisenä, useamman "
            "kappaleen raporttina, maksimissaan 400 sanaa."
        )

        user_prompt = f"""
        Analysoi alla oleva sinilevähavaintoja koskeva data ja laadi siitä tiivis, viikoittaista 
        sinilevätiedotetta vastaava yhteenveto. Muodosta tiedote seuraavien ohjeiden mukaisesti:

        1. Yleistilanne: Aloita kuvaamalla lyhyesti, kuinka monessa havainnossa havaittiin levää yleisesti (LevätilanneTxt != "Ei levää") ja kuinka monessa havaittiin runsas/erittäin runsas esiintymä.
        2. Alueellinen katsaus: Nimeä ja kuvaile lyhyesti ne ELY-keskusten alueet (2-3 keskeisintä), joissa havaittiin eniten runsaita tai erittäin runsaita leväesiintymiä. Anna alueellinen yhteenveto, älä luettele yksittäisiä paikkoja.
        3. Loppuhuomio: Sisällytä lyhyt yhteenveto.
        4. Ohjeistus: Päätä tiedote lyhyeen ja ytimekkääseen ohjeistukseen toimenpiteistä sinilevän havaitsemisen varalle.

        DATA ALKAA TÄSTÄ:
        {serializer.data}
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
            return Response(response.model_dump_json())

        except Exception as e:
            print(f"VIRHE Geminin kutsussa: {e}")
            return Response("moi")
