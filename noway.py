from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import json
from openai import OpenAI
import time
import sys

# LLM API Configuration
endpoint = "https://cdong1--azure-proxy-web-app.modal.run"
api_key = "supersecretkey"
deployment_name = "gpt-4o"

def setup_client():
    """Setup the OpenAI client with error handling"""
    try:
        client = OpenAI(
            base_url=endpoint,
            api_key=api_key
        )
        print("OpenAI client configured successfully")
        return client
    except Exception as e:
        print(f"Error setting up OpenAI client: {e}")
        return None

client = setup_client()

def debug_print(message):
    """Helper function to ensure output is flushed immediately"""
    print(message, flush=True)

def scrape_nicholas_cage_movies():
    """Scrape ALL Nicholas Cage movies from IMDB list with proper selectors"""
    debug_print("Starting web scraping...")
    
    url = 'https://www.imdb.com/list/ls086744766/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        debug_print("Making request to IMDB...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        movies_list = []
        
        # Debug: Save the HTML to see what we're working with
        with open('imdb_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        debug_print("Saved page HTML to 'imdb_page_debug.html' for inspection")
        
        # Try multiple selectors to find the movie containers
        selectors_to_try = [
            'div.lister-item',  # Traditional IMDB list selector
            'li.ipc-metadata-list-summary-item',  # New IMDB selector
            'div[data-testid="list-item"]',  # Test ID selector
            'h3 a[href*="/title/tt"]',  # Direct title links
        ]
        
        movie_containers = []
        for selector in selectors_to_try:
            found = soup.select(selector)
            debug_print(f"Selector '{selector}': found {len(found)} items")
            if found and len(found) > len(movie_containers):
                movie_containers = found
        
        # If still no containers, try finding by text content
        if not movie_containers:
            debug_print("Trying alternative approach - searching for movie links...")
            # Find all movie title links
            movie_links = soup.find_all('a', href=re.compile(r'/title/tt\d+'))
            debug_print(f"Found {len(movie_links)} movie links total")
            
            # Filter to get unique movies (avoid duplicates)
            unique_links = []
            seen_titles = set()
            for link in movie_links:
                title = link.text.strip()
                if title and title not in seen_titles and len(title) > 2:
                    seen_titles.add(title)
                    unique_links.append(link)
            
            movie_containers = unique_links
            debug_print(f"Found {len(movie_containers)} unique movie titles")
        
        debug_print(f"Total items to process: {len(movie_containers)}")
        
        # Process each movie container
        for index, container in enumerate(movie_containers, 1):
            try:
                debug_print(f"Processing item {index}...")
                
                # Extract title based on container type
                if container.name == 'a':  # Direct link element
                    movie_title = container.text.strip()
                    movie_url = "https://www.imdb.com" + container['href']
                    # Find parent container for additional info
                    parent = container.find_parent(['div', 'li'])
                else:  # Container element
                    title_link = container.find('a', href=re.compile(r'/title/tt'))
                    if title_link:
                        movie_title = title_link.text.strip()
                        movie_url = "https://www.imdb.com" + title_link['href']
                        parent = container
                    else:
                        # Try to extract text content directly
                        movie_title = container.get_text(strip=True)
                        movie_url = "N/A"
                        parent = container
                
                if not movie_title or movie_title == '...':
                    debug_print("Empty title, skipping")
                    continue
                
                debug_print(f"   Title: {movie_title}")
                
                # Extract year from the text around the title
                year_match = re.search(r'\((\d{4})\)', container.get_text())
                year = year_match.group(1) if year_match else "N/A"
                
                # Try to find rating
                rating_element = (container.find('span', class_='ipl-rating-star__rating') or 
                                container.find('span', class_=re.compile(r'rating')) or
                                container.find('div', class_=re.compile(r'rating')))
                rating = rating_element.text.strip() if rating_element else "N/A"
                
                # Try to find additional info from parent
                runtime = "N/A"
                genre = "N/A"
                if parent:
                    # Look for runtime
                    runtime_text = parent.get_text()
                    runtime_match = re.search(r'(\d+h\s*\d*min|\d+\s*min)', runtime_text)
                    if runtime_match:
                        runtime = runtime_match.group(1)
                    
                    # Look for genre
                    genre_elem = parent.find('span', class_='genre')
                    if genre_elem:
                        genre = genre_elem.text.strip()
                
                movies_list.append({
                    "raw_title": movie_title,
                    "raw_year": year,
                    "raw_rating": rating,
                    "raw_runtime": runtime,
                    "raw_genre": genre,
                    "raw_description": "N/A",
                    "raw_url": movie_url,
                    "raw_rank": index
                })
                
                debug_print(f"Added: {movie_title} ({year})")
                
            except Exception as e:
                debug_print(f"Error processing item {index}: {e}")
                continue
        
        debug_print(f"Successfully processed {len(movies_list)} movies")
        
        # If we still don't have enough movies, try a different approach
        if len(movies_list) < 50:
            debug_print("Trying secondary scraping approach...")
            secondary_movies = scrape_secondary_approach(soup)
            movies_list.extend(secondary_movies)
            debug_print(f"Total after secondary approach: {len(movies_list)} movies")
        
        return movies_list
        
    except Exception as e:
        debug_print(f"Error in web scraping: {e}")
        return []

def scrape_secondary_approach(soup):
    """Alternative scraping approach for IMDB lists"""
    movies_list = []
    
    # Look for JSON-LD data (IMDB often stores data this way)
    script_data = soup.find('script', type='application/ld+json')
    if script_data:
        try:
            data = json.loads(script_data.string)
            if 'itemListElement' in data:
                for item in data['itemListElement']:
                    if 'item' in item:
                        movie_data = item['item']
                        movies_list.append({
                            "raw_title": movie_data.get('name', 'N/A'),
                            "raw_year": movie_data.get('datePublished', 'N/A'),
                            "raw_rating": movie_data.get('aggregateRating', {}).get('ratingValue', 'N/A'),
                            "raw_runtime": "N/A",
                            "raw_genre": ', '.join(movie_data.get('genre', [])),
                            "raw_description": "N/A",
                            "raw_url": movie_data.get('url', 'N/A'),
                            "raw_rank": item.get('position', len(movies_list) + 1)
                        })
        except:
            pass
    
    return movies_list

def process_movies_with_llm(raw_movies, batch_size=15):
    """Process all movies with LLM, handling them in batches if needed"""
    if not raw_movies:
        return None
    
    debug_print(f"Processing {len(raw_movies)} movies with LLM...")
    
    # If we have many movies, process in batches
    if len(raw_movies) > batch_size:
        debug_print(f"Processing in batches of {batch_size}...")
        all_processed = []
        
        for i in range(0, len(raw_movies), batch_size):
            batch = raw_movies[i:i + batch_size]
            batch_num = i//batch_size + 1
            debug_print(f"   Processing batch {batch_num}/{(len(raw_movies)-1)//batch_size + 1}")
            
            processed_batch = process_single_batch(batch, batch_num)
            if processed_batch:
                all_processed.extend(processed_batch)
            else:
                # If LLM fails, use raw data as fallback
                fallback_batch = [{
                    "rank": movie["raw_rank"],
                    "title": movie["raw_title"],
                    "release_year": movie["raw_year"] if movie["raw_year"] != "N/A" else None,
                    "imdb_rating": float(movie["raw_rating"]) if movie["raw_rating"] != "N/A" else None,
                    "runtime": movie["raw_runtime"],
                    "genres": [movie["raw_genre"]] if movie["raw_genre"] != "N/A" else [],
                    "imdb_url": movie["raw_url"]
                } for movie in batch]
                all_processed.extend(fallback_batch)
                debug_print(f"Used fallback data for batch {batch_num}")
            
            time.sleep(1)  # Rate limiting
        
        return all_processed
    else:
        return process_single_batch(raw_movies)

def process_single_batch(movies, batch_num=1):
    """Process a single batch of movies with LLM"""
    debug_print(f"Sending batch {batch_num} to LLM ({len(movies)} movies)...")
    
    # Prepare the data for LLM
    movies_text = "MOVIE DATA TO PROCESS:\n\n"
    for movie in movies:
        movies_text += f"Rank: {movie['raw_rank']}\n"
        movies_text += f"Title: {movie['raw_title']}\n"
        movies_text += f"Year: {movie['raw_year']}\n"
        movies_text += f"Rating: {movie['raw_rating']}\n"
        movies_text += f"Runtime: {movie['raw_runtime']}\n"
        movies_text += f"Genre: {movie['raw_genre']}\n"
        movies_text += f"URL: {movie['raw_url']}\n"
        movies_text += "---\n"
    
    prompt = f"""
    Please convert this movie data into a clean JSON array. Return ONLY valid JSON, no other text.
    
    {movies_text}
    
    Required JSON format for each movie:
    {{
      "rank": 1,
      "title": "Clean Movie Title",
      "release_year": 2023,
      "imdb_rating": 8.5,
      "runtime": "136 min",
      "genres": ["Action", "Drama"],
      "imdb_url": "full_url"
    }}
    
    Instructions:
    1. Keep all movies in the order provided by rank
    2. Clean the titles - remove any extra numbers or symbols at the beginning
    3. Convert year to number if possible (use null if "N/A" or not a number)
    4. Convert rating to number if possible (use null if "N/A" or not a number)
    5. For genres, convert comma-separated strings to arrays
    6. Preserve the original rank number
    7. If any field is "N/A", use null instead
    
    Return a JSON array of movie objects.
    """
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise JSON formatter. You always return valid JSON arrays and nothing else. Make sure titles are clean and properly formatted."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=3000  # Increase tokens for larger batches
        )
        
        result = response.choices[0].message.content
        debug_print(f"LLM response received for batch {batch_num}")
        
        # Clean the response (remove markdown code blocks if present)
        cleaned_result = result.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON
        parsed_data = json.loads(cleaned_result)
        debug_print(f"Batch {batch_num} processed successfully: {len(parsed_data)} movies")
        return parsed_data
        
    except Exception as e:
        debug_print(f"Error processing batch {batch_num}: {e}")
        return None

def main():
    debug_print("Starting Nicholas Cage Movie Scraper with LLM Processing...")
    debug_print("=" * 60)
    
    # Test LLM connection first
    if not client:
        debug_print("LLM client not available")
        return
    
    # Step 1: Scrape raw data
    debug_print("Step 1: Scraping movie data...")
    raw_movies = scrape_nicholas_cage_movies()
    
    if not raw_movies:
        debug_print("No movies scraped. Exiting.")
        return
    
    debug_print(f"Scraped {len(raw_movies)} raw movies")
    
    # Step 2: Process with LLM (ALL movies)
    debug_print("Step 2: Processing ALL movies with LLM...")
    processed_movies = process_movies_with_llm(raw_movies, batch_size=15)
    
    # Step 3: Save results
    debug_print("Step 3: Saving results...")
    
    # Save raw data
    with open('nicholas_cage_raw_movies.json', 'w', encoding='utf-8') as f:
        json.dump(raw_movies, f, indent=2, ensure_ascii=False)
    debug_print(f"Raw data saved: {len(raw_movies)} movies")
    
    # Save processed data
    if processed_movies:
        with open('nicholas_cage_processed_movies.json', 'w', encoding='utf-8') as f:
            json.dump(processed_movies, f, indent=2, ensure_ascii=False)
        
        df = pd.DataFrame(processed_movies)
        df.to_csv('nicholas_cage_processed_movies.csv', index=False)
        
        debug_print(f"Processed data saved: {len(processed_movies)} movies")
        
        # Display summary
        debug_print("PROCESSING SUMMARY:")
        debug_print(f"   Raw movies scraped: {len(raw_movies)}")
        debug_print(f"   Movies processed by LLM: {len(processed_movies)}")
        
        debug_print("FIRST 5 PROCESSED MOVIES:")
        for movie in processed_movies[:5]:
            debug_print(f"   {movie.get('rank')}. {movie.get('title')} ({movie.get('release_year')}) - Rating: {movie.get('imdb_rating')}")
    
    else:
        debug_print("No movies were processed by LLM")
    
    debug_print("Script completed!")
    debug_print("Generated files:")
    debug_print("   - nicholas_cage_raw_movies.json")
    debug_print("   - nicholas_cage_processed_movies.json")
    debug_print("   - nicholas_cage_processed_movies.csv")
    debug_print("   - imdb_page_debug.html (for troubleshooting)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        debug_print("Script interrupted by user")
    except Exception as e:
        debug_print(f"Unexpected error: {e}")
        import traceback
        debug_print(traceback.format_exc())