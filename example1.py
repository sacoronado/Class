from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from openai import OpenAI
import time

# === Step 1: Set up Selenium ===
options = Options()
options.add_argument("--headless")  # Run in background
options.add_argument("--disable-gpu")
service = Service()  # Assumes chromedriver is in PATH
driver = webdriver.Chrome(service=service, options=options)

# === Step 2: Load IMDb Page ===
url = "https://www.imdb.com/list/ls086744766/"
driver.get(url)
time.sleep(3)  # Let the page fully load

soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# === Step 3: Extract Raw Movie Data ===
raw_movies = []
movie_blocks = soup.select("div.lister-item.mode-detail")

for block in movie_blocks:
    title_tag = block.select_one("h3.lister-item-header a")
    year_tag = block.select_one("span.lister-item-year")
    duration_tag = block.select_one("span.runtime")
    metascore_tag = block.select_one("div.inline-block.ratings-metascore span.metascore")

    title = title_tag.text.strip() if title_tag else None
    year = year_tag.text.strip("()") if year_tag else None
    duration = duration_tag.text.strip() if duration_tag else None
    metascore = metascore_tag.text.strip() if metascore_tag else None

    if title:
        raw_movies.append(f"Title: {title}, Year: {year or 'N/A'}, Duration: {duration or 'N/A'}, Metascore: {metascore or 'N/A'}")

# === Step 4: Print Raw Data ===
print("🔍 Raw scraped data:")
if not raw_movies:
    print("⚠️ No movie data found. IMDb page structure may have changed.")
else:
    for entry in raw_movies:
        print(entry)

# === Step 5: Send to GPT-4o for JSON Formatting ===
if raw_movies:
    endpoint = "https://cdong1--azure-proxy-web-app.modal.run"
    api_key = "supersecretkey"
    deployment_name = "gpt-4o"

    client = OpenAI(
        base_url=endpoint,
        api_key=api_key
    )

    formatted_data = "\n".join(raw_movies)

    prompt = f"""
Here is a list of raw movie data scraped from IMDb about Nicolas Cage films:

{formatted_data}

Please convert this into a structured JSON array. Each object should include:
- title
- year
- duration
- metascore
"""

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    print("\n📦 Structured JSON output:")
    print(response.choices[0].message.content)