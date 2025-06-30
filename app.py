import streamlit as st
import numpy as np
import pandas as pd
import pickle
from streamlit_star_rating import st_star_rating

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATA LOADING (CACHED) ---
@st.cache_data
def load_artifacts():
    """Loads all pre-trained model artifacts."""
    with np.load('artifacts/complete.npz') as data:
        movies_biases = data['movies_biases']
        movie_vector = data['movie_vector']
    
    with open('artifacts/mappings.pkl', 'rb') as f:
        mappings = pickle.load(f)
        map_movie_to_idx = mappings['map_movie_to_idx']
        
    map_idx_to_movie = {idx: movie_id for movie_id, idx in map_movie_to_idx.items()}
    
    return movies_biases, movie_vector, map_movie_to_idx, map_idx_to_movie

@st.cache_data
def load_movie_data():
    """Loads the movies data."""
    df = pd.read_csv('data/movies_with_posters.csv')
    df['display'] = df['title']
    return df

# --- Load all data and artifacts ---
movies_biases, movie_vector, map_movie_to_idx, map_idx_to_movie = load_artifacts()
movies_df = load_movie_data()

# --- CORE LOGIC (Using your prediction function) ---
def get_recommendations_from_user_code(new_user_ratings, movie_matrix, item_bias, movies_df, map_movie_to_idx, map_idx_to_movie, n=12):
    """Encapsulates your provided prediction logic."""
    lamda = 0.02
    tau = 0.02
    k = movie_matrix.shape[1]
    
    sum_vn = np.zeros((k,k))
    sum_r_vn = np.zeros(k)

    new_user_input_for_calc = []
    for movie_id, rating in new_user_ratings.items():
        if str(movie_id) in map_movie_to_idx:
            movie_idx = map_movie_to_idx[str(movie_id)]
            new_user_input_for_calc.append((movie_idx, rating))
    
    if not new_user_input_for_calc:
        return movies_df.sample(n=n, random_state=42)

    for (n_idx, r) in new_user_input_for_calc:
      vn = movie_matrix[n_idx, :]
      sum_vn += np.outer(vn, vn)
      sum_r_vn += lamda * (r - item_bias[n_idx]) * vn
      
    sum_vn = lamda * (sum_vn) + tau * np.eye(k)
    user_vec = np.linalg.solve(sum_vn, sum_r_vn)

    scores = movie_matrix.dot(user_vec) + 0.005 * item_bias
    ranking_indices = np.argsort(scores)[::-1]

    rated_indices = {idx for (idx, r) in new_user_input_for_calc}
    top_indices = [idx for idx in ranking_indices if idx not in rated_indices][:n]
    
    top_movie_ids = [int(map_idx_to_movie[idx]) for idx in top_indices]
    result_df = pd.DataFrame({'movieId': top_movie_ids})
    final_recommendations = pd.merge(result_df, movies_df, on='movieId')
    
    return final_recommendations

# --- CALLBACK FUNCTION FOR CLEARING STATE ---
def clear_all_ratings():
    """Resets the user's ratings and recommendations to the initial state."""
    st.session_state.new_user_ratings = {}
    st.session_state.search_selector = []
    st.session_state.recommendations = movies_df.sample(n=12, random_state=101)

# --- SESSION STATE INITIALIZATION ---
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = movies_df.sample(n=12, random_state=42)
if 'new_user_ratings' not in st.session_state:
    st.session_state.new_user_ratings = {}
if 'search_selector' not in st.session_state:
    st.session_state.search_selector = []

# --- SIDEBAR UI ---
st.sidebar.header("Find & Rate Specific Movies")
movie_sample = movies_df.sort_values('title').reset_index(drop=True)

searched_movies = st.sidebar.multiselect(
    "Start typing to find movies...",
    movie_sample['display'],
    key='search_selector'
)

# --- THIS IS THE UPDATED SIDEBAR DISPLAY LOGIC ---
if searched_movies:
    st.sidebar.subheader("Rate the movies you found:")
    for movie_title in searched_movies:
        movie_details = movie_sample.loc[movie_sample['display'] == movie_title].iloc[0]
        movie_id = movie_details['movieId']
        poster_url = movie_details['poster_url']
        
        # 1. Display the star rating widget FIRST
        rating = st_star_rating(
            label=f"Your rating for **{movie_title}**",
            maxValue=5,
            defaultValue=st.session_state.new_user_ratings.get(movie_id, 0),
            key=f"search_rating_{movie_id}",
            size=20
        )
        
        # 2. Display the poster SECOND, below the rating
        st.sidebar.image(poster_url, use_container_width=True)

        # Store the rating if the user provided one
        if rating:
            st.session_state.new_user_ratings[movie_id] = rating
        
        st.sidebar.markdown("---")

st.sidebar.button("Reset All Ratings", on_click=clear_all_ratings, help="Click to clear all your ratings and start over.")
st.sidebar.info("After rating, click the 'Update' button in the main panel to see new recommendations.")


# --- MAIN PANEL UI ---
# (The rest of the code remains the same)
st.title("🎬 Movie Recommender")
st.markdown("Rate movies to get personalized recommendations. Find specific movies in the sidebar!")

num_ratings = len(st.session_state.new_user_ratings)
if num_ratings > 0:
    if num_ratings < 5:
        st.info(f"You have rated {num_ratings} movie(s). For best results, we recommend rating more than 1 movie.")
    else:
        st.info(f"You have rated {num_ratings} movie(s). Click below to update your recommendations!")

    if st.button("Update My Recommendations", type="primary"):
        with st.spinner("Finding movies you'll love..."):
            st.session_state.recommendations = get_recommendations_from_user_code(
                st.session_state.new_user_ratings,
                movie_vector,
                movies_biases,
                movies_df,
                map_movie_to_idx,
                map_idx_to_movie,
                n=12
            )
st.markdown("---")

st.header("Movies For You to Rate")
recommendations_df = st.session_state.recommendations
num_cols = 4
cols = st.columns(num_cols)

for i, row in enumerate(recommendations_df.itertuples()):
    with cols[i % num_cols]:
        with st.container():
            st.image(row.poster_url, use_container_width=True)
            st.markdown(f"**{row.title}**")
            
            rating = st_star_rating(
                label="",
                maxValue=5,
                defaultValue=st.session_state.new_user_ratings.get(row.movieId, 0),
                key=f"grid_rating_{row.movieId}",
                size=20
            )
            if rating:
                st.session_state.new_user_ratings[row.movieId] = rating