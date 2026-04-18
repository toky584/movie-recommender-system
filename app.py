from flask import Flask, render_template, request, jsonify
from src.recommender import MovieRecommender
import os

app = Flask(__name__, 
            static_folder='app/static', 
            template_folder='app/templates')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize recommender
recommender = MovieRecommender(
    artifacts_path=os.path.join(BASE_DIR, 'artifacts'),
    data_path=os.path.join(BASE_DIR, 'data')
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/movies/random')
def get_random_movies():
    n = request.args.get('n', 12, type=int)
    movies = recommender.get_random_movies(n=n)
    return jsonify(movies)

@app.route('/api/movies/popular')
def get_popular_movies():
    n = request.args.get('n', 12, type=int)
    movies = recommender.get_popular_movies(n=n)
    return jsonify(movies)

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    movies = recommender.search_movies(query)
    return jsonify(movies)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json
    ratings = data.get('ratings', {})
    # ratings should be {movieId: rating}
    # Ensure keys are integers if needed, but recommender handles string conversion
    formatted_ratings = {int(k): float(v) for k, v in ratings.items()}
    
    recommendations = recommender.get_recommendations(formatted_ratings)
    return jsonify(recommendations)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
