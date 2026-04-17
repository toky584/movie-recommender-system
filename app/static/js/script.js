document.addEventListener('DOMContentLoaded', () => {
    const movieSearch = document.getElementById('movie-search');
    const searchResults = document.getElementById('search-results');
    const movieGrid = document.getElementById('movie-grid');
    const ratedMoviesList = document.getElementById('rated-movies-list');
    const ratingCount = document.getElementById('rating-count');
    const statCount = document.getElementById('stat-count');
    const statMessage = document.getElementById('stat-message');
    const updateBtn = document.getElementById('update-recommendations');
    const resetBtn = document.getElementById('reset-ratings');

    let userRatings = JSON.parse(localStorage.getItem('userRatings')) || {};
    let currentMovies = [];

    // Initialize
    updateUI();
    loadRandomMovies();

    // Event Listeners
    movieSearch.addEventListener('input', debounce(handleSearch, 300));
    updateBtn.addEventListener('click', getRecommendations);
    resetBtn.addEventListener('click', resetRatings);

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async function handleSearch() {
        const query = movieSearch.value.trim();
        if (query.length < 2) {
            searchResults.innerHTML = '';
            return;
        }

        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const movies = await response.json();
        renderSearchResults(movies);
    }

    function renderSearchResults(movies) {
        searchResults.innerHTML = '';
        movies.forEach(movie => {
            const div = document.createElement('div');
            div.className = 'search-item';
            div.innerHTML = `
                <span>${movie.title}</span>
            `;
            div.onclick = () => {
                addMovieToRatings(movie);
                movieSearch.value = '';
                searchResults.innerHTML = '';
            };
            searchResults.appendChild(div);
        });
    }

    function addMovieToRatings(movie, rating = 5) {
        userRatings[movie.movieId] = {
            title: movie.title,
            poster_url: movie.poster_url,
            rating: rating
        };
        saveRatings();
        updateUI();
    }

    function saveRatings() {
        localStorage.setItem('userRatings', JSON.stringify(userRatings));
    }

    function updateUI() {
        const count = Object.keys(userRatings).length;
        ratingCount.textContent = count;
        statCount.textContent = count;
        
        if (count < 5) {
            statMessage.textContent = 'Rate more for better results!';
        } else {
            statMessage.textContent = 'Great! Update to see your personalized list.';
        }

        renderRatedList();
    }

    function renderRatedList() {
        ratedMoviesList.innerHTML = '';
        Object.entries(userRatings).forEach(([id, movie]) => {
            const div = document.createElement('div');
            div.className = 'rated-item';
            div.innerHTML = `
                <img src="${movie.poster_url}" alt="${movie.title}">
                <div class="rated-item-info">
                    <h4>${movie.title}</h4>
                    <div class="stars-small">
                        ${getStarsHTML(movie.rating)}
                    </div>
                </div>
                <i class="fas fa-times delete-rating" onclick="removeRating(${id})"></i>
            `;
            ratedMoviesList.appendChild(div);
        });
    }

    window.removeRating = (id) => {
        delete userRatings[id];
        saveRatings();
        updateUI();
    };

    function getStarsHTML(rating) {
        let html = '';
        for (let i = 1; i <= 5; i++) {
            html += `<i class="fa${i <= rating ? 's' : 'r'} fa-star"></i>`;
        }
        return html;
    }

    async function loadRandomMovies() {
        movieGrid.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading suggestions...</div>';
        const response = await fetch('/api/movies/random?n=12');
        currentMovies = await response.json();
        renderMovieGrid(currentMovies);
    }

    async function getRecommendations() {
        if (Object.keys(userRatings).length === 0) {
            alert('Please rate at least one movie first!');
            return;
        }

        movieGrid.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Finding movies you\'ll love...</div>';
        
        // Extract only movieId: rating for the API
        const ratingsForApi = {};
        Object.entries(userRatings).forEach(([id, data]) => {
            ratingsForApi[id] = data.rating;
        });

        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ratings: ratingsForApi })
        });
        
        currentMovies = await response.json();
        renderMovieGrid(currentMovies);
    }

    function renderMovieGrid(movies) {
        movieGrid.innerHTML = '';
        movies.forEach(movie => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            const userRating = userRatings[movie.movieId]?.rating || 0;
            
            card.innerHTML = `
                <div class="movie-poster">
                    <img src="${movie.poster_url}" alt="${movie.title}" onerror="this.src='https://via.placeholder.com/300x450?text=No+Poster'">
                </div>
                <div class="movie-info">
                    <h3>${movie.title}</h3>
                    <div class="stars" data-movie-id="${movie.movieId}">
                        ${getInteractiveStarsHTML(userRating)}
                    </div>
                </div>
            `;
            movieGrid.appendChild(card);

            // Add star click listeners
            const stars = card.querySelectorAll('.star');
            stars.forEach(star => {
                star.onclick = () => {
                    const rating = parseInt(star.dataset.value);
                    addMovieToRatings(movie, rating);
                    renderMovieGrid(currentMovies); // Re-render to show active stars
                };
            });
        });
    }

    function getInteractiveStarsHTML(activeRating) {
        let html = '';
        for (let i = 1; i <= 5; i++) {
            html += `<i class="fas fa-star star ${i <= activeRating ? 'active' : ''}" data-value="${i}"></i>`;
        }
        return html;
    }

    function resetRatings() {
        if (confirm('Are you sure you want to reset all your ratings?')) {
            userRatings = {};
            saveRatings();
            updateUI();
            loadRandomMovies();
        }
    }
});
