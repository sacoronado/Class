from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import json
from openai import OpenAI
import time

# LLM API Configuration
endpoint = "https://cdong1--azure-proxy-web-app.modal.run"
api_key = "supersecretkey"
deployment_name = "gpt-4o"
client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

def scrape_nicholas_cage_movies():
    """Scrape Nicholas Cage movies from IMDB list"""
    url = 'https://www.imdb.com/list/ls086744766/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    movies_list = []
    
    # Try different selectors for IMDB list pages
    selectors_to_try = [
        'div.lister-item-content',
        'div.lister-item',
        'div.list-item',
        'li.ipc-metadata-list-summary-item'
    ]
    
    movie_containers = None
    for selector in selectors_to_try:
        movie_containers = soup.select(selector)
        if movie_containers:
            print(f"Found {len(movie_containers)} movies using selector: {selector}")
            break
    
    if movie_containers:
        for index, container in enumerate(movie_containers, 1):
            try:
                # Extract movie information
                title_element = (container.find('h3', class_='lister-item-header') or 
                               container.find('a', href=re.compile(r'/title/tt')))
                
                if title_element and title_element.find('a'):
                    movie_title = title_element.find('a').text.strip()
                    movie_url = "https://www.imdb.com" + title_element.find('a')['href']
                else:
                    continue
                
                # Extract year
                year_element = container.find('span', class_='lister-item-year')
                year = year_element.text.strip('() ') if year_element else "N/A"
                
                # Extract rating
                rating_element = container.find('span', class_='ipl-rating-star__rating')
                rating = rating_element.text.strip() if rating_element else "N/A"
                
                # Extract runtime
                runtime_element = container.find('span', class_='runtime')
                runtime = runtime_element.text if runtime_element else "N/A"
                
                # Extract genre
                genre_element = container.find('span', class_='genre')
                genre = genre_element.text.strip() if genre_element else "N/A"
                
                # Extract description
                description_element = container.find('p', class_='')
                description = description_element.text.strip() if description_element else "N/A"
                
                movies_list.append({
                    "raw_title": movie_title,
                    "raw_year": year,
                    "raw_rating": rating,
                    "raw_runtime": runtime,
                    "raw_genre": genre,
                    "raw_description": description,
                    "raw_url": movie_url
                })
                
            except Exception as e:
                print(f"Error processing movie {index}: {e}")
                continue
    
    return movies_list

def format_movie_data_with_llm(raw_movies_data):
    """Use LLM to parse and format raw movie data into structured JSON"""
    
    # Prepare the raw data for the LLM
    raw_data_text = "RAW MOVIE DATA:\n\n"
    for i, movie in enumerate(raw_movies_data[:20]):  # Limit to first 20 for demo
        raw_data_text += f"Movie {i+1}:\n"
        raw_data_text += f"Title: {movie['raw_title']}\n"
        raw_data_text += f"Year: {movie['raw_year']}\n"
        raw_data_text += f"Rating: {movie['raw_rating']}\n"
        raw_data_text += f"Runtime: {movie['raw_runtime']}\n"
        raw_data_text += f"Genre: {movie['raw_genre']}\n"
        raw_data_text += f"Description: {movie['raw_description']}\n"
        raw_data_text += "---\n"
    
    prompt = f"""
    You are a data processing expert. I need you to parse raw movie data and convert it into a structured JSON format.
    
    {raw_data_text}
    
    Please analyze this raw movie data and convert it into a clean JSON array with the following structure for each movie:
    
    {{
      "movies": [
        {{
          "title": "clean movie title",
          "release_year": 2023,
          "imdb_rating": 8.5,
          "runtime_minutes": 120,
          "genres": ["Action", "Drama"],
          "brief_summary": "cleaned description",
          "imdb_url": "full_url",
          "actor_role": "extracted role if mentioned"
        }}
      ]
    }}
    
    Instructions:
    1. Clean the titles - remove any extra numbers or symbols
    2. Extract numeric year from year field (ignore text like '2023-2024')
    3. Convert ratings to float numbers
    4. Extract numeric minutes from runtime (e.g., '2h 15min' → 135)
    5. Split genres into arrays
    6. Extract Nicholas Cage's role from descriptions if mentioned (look for 'as [character]')
    7. Keep the URL as is
    8. If any field is "N/A", omit it or use null
    
    Return ONLY valid JSON, no other text.
    """
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a expert data parser that converts unstructured text into perfect JSON format. You always return valid JSON and nothing else."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1  # Low temperature for consistent formatting
        )
        
        # Parse the JSON response
        json_response = response.choices[0].message.content
        parsed_data = json.loads(json_response)
        return parsed_data
        
    except Exception as e:
        print(f"Error with LLM processing: {e}")
        return None

def process_movies_in_batches(raw_movies, batch_size=10):
    """Process movies in batches to avoid token limits"""
    all_processed_movies = []
    
    for i in range(0, len(raw_movies), batch_size):
        batch = raw_movies[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(raw_movies)-1)//batch_size + 1}")
        
        processed_batch = format_movie_data_with_llm(batch)
        if processed_batch and 'movies' in processed_batch:
            all_processed_movies.extend(processed_batch['movies'])
        
        # Add delay to avoid rate limiting
        time.sleep(1)
    
    return all_processed_movies

def main():
    print("🎬 Starting Nicholas Cage Movie Scraper with LLM Processing...")
    
    # Step 1: Scrape raw data
    print("📊 Step 1: Scraping raw movie data from IMDB...")
    raw_movies = scrape_nicholas_cage_movies()
    
    if not raw_movies:
        print("❌ No movies found. Exiting.")
        return
    
    print(f"✅ Successfully scraped {len(raw_movies)} raw movie entries")
    
    # Step 2: Process with LLM
    print("🤖 Step 2: Sending data to LLM for parsing and formatting...")
    
    # Process all movies (you might want to use batches for large datasets)
    if len(raw_movies) > 20:
        print(f"📦 Processing {len(raw_movies)} movies in batches...")
        processed_movies = process_movies_in_batches(raw_movies, batch_size=15)
    else:
        processed_data = format_movie_data_with_llm(raw_movies)
        processed_movies = processed_data['movies'] if processed_data else []
    
    if not processed_movies:
        print("❌ LLM processing failed. Saving raw data instead.")
        # Fallback: save raw data
        with open('nicholas_cage_movies_raw.json', 'w', encoding='utf-8') as f:
            json.dump(raw_movies, f, indent=2, ensure_ascii=False)
        df = pd.DataFrame(raw_movies)
        df.to_csv('nicholas_cage_movies_raw.csv', index=False)
        print("💾 Raw data saved to 'nicholas_cage_movies_raw.json' and '.csv'")
        return
    
    # Step 3: Save processed data
    print("💾 Step 3: Saving processed data...")
    
    # Save as JSON
    with open('nicholas_cage_movies_processed.json', 'w', encoding='utf-8') as f:
        json.dump({"movies": processed_movies}, f, indent=2, ensure_ascii=False)
    
    # Save as CSV
    df = pd.DataFrame(processed_movies)
    df.to_csv('nicholas_cage_movies_processed.csv', index=False)
    
    print(f"✅ Successfully processed and saved {len(processed_movies)} movies!")
    print("📁 Files created:")
    print("   - nicholas_cage_movies_processed.json")
    print("   - nicholas_cage_movies_processed.csv")
    
    # Display sample
    print("\n🎬 Sample of processed movies:")
    for i, movie in enumerate(processed_movies[:3]):
        print(f"{i+1}. {movie.get('title', 'N/A')} ({movie.get('release_year', 'N/A')})")
        print(f"   Rating: {movie.get('imdb_rating', 'N/A')} | Runtime: {movie.get('runtime_minutes', 'N/A')}min")
        print(f"   Genres: {', '.join(movie.get('genres', []))}")
        if movie.get('actor_role'):
            print(f"   Role: {movie['actor_role']}")
        print()

