import pandas as pd
import requests
from tqdm import tqdm
import os
import concurrent.futures

# --- CONFIGURATION ---
# PASTE YOUR TMDB API KEY HERE
TMDB_API_KEY = "your-api-here"

# Base URL for TMDb images
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
# A placeholder image for movies without a poster
PLACEHOLDER_IMAGE = "https://www.movienewz.com/img/films/poster-holder.jpg"

# --- FILE PATHS ---
DATA_DIR = 'data'
MOVIES_FILE = os.path.join(DATA_DIR, 'movies.csv')
LINKS_FILE = os.path.join(DATA_DIR, 'links.csv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'movies_with_posters.csv')

def get_poster_url(tmdb_id):
    """Fetches the poster path for a given tmdb_id and returns the full URL."""
    if pd.isna(tmdb_id):
        return PLACEHOLDER_IMAGE
        
    api_url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}?api_key={TMDB_API_KEY}"
    
    try:
        response = requests.get(api_url, timeout=5) # Add a timeout
        response.raise_for_status() 
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return IMAGE_BASE_URL + poster_path
        else:
            return PLACEHOLDER_IMAGE
            
    except requests.exceptions.RequestException:
        return PLACEHOLDER_IMAGE

def main():
    """Main function to process movies, fetch poster URLs concurrently, and save the result."""
    print("Loading datasets...")
    movies_df = pd.read_csv(MOVIES_FILE)
    links_df = pd.read_csv(LINKS_FILE, dtype={'tmdbId': 'Int64'})

    print("Merging movies and links data...")
    merged_df = pd.merge(movies_df, links_df, on='movieId')

    # Get the list of tmdbIds to process
    tmdb_ids = merged_df['tmdbId'].tolist()
    
    print(f"Fetching poster URLs for {len(tmdb_ids)} movies using concurrent requests...")
    
    # Use a ThreadPoolExecutor to make requests in parallel
    # We will store results in a list that will be in the correct order
    poster_urls = [None] * len(tmdb_ids)

    # Let's use 20 threads. This is a good balance for not overwhelming the API.
    # You can experiment with this number (e.g., 10, 30).
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Create a dictionary to map future objects back to their original index
        future_to_index = {executor.submit(get_poster_url, tmdb_id): i for i, tmdb_id in enumerate(tmdb_ids)}
        
        # Use tqdm to show progress as futures complete
        for future in tqdm(concurrent.futures.as_completed(future_to_index), total=len(tmdb_ids)):
            index = future_to_index[future]
            try:
                poster_urls[index] = future.result()
            except Exception as exc:
                print(f"A request generated an exception: {exc}")
                poster_urls[index] = PLACEHOLDER_IMAGE

    merged_df['poster_url'] = poster_urls

    print("Saving enriched data to new CSV file...")
    final_df = merged_df[['movieId', 'title', 'genres', 'poster_url']]
    final_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"✅ Done! Enriched data saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
