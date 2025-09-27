from bs4 import BeautifulSoup
import requests
import pandas as pd
import json

def scrape_nicholas_cage_movies():
    url = 'https://www.imdb.com/list/ls086744766/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # IMDB often stores data in JSON-LD format
    script_data = soup.find('script', type='application/ld+json')
    movies_list = []
    
    if script_data:
        try:
            data = json.loads(script_data.string)
            if 'itemListElement' in data:
                for item in data['itemListElement']:
                    if 'item' in item:
                        movie_data = item['item']
                        movies_list.append({
                            'rank': item.get('position', 'N/A'),
                            'title': movie_data.get('name', 'N/A'),
                            'year': movie_data.get('datePublished', 'N/A'),
                            'rating': movie_data.get('aggregateRating', {}).get('ratingValue', 'N/A'),
                            'rating_count': movie_data.get('aggregateRating', {}).get('ratingCount', 'N/A'),
                            'genre': ', '.join(movie_data.get('genre', [])),
                            'url': movie_data.get('url', 'N/A')
                        })
        except:
            pass
    
    # If JSON approach fails, try direct HTML parsing
    if not movies_list:
        # Look for specific list item patterns
        items = soup.find_all('div', class_=lambda x: x and 'lister-item' in x)
        
        for index, item in enumerate(items, 1):
            try:
                # Title
                title_elem = item.find('h3').find('a') if item.find('h3') else None
                title = title_elem.text.strip() if title_elem else 'N/A'
                url = 'https://www.imdb.com' + title_elem['href'] if title_elem else 'N/A'
                
                # Year
                year_elem = item.find('span', class_='lister-item-year')
                year = year_elem.text.strip('() ') if year_elem else 'N/A'
                
                # Rating
                rating_elem = item.find('span', class_='ipl-rating-star__rating')
                rating = rating_elem.text if rating_elem else 'N/A'
                
                movies_list.append({
                    'rank': index,
                    'title': title,
                    'year': year,
                    'rating': rating,
                    'url': url
                })
            except:
                continue
    
    return movies_list

# Run the function
movies = scrape_nicholas_cage_movies()

if movies:
    df = pd.DataFrame(movies)
    df.to_csv('nicholas_cage_movies.csv', index=False)
    print(f"✅ Successfully extracted {len(movies)} movies!")
    print(df.head(10))
else:
    print("❌ Could not extract movies. The page structure may require different selectors.")