from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("DATABASE_URL")
print(f"Testing connection to: {url}")

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        print("Connection successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Connection failed: {e}")
