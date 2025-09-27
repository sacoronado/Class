from bs4 import BeautifulSoup
import requests
import re
import pandas as pd

# Downloading imdb top 250 movie's data
url = 'https://www.imdb.com/chart/top/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Updated selectors for current IMDB structure
movies = soup.select('li.ipc-metadata-list-summary-item')
list = []

for index, movie in enumerate(movies):
    try:
        # Extract title
        title_element = movie.select_one('h3.ipc-title__text')
        if title_element:
            title_text = title_element.get_text().strip()
            # Remove ranking number from title (e.g., "1. The Shawshank Redemption" -> "The Shawshank Redemption")
            title_parts = title_text.split('. ', 1)
            movie_title = title_parts[1] if len(title_parts) > 1 else title_parts[0]
            place = title_parts[0] if len(title_parts) > 1 else str(index + 1)
        else:
            continue
        
        # Extract year
        year_element = movie.select_one('span.cli-title-metadata-item')
        year = year_element.get_text() if year_element else "N/A"
        
        # Extract rating
        rating_element = movie.select_one('span.ipc-rating-star')
        rating = rating_element.get_text().split()[0] if rating_element else "N/A"
        
        # Extract star cast (director info)
        star_cast_element = movie.select_one('span.cli-title-metadata-item')
        star_cast = star_cast_element.get_text() if star_cast_element else "N/A"
        
        data = {
            "place": place,
            "movie_title": movie_title,
            "rating": rating,
            "year": year,
            "star_cast": star_cast,
        }
        list.append(data)
        
    except Exception as e:
        print(f"Error processing movie {index}: {e}")
        continue

# Print results
for movie in list:
    print(f"{movie['place']} - {movie['movie_title']} ({movie['year']}) - Rating: {movie['rating']}")

# Save to CSV
if list:
    df = pd.DataFrame(list)
    df.to_csv('imdb_top_250_movies.csv', index=False)
    print(f"\nSuccessfully saved {len(list)} movies to imdb_top_250_movies.csv")
else:
    print("No data found. The website structure may have changed.")