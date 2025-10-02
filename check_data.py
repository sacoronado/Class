from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

def check_supabase_data():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Count total records
        count_response = supabase.table("nicholas_cage_movies").select("*", count='exact').execute()
        print(f"Total records in table: {len(count_response.data)}")
        
        # Show first 5 records
        response = supabase.table("nicholas_cage_movies").select("*").limit(5).execute()
        print("\nFirst 5 records:")
        for i, movie in enumerate(response.data, 1):
            print(f"{i}. {movie.get('title', 'N/A')} - Rating: {movie.get('imdb_rating', 'N/A')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_supabase_data()