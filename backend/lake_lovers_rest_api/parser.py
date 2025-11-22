import sqlite3
import pandas as pd
#from api.models import Data

try:
    df = pd.read_csv('result.csv')
    print(df)
except FileNotFoundError:
    print("The file was not found.")
except Exception as e:
    print(f"An error occurred: {e}")

#Data.objects.bulk_create([Data(**item) for item in data])