document.addEventListener('DOMContentLoaded', () => {
    const movieSearch = document.getElementById('movie-search');
    const searchResults = document.getElementById('search-results');
    const movieGrid = document.getElementById('movie-grid');
    const ratedMoviesList = document.getElementById('rated-movies-list');
    const ratingCount = document.getElementById('rating-count');
    const statCount = document.getElementById('stat-count');
    const statMessage = document.getElementById('stat-message');
    const resetBtn = document.getElementById('reset-ratings');
    const genreFilters = document.getElementById('genre-filters');
    const refreshIndicator = document.getElementById('refresh-indicator');

    let userRatings = JSON.parse(localStorage.getItem('userRatings')) || {};
    let currentMovies = [];
    let activeGenre = null;

    updateUI();
    if (Object.keys(userRatings).length > 0) {
        getRecommendations();
    } else {
        loadPopularMovies();
    }

    movieSearch.addEventListener('input', debounce(handleSearch, 300));
    resetBtn.addEventListener('click', resetRatings);

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    }

    const debouncedRecommend = debounce(() => {
        if (Object.keys(userRatings).length > 0) getRecommendations();
    }, 500);

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
            div.textContent = movie.title;
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
        debouncedRecommend();
    }

    function saveRatings() {
        localStorage.setItem('userRatings', JSON.stringify(userRatings));
    }

    function updateUI() {
        const count = Object.keys(userRatings).length;
        ratingCount.textContent = count;
        statCount.textContent = count;
        statMessage.textContent = count < 5
            ? 'Rate more for better results!'
            : 'Recommendations refresh automatically as you rate.';
        renderRatedList();
    }

    function renderRatedList() {
        ratedMoviesList.innerHTML = '';
        Object.entries(userRatings).forEach(([id, movie]) => {
            const div = document.createElement('div');
            div.className = 'rated-item';
            div.innerHTML = `
                <img src="${movie.poster_url}" alt="" onerror="this.src='https://via.placeholder.com/40x60?text=?'">
                <div class="rated-item-info">
                    <h4>${escapeHtml(movie.title)}</h4>
                    <div class="stars-small">${getStarsHTML(movie.rating)}</div>
                </div>
                <i class="fas fa-times delete-rating" data-remove="${id}"></i>
            `;
            div.querySelector('[data-remove]').onclick = () => removeRating(id);
            ratedMoviesList.appendChild(div);
        });
    }

    function removeRating(id) {
        delete userRatings[id];
        saveRatings();
        updateUI();
        if (Object.keys(userRatings).length === 0) {
            loadPopularMovies();
        } else {
            debouncedRecommend();
        }
    }

    function getStarsHTML(rating) {
        let html = '';
        for (let i = 1; i <= 5; i++) {
            html += `<i class="fa${i <= rating ? 's' : 'r'} fa-star"></i>`;
        }
        return html;
    }

    function renderSkeletons(n = 12) {
        movieGrid.innerHTML = '';
        for (let i = 0; i < n; i++) {
            const card = document.createElement('div');
            card.className = 'movie-card skeleton';
            card.innerHTML = `
                <div class="movie-poster skeleton-box"></div>
                <div class="movie-info">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line short"></div>
                </div>
            `;
            movieGrid.appendChild(card);
        }
    }

    async function loadPopularMovies() {
        renderSkeletons();
        const response = await fetch('/api/movies/popular?n=12');
        currentMovies = await response.json();
        renderMovieGrid(currentMovies);
    }

    async function getRecommendations() {
        refreshIndicator.hidden = false;
        renderSkeletons();

        const ratingsForApi = {};
        Object.entries(userRatings).forEach(([id, data]) => {
            ratingsForApi[id] = data.rating;
        });

        try {
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ratings: ratingsForApi })
            });
            currentMovies = await response.json();
            renderMovieGrid(currentMovies);
        } finally {
            refreshIndicator.hidden = true;
        }
    }

    function renderGenreFilters(movies) {
        const genres = new Set();
        movies.forEach(m => (m.genres || '').split('|').forEach(g => g && genres.add(g)));
        genreFilters.innerHTML = '';
        if (genres.size === 0) return;

        const all = document.createElement('span');
        all.className = `genre-chip filter ${activeGenre === null ? 'active' : ''}`;
        all.textContent = 'All';
        all.onclick = () => { activeGenre = null; renderMovieGrid(currentMovies); };
        genreFilters.appendChild(all);

        [...genres].sort().forEach(g => {
            const chip = document.createElement('span');
            chip.className = `genre-chip filter ${activeGenre === g ? 'active' : ''}`;
            chip.textContent = g;
            chip.onclick = () => { activeGenre = (activeGenre === g ? null : g); renderMovieGrid(currentMovies); };
            genreFilters.appendChild(chip);
        });
    }

    function renderMovieGrid(movies) {
        renderGenreFilters(movies);
        movieGrid.innerHTML = '';

        const filtered = activeGenre
            ? movies.filter(m => (m.genres || '').split('|').includes(activeGenre))
            : movies;

        if (filtered.length === 0) {
            movieGrid.innerHTML = `<div class="empty-state">No ${escapeHtml(activeGenre)} movies in current picks.</div>`;
            return;
        }

        filtered.forEach(movie => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            const userRating = userRatings[movie.movieId]?.rating || 0;
            const genres = (movie.genres || '').split('|').filter(Boolean);
            const because = movie.because && movie.because.length
                ? `<div class="because" title="${escapeHtml(movie.because.join(' • '))}"><i class="fas fa-lightbulb"></i> Because you liked ${escapeHtml(movie.because[0])}</div>`
                : '';

            card.innerHTML = `
                <div class="movie-poster">
                    <img src="${movie.poster_url}" alt="" loading="lazy" onerror="this.src='https://via.placeholder.com/300x450?text=No+Poster'">
                </div>
                <div class="movie-info">
                    <h3 title="${escapeHtml(movie.title)}">${escapeHtml(movie.title)}</h3>
                    <div class="genre-chips">
                        ${genres.slice(0, 3).map(g => `<span class="genre-chip">${escapeHtml(g)}</span>`).join('')}
                    </div>
                    ${because}
                    <div class="stars" data-movie-id="${movie.movieId}">
                        ${getInteractiveStarsHTML(userRating)}
                    </div>
                </div>
            `;
            movieGrid.appendChild(card);

            const starsContainer = card.querySelector('.stars');
            starsContainer.addEventListener('click', e => {
                const star = e.target.closest('.star');
                if (!star) return;
                const rating = parseInt(star.dataset.value);
                addMovieToRatings(movie, rating);
                starsContainer.innerHTML = getInteractiveStarsHTML(rating);
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

    function escapeHtml(str) {
        return String(str ?? '').replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));
    }

    function resetRatings() {
        if (confirm('Are you sure you want to reset all your ratings?')) {
            userRatings = {};
            activeGenre = null;
            saveRatings();
            updateUI();
            loadPopularMovies();
        }
    }
});
