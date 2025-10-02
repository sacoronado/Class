import pandas as pd
import json
from supabase import create_client
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def load_to_supabase():
    with open('nicholas_cage_processed_movies.json', 'r') as f:
        movies_data = json.load(f)
    
    print(f"Loaded {len(movies_data)} movies from JSON")
    
    df = pd.DataFrame(movies_data)
    
    current_time = datetime.now().isoformat()
    df['extracted_at'] = current_time
    df['updated_at'] = current_time
    
    df = df.rename(columns={
        'rank': 'imdb_rank',
        'release_year': 'year'
    })
    
    if 'role' not in df.columns:
        df['role'] = 'Unknown'
    
    if 'summary' not in df.columns:
        df['summary'] = 'Description not available'
    
    print("Sample data:")
    print(df[['imdb_rank', 'title', 'year', 'imdb_rating']].head())
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    supabase = create_client(supabase_url, supabase_key)
    
    df['genres'] = df['genres'].apply(lambda x: x if isinstance(x, list) else [])
    
    records = df.to_dict('records')
    
    # First delete all existing records
    supabase.table('nicholas_cage_movies').delete().neq('id', 0).execute()
    
    # Then insert new records
    response = supabase.table('nicholas_cage_movies').insert(records).execute()
    
    print(f"Loaded {len(records)} movies to Supabase")
    
    verify_response = supabase.table('nicholas_cage_movies').select('*', count='exact').execute()
    print(f"Total movies in database: {len(verify_response.data)}")
    
    return True

if __name__ == "__main__":
    print("Nicholas Cage Movies - Supabase Loader")
    load_to_supabase()