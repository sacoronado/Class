import os
from dotenv import load_dotenv

print("Current directory:", os.getcwd())
print("Files in directory:", [f for f in os.listdir('.') if f.endswith('.env') or f == '.env'])

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("SUPABASE_URL:", "FOUND" if url else "MISSING")
print("SUPABASE_KEY:", "FOUND" if key else "MISSING")

if url:
    print("URL starts with:", url[:20] + "...")
if key:
    print("Key starts with:", key[:10] + "...")