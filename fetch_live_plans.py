
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DATASTATION_TOKEN")
# Try both base URLs as we are not 100% sure which one works yet (verification was cancelled)
BASE_URLS = [
    "https://datastation.com.ng/api",
    "https://datastationapi.com/api"
]

HEADERS = {
    "Authorization": TOKEN,
    "Content-Type": "application/json"
}

def fetch_plans():
    for base in BASE_URLS:
        print(f"Trying {base}...")
        try:
            # Endpoint guess based on utils/datastation.py: /data/ (GET)
            url = f"{base}/data/"
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                print("SUCCESS: Connected.")
                try:
                    data = response.json()
                    # Datastation structure varies. Usually 'results' or just a list or 'Dataplan'
                    # Let's print structure info
                    print(json.dumps(data, indent=2)[:1000]) # First 1k chars
                    return
                except:
                    print("Could not parse JSON.")
                    print(response.text[:500])
                    return
            else:
                print(f"Failed with {response.status_code}")
                print(response.text[:200])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fetch_plans()
