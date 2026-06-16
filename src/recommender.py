import numpy as np
import pandas as pd
import pickle
import os

class MovieRecommender:
    def __init__(self, artifacts_path='artifacts', data_path='data'):
        self.artifacts_path = artifacts_path
        self.data_path = data_path
        self.movies_biases = None
        self.movie_vector = None
        self.map_movie_to_idx = None
        self.map_idx_to_movie = None
        self.movies_df = None
        self.load_data()

    def load_data(self):
        """Loads all pre-trained model artifacts and movie data."""
        complete_path = os.path.join(self.artifacts_path, 'complete.npz')
        mappings_path = os.path.join(self.artifacts_path, 'mappings.pkl')
        movies_csv_path = os.path.join(self.data_path, 'movies_with_posters.csv')

        with np.load(complete_path) as data:
            self.movies_biases = data['movies_biases']
            self.movie_vector = data['movie_vector']
        
        with open(mappings_path, 'rb') as f:
            mappings = pickle.load(f)
            self.map_movie_to_idx = mappings['map_movie_to_idx']
            
        self.map_idx_to_movie = {idx: movie_id for movie_id, idx in self.map_movie_to_idx.items()}
        
        self.movies_df = pd.read_csv(movies_csv_path)
        self.movies_df['movieId'] = self.movies_df['movieId'].astype(int)
        # Ensure movieId is string in mapping if it was saved that way, or handle conversion
        # The original code used str(movie_id)

    def get_recommendations(self, new_user_ratings, n=12):
        """
        new_user_ratings: dict of {movieId: rating}
        Returns list of movie dicts; each recommendation also includes a
        `because` field listing the 2 rated titles whose learned vectors
        most align with the recommendation (for UI explanations).
        """
        lamda = 0.02
        tau = 0.02
        k = self.movie_vector.shape[1]

        sum_vn = np.zeros((k,k))
        sum_r_vn = np.zeros(k)

        new_user_input_for_calc = []
        for movie_id, rating in new_user_ratings.items():
            movie_id_str = str(movie_id)
            if movie_id_str in self.map_movie_to_idx:
                movie_idx = self.map_movie_to_idx[movie_id_str]
                new_user_input_for_calc.append((movie_idx, rating))

        if not new_user_input_for_calc:
            return self.get_popular_movies(n=n)

        for (n_idx, r) in new_user_input_for_calc:
            vn = self.movie_vector[n_idx, :]
            sum_vn += np.outer(vn, vn)
            sum_r_vn += lamda * (r - self.movies_biases[n_idx]) * vn

        sum_vn = lamda * (sum_vn) + tau * np.eye(k)
        user_vec = np.linalg.solve(sum_vn, sum_r_vn)

        scores = self.movie_vector.dot(user_vec) + 0.005 * self.movies_biases
        ranking_indices = np.argsort(scores)[::-1]

        rated_indices = {idx for (idx, r) in new_user_input_for_calc}
        top_indices = [idx for idx in ranking_indices if idx not in rated_indices][:n]

        rated_idx_list = [idx for (idx, _) in new_user_input_for_calc]
        rated_vecs = self.movie_vector[rated_idx_list]  # (R, k)
        movies_by_id = self.movies_df.set_index('movieId')

        recommendations = []
        for rec_idx in top_indices:
            mid = int(self.map_idx_to_movie[rec_idx])
            if mid not in movies_by_id.index:
                continue
            movie = movies_by_id.loc[mid].to_dict()
            movie['movieId'] = mid

            sims = rated_vecs @ self.movie_vector[rec_idx]
            top_contrib = np.argsort(sims)[::-1][:2]
            because = []
            for c in top_contrib:
                rated_mid = int(self.map_idx_to_movie[rated_idx_list[c]])
                if rated_mid in movies_by_id.index:
                    because.append(movies_by_id.loc[rated_mid]['title'])
            movie['because'] = because
            recommendations.append(movie)

        return recommendations

    def search_movies(self, query, n=10):
        if not query:
            return []
        results = self.movies_df[self.movies_df['title'].str.contains(query, case=False, na=False)]
        return results.head(n).to_dict(orient='records')

    def get_random_movies(self, n=12):
        return self.movies_df.sample(n=n).to_dict(orient='records')

    def get_popular_movies(self, n=12):
        """Cold-start pool: highest-bias movies from the ALS model.

        Learned bias correlates with overall popularity, so this surfaces
        well-known titles rather than obscure random picks.
        """
        top_idx = np.argsort(self.movies_biases)[::-1][:n * 3]
        top_ids = [int(self.map_idx_to_movie[i]) for i in top_idx]
        df = self.movies_df[self.movies_df['movieId'].isin(top_ids)]
        order = {mid: i for i, mid in enumerate(top_ids)}
        df = df.assign(_order=df['movieId'].map(order)).sort_values('_order').drop(columns=['_order'])
        return df.head(n).to_dict(orient='records')
