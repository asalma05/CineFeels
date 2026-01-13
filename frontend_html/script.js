// ===== Configuration =====
const API_BASE_URL = 'http://localhost:8000';

// ===== State Management =====
let currentUser = null;
let token = localStorage.getItem('token');
let emotions = {
    joy: 0,
    sadness: 0,
    fear: 0,
    anger: 0,
    surprise: 0,
    disgust: 0,
    thrill: 0,
    romance: 0,
    humor: 0,
    inspiration: 0
};
let analysisHistory = [];
let emotionProfile = {
    joy: 0,
    sadness: 0,
    fear: 0,
    anger: 0,
    surprise: 0,
    disgust: 0
};

// Feature state - now fetched from API
let watchlist = [];
let compareMovies = [];
let allMoviesCache = [];
let currentFilters = {
    decade: '',
    genre: '',
    duration: '',
    rating: ''
};

// ===== API Helper =====
async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    });
    
    return response;
}

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// ===== Authentication =====
async function checkAuth() {
    if (token) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                currentUser = await response.json();
                showPage('dashboard-page');
                loadDashboardData();
            } else {
                logout();
            }
        } catch (error) {
            console.error('Auth check error:', error);
            showPage('landing-page');
        }
    } else {
        showPage('landing-page');
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            token = data.access_token;
            localStorage.setItem('token', token);
            
            // Get user profile
            const userResponse = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (userResponse.ok) {
                currentUser = await userResponse.json();
                hideModal('login-modal');
                showPage('dashboard-page');
                loadDashboardData();
            }
        } else {
            const error = await response.json();
            showError('login-error', error.detail || 'Identifiants incorrects');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('login-error', 'Erreur de connexion au serveur');
    }
    
    hideLoading();
}

async function handleRegister(event) {
    event.preventDefault();
    
    const fullName = document.getElementById('register-fullname').value;
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                username: username,
                password: password,
                full_name: fullName
            })
        });
        
        if (response.ok) {
            // Auto-login after registration
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);
            
            const loginResponse = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
                method: 'POST',
                body: formData
            });
            
            if (loginResponse.ok) {
                const data = await loginResponse.json();
                token = data.access_token;
                localStorage.setItem('token', token);
                
                const userResponse = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (userResponse.ok) {
                    currentUser = await userResponse.json();
                    hideModal('register-modal');
                    showPage('dashboard-page');
                    loadDashboardData();
                }
            }
        } else {
            const error = await response.json();
            showError('register-error', error.detail || 'Erreur lors de l\'inscription');
        }
    } catch (error) {
        console.error('Register error:', error);
        showError('register-error', 'Erreur de connexion au serveur');
    }
    
    hideLoading();
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    analysisHistory = [];
    showPage('landing-page');
}

// ===== Page Navigation =====
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
    
    if (pageId === 'dashboard-page' && currentUser) {
        updateUserDisplay();
    }
}

function updateUserDisplay() {
    const username = currentUser.username || currentUser.full_name || 'Utilisateur';
    document.getElementById('username-display').textContent = username;
    document.getElementById('username-welcome').textContent = username;
}

// ===== Modal Management =====
function showModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function hideModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    // Clear form
    const form = document.querySelector(`#${modalId} form`);
    if (form) form.reset();
    // Hide error
    const error = document.querySelector(`#${modalId} .error-message`);
    if (error) error.classList.add('hidden');
}

function switchModal(from, to) {
    hideModal(from);
    showModal(to);
}

function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
}

// ===== Loading =====
function showLoading() {
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

// ===== Dashboard Data =====
async function loadDashboardData() {
    updateUserDisplay();
    await loadUserStats();
    await loadWatchlistFromAPI();
    await loadAnalysisHistoryFromAPI();
    await loadEmotionProfile();
    loadBestMovies();
    drawRadarChart();
}

async function loadUserStats() {
    try {
        const response = await apiRequest('/api/v1/user/stats');
        if (response.ok) {
            const stats = await response.json();
            document.getElementById('total-analyses').textContent = stats.total_analyses || 0;
            document.getElementById('total-movies').textContent = stats.total_movies || 0;
            document.getElementById('total-favorites').textContent = stats.total_favorites || 0;
            document.getElementById('total-watchlist').textContent = stats.watchlist_count || 0;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        // Fallback to local data
        loadStats();
    }
}

function loadStats() {
    document.getElementById('total-analyses').textContent = analysisHistory.length;
    document.getElementById('total-movies').textContent = analysisHistory.reduce((sum, a) => sum + (a.movieCount || 0), 0);
    document.getElementById('total-favorites').textContent = 0;
    document.getElementById('total-watchlist').textContent = watchlist.length;
}

function loadAnalysisHistory() {
    // Load from localStorage as fallback
    const saved = localStorage.getItem('analysisHistory');
    if (saved) {
        analysisHistory = JSON.parse(saved);
    }
    
    renderAnalysisHistory();
    loadStats();
    updateEmotionProfile();
    drawRadarChart();
}

async function loadAnalysisHistoryFromAPI() {
    try {
        const response = await apiRequest('/api/v1/user/analyses');
        if (response.ok) {
            analysisHistory = await response.json();
            renderAnalysisHistory();
        } else {
            // Fallback to localStorage
            loadAnalysisHistory();
        }
    } catch (error) {
        console.error('Error loading analysis history from API:', error);
        loadAnalysisHistory();
    }
}

async function loadEmotionProfile() {
    try {
        const response = await apiRequest('/api/v1/user/profile/emotions');
        if (response.ok) {
            emotionProfile = await response.json();
            drawRadarChart();
        }
    } catch (error) {
        console.error('Error loading emotion profile:', error);
        updateEmotionProfile();
    }
}

function renderAnalysisHistory() {
    const container = document.getElementById('analysis-history');
    
    if (analysisHistory.length === 0) {
        container.innerHTML = '<p class="empty-message">Aucune analyse pour le moment. Commencez par sélectionner vos émotions !</p>';
        return;
    }
    
    container.innerHTML = analysisHistory.map(analysis => `
        <div class="history-item">
            <div class="history-item-header">
                <span class="history-date">${formatDate(analysis.date)}</span>
                <span class="history-movies-count">${analysis.movieCount} films recommandés</span>
            </div>
            <div class="history-emotions">
                ${Object.entries(analysis.emotions)
                    .filter(([_, value]) => value > 0)
                    .map(([emotion, value]) => `
                        <span class="emotion-tag">${emotion}: ${Math.round(value * 100)}%</span>
                    `).join('')}
            </div>
        </div>
    `).join('');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function updateEmotionProfile() {
    // Calculate aggregate emotion profile from history
    const baseEmotions = ['joy', 'sadness', 'fear', 'anger', 'surprise', 'disgust'];
    
    if (analysisHistory.length === 0) {
        baseEmotions.forEach(e => emotionProfile[e] = 0);
        return;
    }
    
    baseEmotions.forEach(emotion => {
        let total = 0;
        let count = 0;
        
        analysisHistory.forEach(analysis => {
            if (analysis.emotions[emotion] !== undefined) {
                total += analysis.emotions[emotion];
                count++;
            }
        });
        
        emotionProfile[emotion] = count > 0 ? total / count : 0;
    });
}

// ===== Radar Chart =====
function drawRadarChart() {
    const canvas = document.getElementById('radar-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 60;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    const emotionLabels = ['joy', 'sadness', 'fear', 'anger', 'surprise', 'disgust'];
    const emotionNames = ['Joie', 'Tristesse', 'Peur', 'Colère', 'Surprise', 'Dégoût'];
    const emotionIcons = ['😊', '😢', '😨', '😠', '😲', '🤢'];
    const emotionColors = {
        joy: '#fbbf24',
        sadness: '#3b82f6',
        fear: '#7c3aed',
        anger: '#ef4444',
        surprise: '#f97316',
        disgust: '#10b981'
    };
    
    const values = emotionLabels.map(e => emotionProfile[e] || 0);
    const angleStep = (Math.PI * 2) / emotionLabels.length;
    
    // Draw grid circles
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.2)';
    ctx.lineWidth = 1;
    for (let i = 1; i <= 5; i++) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, (radius / 5) * i, 0, Math.PI * 2);
        ctx.stroke();
    }
    
    // Draw axes
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.3)';
    emotionLabels.forEach((_, i) => {
        const angle = angleStep * i - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;
        
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.stroke();
    });
    
    // Draw data polygon
    ctx.beginPath();
    ctx.fillStyle = 'rgba(251, 191, 36, 0.3)';
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 2;
    
    values.forEach((value, i) => {
        const angle = angleStep * i - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius * value;
        const y = centerY + Math.sin(angle) * radius * value;
        
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    
    // Draw data points
    values.forEach((value, i) => {
        const angle = angleStep * i - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius * value;
        const y = centerY + Math.sin(angle) * radius * value;
        
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = emotionColors[emotionLabels[i]];
        ctx.fill();
    });
    
    // Draw labels
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    emotionLabels.forEach((emotion, i) => {
        const angle = angleStep * i - Math.PI / 2;
        const labelDistance = radius + 45;
        const x = centerX + Math.cos(angle) * labelDistance;
        const y = centerY + Math.sin(angle) * labelDistance;
        
        // Draw icon
        ctx.font = '24px sans-serif';
        ctx.fillText(emotionIcons[i], x, y - 15);
        
        // Draw label
        ctx.font = 'bold 12px sans-serif';
        ctx.fillStyle = emotionColors[emotion];
        ctx.fillText(emotionNames[i], x, y + 10);
        
        // Draw percentage
        ctx.font = '11px sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText(`${Math.round(values[i] * 100)}%`, x, y + 25);
    });
}

// ===== Emotion Selector =====
function toggleEmotionSelector() {
    const selector = document.getElementById('emotion-selector');
    selector.classList.toggle('hidden');
}

function updateEmotion(slider) {
    const emotion = slider.dataset.emotion;
    const value = slider.value;
    
    emotions[emotion] = value / 100;
    document.getElementById(`${emotion}-value`).textContent = `${value}%`;
    
    // Update slider background
    const percentage = value;
    slider.style.background = `linear-gradient(to right, #f59e0b 0%, #f59e0b ${percentage}%, #334155 ${percentage}%, #334155 100%)`;
}

function resetEmotions() {
    Object.keys(emotions).forEach(emotion => {
        emotions[emotion] = 0;
        const slider = document.getElementById(`${emotion}-slider`);
        if (slider) {
            slider.value = 0;
            slider.style.background = '#334155';
        }
        const valueEl = document.getElementById(`${emotion}-value`);
        if (valueEl) {
            valueEl.textContent = '0%';
        }
    });
    
    document.getElementById('recommendations-section').classList.add('hidden');
}

// ===== Recommendations =====
async function getRecommendations() {
    // Filter emotions with value > 0
    const activeEmotions = {};
    Object.entries(emotions).forEach(([key, value]) => {
        if (value > 0) {
            activeEmotions[key] = value;
        }
    });
    
    if (Object.keys(activeEmotions).length === 0) {
        alert('Veuillez sélectionner au moins une émotion !');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/recommendations/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                emotions: activeEmotions,
                limit: 12,
                min_rating: 6.0
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            const movies = data.movies || [];
            
            // Save to history (now async)
            await saveAnalysis(activeEmotions, movies.length);
            
            // Show recommendations
            document.getElementById('recommendations-section').classList.remove('hidden');
            renderMovies('recommended-movies', movies);
            
            // Scroll to recommendations
            document.getElementById('recommendations-section').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert('Erreur lors de la récupération des recommandations');
        }
    } catch (error) {
        console.error('Recommendations error:', error);
        alert('Erreur de connexion au serveur');
    }
    
    hideLoading();
}

async function saveAnalysis(emotions, movieCount) {
    const analysis = {
        id: Date.now().toString(),
        date: new Date().toISOString(),
        emotions: { ...emotions },
        movieCount: movieCount
    };
    
    // Save to API (Neo4j)
    try {
        const response = await apiRequest('/api/v1/user/analyses', {
            method: 'POST',
            body: JSON.stringify({
                emotions: emotions,
                movie_count: movieCount
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            analysis.id = result.id;
            analysis.date = result.date;
        }
    } catch (error) {
        console.error('Error saving analysis to API:', error);
    }
    
    // Also save to localStorage as backup
    analysisHistory.unshift(analysis);
    if (analysisHistory.length > 20) {
        analysisHistory = analysisHistory.slice(0, 20);
    }
    localStorage.setItem('analysisHistory', JSON.stringify(analysisHistory));
    
    // Reload data from API
    await loadUserStats();
    await loadEmotionProfile();
    renderAnalysisHistory();
    drawRadarChart();
}

// ===== Movie Rendering =====
function renderMovies(containerId, movies, options = {}) {
    const container = document.getElementById(containerId);
    const { showWatchlistBtn = true, onClickHandler = 'showMovieDetail' } = options;
    
    if (!movies || movies.length === 0) {
        container.innerHTML = '<p class="empty-message">Aucun film trouvé</p>';
        return;
    }
    
    container.innerHTML = movies.map(movie => {
        const inWatchlist = watchlist.some(m => m.id === movie.id);
        return `
        <div class="movie-card" onclick="${onClickHandler}(${movie.id})">
            ${showWatchlistBtn ? `
                <button class="watchlist-btn ${inWatchlist ? 'in-watchlist' : ''}" 
                        onclick="event.stopPropagation(); toggleWatchlist(${movie.id}, '${encodeURIComponent(movie.title)}', '${movie.poster_path || ''}', ${movie.vote_average || 0})"
                        title="${inWatchlist ? 'Retirer de ma liste' : 'Ajouter à ma liste'}">
                    ${inWatchlist ? '✓' : '+'}
                </button>
            ` : ''}
            <img 
                src="${getMoviePosterUrl(movie.poster_path)}" 
                alt="${movie.title}"
                class="movie-poster"
                onerror="this.src='https://via.placeholder.com/200x280?text=No+Image'"
            >
            <div class="movie-info">
                <h3 class="movie-title" title="${movie.title}">${movie.title}</h3>
                <p class="movie-year">${movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A'}</p>
                ${movie.vote_average ? `
                    <span class="movie-rating">
                        <span class="star">⭐</span>
                        ${movie.vote_average.toFixed(1)}
                    </span>
                ` : ''}
            </div>
        </div>
    `}).join('');
}

function getMoviePosterUrl(path, size = 'w500') {
    if (!path) return 'https://via.placeholder.com/200x280?text=No+Image';
    return `https://image.tmdb.org/t/p/${size}${path}`;
}

// ===== Movie Detail =====
async function showMovieDetail(movieId) {
    showLoading();
    
    try {
        const [movieResponse, emotionsResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/api/v1/movies/${movieId}`),
            fetch(`${API_BASE_URL}/api/v1/movies/${movieId}/emotions`)
        ]);
        
        if (movieResponse.ok) {
            const movie = await movieResponse.json();
            const emotions = emotionsResponse.ok ? await emotionsResponse.json() : null;
            
            renderMovieDetail(movie, emotions);
            showPage('movie-detail-page');
        } else {
            alert('Film non trouvé');
        }
    } catch (error) {
        console.error('Error loading movie:', error);
        alert('Erreur de chargement du film');
    }
    
    hideLoading();
}

function renderMovieDetail(movie, emotions) {
    const container = document.getElementById('movie-detail-container');
    
    const baseEmotions = emotions?.base_emotions || {};
    const emotionColors = {
        joy: '#fbbf24',
        sadness: '#3b82f6',
        fear: '#7c3aed',
        anger: '#ef4444',
        surprise: '#f97316',
        disgust: '#10b981',
        neutral: '#6b7280'
    };
    
    const emotionIcons = {
        joy: '😊',
        sadness: '😢',
        fear: '😨',
        anger: '😠',
        surprise: '😲',
        disgust: '🤢',
        neutral: '😐'
    };
    
    const inWatchlist = watchlist.some(m => m.id === movie.id);
    
    container.innerHTML = `
        <div class="movie-detail">
            <div class="movie-detail-poster-container">
                <img 
                    src="${getMoviePosterUrl(movie.poster_path)}" 
                    alt="${movie.title}"
                    class="movie-detail-poster"
                    onerror="this.src='https://via.placeholder.com/300x450?text=No+Image'"
                >
                <div class="movie-detail-actions">
                    <button class="btn ${inWatchlist ? 'btn-secondary' : 'btn-primary'}" 
                            onclick="toggleWatchlist(${movie.id}, '${encodeURIComponent(movie.title)}', '${movie.poster_path || ''}', ${movie.vote_average || 0})">
                        ${inWatchlist ? '✓ Dans ma liste' : '📋 À voir plus tard'}
                    </button>
                    <button class="btn btn-share" onclick="shareMovie(${movie.id}, '${encodeURIComponent(movie.title)}')">
                        📤 Partager
                    </button>
                </div>
            </div>
            <div class="movie-detail-info">
                <h1>${movie.title}</h1>
                <div class="movie-detail-meta">
                    ${movie.release_date ? `<span>📅 ${new Date(movie.release_date).getFullYear()}</span>` : ''}
                    ${movie.runtime ? `<span>⏱️ ${movie.runtime} min</span>` : ''}
                    ${movie.genres ? `<span>🎭 ${movie.genres.map(g => typeof g === 'string' ? g : g.name).join(', ')}</span>` : ''}
                </div>
                ${movie.vote_average ? `
                    <div class="movie-detail-rating">
                        <span>⭐</span>
                        ${movie.vote_average.toFixed(1)} / 10
                    </div>
                ` : ''}
                <p class="movie-detail-overview">${movie.overview || 'Aucune description disponible.'}</p>
                
                ${Object.keys(baseEmotions).length > 0 ? `
                    <div class="movie-emotions-chart">
                        <h3>Analyse émotionnelle du film</h3>
                        <div class="emotion-bars">
                            ${Object.entries(baseEmotions).map(([emotion, value]) => `
                                <div class="emotion-bar">
                                    <div class="emotion-bar-label">
                                        <span>${emotionIcons[emotion] || '🎬'}</span>
                                        <span>${emotion}</span>
                                    </div>
                                    <div class="emotion-bar-track">
                                        <div 
                                            class="emotion-bar-fill" 
                                            style="width: ${value * 100}%; background-color: ${emotionColors[emotion] || '#6b7280'}"
                                        ></div>
                                    </div>
                                    <span class="emotion-bar-value">${Math.round(value * 100)}%</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// ===== Watchlist Functions =====
function loadWatchlist() {
    // Fallback: Load from localStorage
    const saved = localStorage.getItem('watchlist');
    if (saved) {
        watchlist = JSON.parse(saved);
    }
    renderWatchlist();
}

async function loadWatchlistFromAPI() {
    try {
        const response = await apiRequest('/api/v1/user/watchlist');
        if (response.ok) {
            watchlist = await response.json();
            renderWatchlist();
        } else {
            loadWatchlist();
        }
    } catch (error) {
        console.error('Error loading watchlist from API:', error);
        loadWatchlist();
    }
}

function saveWatchlist() {
    // Fallback: Save to localStorage
    localStorage.setItem('watchlist', JSON.stringify(watchlist));
}

async function toggleWatchlist(movieId, encodedTitle, posterPath, rating) {
    const title = decodeURIComponent(encodedTitle);
    const isInList = watchlist.some(m => m.id === movieId);
    
    try {
        if (isInList) {
            // Remove from watchlist via API
            const response = await apiRequest(`/api/v1/user/watchlist/${movieId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                watchlist = watchlist.filter(m => m.id !== movieId);
            }
        } else {
            // Add to watchlist via API
            const response = await apiRequest('/api/v1/user/watchlist', {
                method: 'POST',
                body: JSON.stringify({
                    movie_id: movieId,
                    title: title,
                    poster_path: posterPath || '',
                    vote_average: rating || 0
                })
            });
            if (response.ok) {
                watchlist.push({
                    id: movieId,
                    title: title,
                    poster_path: posterPath,
                    vote_average: rating
                });
            }
        }
    } catch (error) {
        console.error('Error updating watchlist:', error);
        // Fallback to local storage
        const index = watchlist.findIndex(m => m.id === movieId);
        if (index > -1) {
            watchlist.splice(index, 1);
        } else {
            watchlist.push({
                id: movieId,
                title: title,
                poster_path: posterPath,
                vote_average: rating
            });
        }
        saveWatchlist();
    }
    
    await loadUserStats();
    renderWatchlist();
    loadBestMovies();
}

function renderWatchlist() {
    const container = document.getElementById('watchlist-movies');
    
    if (watchlist.length === 0) {
        container.innerHTML = '<p class="empty-message">Votre liste est vide. Ajoutez des films en cliquant sur le bouton "+" sur les cartes de films !</p>';
        return;
    }
    
    container.innerHTML = watchlist.map(movie => `
        <div class="movie-card" onclick="showMovieDetail(${movie.id})">
            <button class="watchlist-btn in-watchlist" 
                    onclick="event.stopPropagation(); toggleWatchlist(${movie.id}, '${encodeURIComponent(movie.title)}', '${movie.poster_path || ''}', ${movie.vote_average || 0})"
                    title="Retirer de ma liste">
                ✓
            </button>
            <img 
                src="${getMoviePosterUrl(movie.poster_path)}" 
                alt="${movie.title}"
                class="movie-poster"
                onerror="this.src='https://via.placeholder.com/200x280?text=No+Image'"
            >
            <div class="movie-info">
                <h3 class="movie-title" title="${movie.title}">${movie.title}</h3>
                ${movie.vote_average ? `
                    <span class="movie-rating">
                        <span class="star">⭐</span>
                        ${movie.vote_average.toFixed(1)}
                    </span>
                ` : ''}
            </div>
        </div>
    `).join('');
}

async function clearWatchlist() {
    if (confirm('Voulez-vous vraiment vider votre liste à voir ?')) {
        try {
            const response = await apiRequest('/api/v1/user/watchlist', {
                method: 'DELETE'
            });
            if (response.ok) {
                watchlist = [];
            }
        } catch (error) {
            console.error('Error clearing watchlist:', error);
            watchlist = [];
            saveWatchlist();
        }
        
        await loadUserStats();
        renderWatchlist();
        loadBestMovies();
    }
}

function scrollToWatchlist() {
    document.getElementById('watchlist-section').scrollIntoView({ behavior: 'smooth' });
}

// ===== Advanced Filters =====
function applyFilters() {
    currentFilters = {
        decade: document.getElementById('filter-decade').value,
        genre: document.getElementById('filter-genre').value,
        duration: document.getElementById('filter-duration').value,
        rating: document.getElementById('filter-rating').value
    };
    
    loadBestMovies();
}

function resetFilters() {
    document.getElementById('filter-decade').value = '';
    document.getElementById('filter-genre').value = '';
    document.getElementById('filter-duration').value = '';
    document.getElementById('filter-rating').value = '';
    currentFilters = { decade: '', genre: '', duration: '', rating: '' };
    loadBestMovies();
}

async function loadBestMovies() {
    try {
        let url = `${API_BASE_URL}/api/v1/movies?limit=12&sort_by=vote_average`;
        
        if (currentFilters.rating) {
            url += `&min_rating=${currentFilters.rating}`;
        } else {
            url += '&min_rating=7.0';
        }
        
        if (currentFilters.genre) {
            url += `&genre=${currentFilters.genre}`;
        }
        
        const response = await fetch(url);
        
        if (response.ok) {
            let data = await response.json();
            let movies = data.movies || [];
            
            // Apply client-side filters
            if (currentFilters.decade) {
                const decadeStart = parseInt(currentFilters.decade);
                const decadeEnd = decadeStart === 1970 ? 1980 : decadeStart + 10;
                movies = movies.filter(m => {
                    if (!m.release_date) return false;
                    const year = new Date(m.release_date).getFullYear();
                    if (decadeStart === 1970) return year < 1980;
                    return year >= decadeStart && year < decadeEnd;
                });
            }
            
            if (currentFilters.duration) {
                const maxDuration = parseInt(currentFilters.duration);
                movies = movies.filter(m => {
                    if (!m.runtime) return true;
                    if (maxDuration === 90) return m.runtime < 90;
                    if (maxDuration === 120) return m.runtime >= 90 && m.runtime <= 120;
                    if (maxDuration === 180) return m.runtime > 120;
                    return true;
                });
            }
            
            allMoviesCache = movies;
            renderMovies('best-movies', movies);
        }
    } catch (error) {
        console.error('Error loading movies:', error);
        document.getElementById('best-movies').innerHTML = '<p class="empty-message">Erreur de chargement des films</p>';
    }
}

// ===== Compare Functions =====
function toggleCompareMode() {
    compareMovies = [];
    updateCompareSelection();
    loadMoviesForCompare();
    showModal('compare-modal');
}

async function loadMoviesForCompare() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/movies?limit=20&sort_by=vote_average&min_rating=7.0`);
        if (response.ok) {
            const data = await response.json();
            renderCompareMovies(data.movies || []);
        }
    } catch (error) {
        console.error('Error loading movies for compare:', error);
    }
}

function renderCompareMovies(movies) {
    const container = document.getElementById('compare-available-movies');
    
    container.innerHTML = movies.map(movie => `
        <div class="movie-card" onclick="addToCompare(${movie.id}, '${encodeURIComponent(movie.title)}', '${movie.poster_path || ''}')">
            <img 
                src="${getMoviePosterUrl(movie.poster_path)}" 
                alt="${movie.title}"
                class="movie-poster"
                onerror="this.src='https://via.placeholder.com/200x280?text=No+Image'"
            >
            <div class="movie-info">
                <h3 class="movie-title" title="${movie.title}">${movie.title}</h3>
            </div>
        </div>
    `).join('');
}

function searchMoviesForCompare() {
    const query = document.getElementById('compare-search').value.toLowerCase();
    const container = document.getElementById('compare-available-movies');
    
    if (!query) {
        loadMoviesForCompare();
        return;
    }
    
    // Filter from cache or reload
    fetch(`${API_BASE_URL}/api/v1/movies?limit=30&sort_by=vote_average`)
        .then(res => res.json())
        .then(data => {
            const filtered = (data.movies || []).filter(m => 
                m.title.toLowerCase().includes(query)
            );
            renderCompareMovies(filtered);
        });
}

function addToCompare(movieId, encodedTitle, posterPath) {
    if (compareMovies.length >= 3) {
        alert('Vous pouvez comparer maximum 3 films');
        return;
    }
    
    if (compareMovies.some(m => m.id === movieId)) {
        return;
    }
    
    compareMovies.push({
        id: movieId,
        title: decodeURIComponent(encodedTitle),
        poster_path: posterPath
    });
    
    updateCompareSelection();
}

function removeFromCompare(movieId) {
    compareMovies = compareMovies.filter(m => m.id !== movieId);
    updateCompareSelection();
    document.getElementById('compare-results').classList.add('hidden');
}

function updateCompareSelection() {
    const container = document.getElementById('compare-selection');
    const compareBtn = document.getElementById('compare-btn');
    
    let html = '';
    for (let i = 0; i < 3; i++) {
        if (compareMovies[i]) {
            html += `
                <div class="compare-slot filled">
                    <img src="${getMoviePosterUrl(compareMovies[i].poster_path)}" alt="${compareMovies[i].title}">
                    <button class="remove-btn" onclick="removeFromCompare(${compareMovies[i].id})">×</button>
                </div>
            `;
        } else {
            html += `
                <div class="compare-slot">
                    <span>+</span>
                    <span>Film ${i + 1}</span>
                </div>
            `;
        }
    }
    
    container.innerHTML = html;
    compareBtn.disabled = compareMovies.length < 2;
}

async function compareSelectedMovies() {
    if (compareMovies.length < 2) return;
    
    showLoading();
    
    const emotionColors = {
        joy: '#fbbf24',
        sadness: '#3b82f6',
        fear: '#7c3aed',
        anger: '#ef4444',
        surprise: '#f97316',
        disgust: '#10b981'
    };
    
    try {
        const emotionsData = await Promise.all(
            compareMovies.map(movie => 
                fetch(`${API_BASE_URL}/api/v1/movies/${movie.id}/emotions`)
                    .then(res => res.ok ? res.json() : { emotions: {} })
                    .catch(() => ({ emotions: {} }))
            )
        );
        
        const resultsContainer = document.getElementById('compare-results');
        resultsContainer.classList.remove('hidden');
        
        resultsContainer.innerHTML = `
            <h3>Comparaison des profils émotionnels</h3>
            <div class="compare-chart">
                ${compareMovies.map((movie, index) => {
                    // Support both 'emotions' and 'base_emotions' formats
                    const emotionData = emotionsData[index] || {};
                    const emotions = emotionData.emotions || emotionData.base_emotions || {};
                    return `
                        <div class="compare-movie-chart">
                            <h4>${movie.title}</h4>
                            <div class="compare-bars">
                                ${['joy', 'sadness', 'fear', 'anger', 'surprise', 'disgust'].map(emotion => `
                                    <div class="compare-bar">
                                        <span class="compare-bar-label">${emotion}</span>
                                        <div class="compare-bar-track">
                                            <div class="compare-bar-fill" style="width: ${(emotions[emotion] || 0) * 100}%; background-color: ${emotionColors[emotion]}"></div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Error comparing movies:', error);
    }
    
    hideLoading();
}

// ===== Share Functions =====
function openShareModal() {
    updateSharePreview();
    showModal('share-modal');
}

function updateSharePreview() {
    const preview = document.getElementById('share-preview');
    const username = currentUser?.username || 'Utilisateur';
    
    const topEmotions = Object.entries(emotionProfile)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .filter(([_, value]) => value > 0);
    
    preview.innerHTML = `
        <div class="logo-title">🎬 Cine<span class="gold">Feels</span></div>
        <p>Le profil émotionnel de <strong class="gold">${username}</strong></p>
        <div class="profile-summary">
            ${topEmotions.length > 0 
                ? topEmotions.map(([emotion, value]) => `
                    <span class="emotion-pill">${emotion}: ${Math.round(value * 100)}%</span>
                `).join('')
                : '<span class="emotion-pill">Découvrez votre profil !</span>'
            }
        </div>
        <p style="margin-top: 16px; font-size: 0.85rem; color: var(--slate-400)">
            ${analysisHistory.length} analyses • ${watchlist.length} films à voir
        </p>
    `;
}

function shareOnTwitter() {
    const text = generateShareText();
    const url = encodeURIComponent(window.location.href);
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${url}`, '_blank');
}

function shareOnFacebook() {
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank');
}

function shareOnWhatsApp() {
    const text = generateShareText();
    window.open(`https://wa.me/?text=${encodeURIComponent(text + ' ' + window.location.href)}`, '_blank');
}

function copyShareLink() {
    const text = generateShareText() + '\n' + window.location.href;
    navigator.clipboard.writeText(text).then(() => {
        const copied = document.getElementById('share-copied');
        copied.classList.remove('hidden');
        setTimeout(() => copied.classList.add('hidden'), 2000);
    });
}

function generateShareText() {
    const username = currentUser?.username || 'Je';
    const topEmotion = Object.entries(emotionProfile)
        .sort((a, b) => b[1] - a[1])[0];
    
    if (topEmotion && topEmotion[1] > 0) {
        return `🎬 ${username} utilise CineFeels pour découvrir des films ! Mon émotion dominante: ${topEmotion[0]} (${Math.round(topEmotion[1] * 100)}%). Découvre ton profil émotionnel !`;
    }
    return `🎬 Découvrez CineFeels - la plateforme qui recommande des films selon vos émotions ! Propulsé par l'IA BERT.`;
}

function shareMovie(movieId, encodedTitle) {
    const title = decodeURIComponent(encodedTitle);
    const text = `🎬 Je viens de découvrir "${title}" sur CineFeels ! Une recommandation basée sur les émotions, propulsée par l'IA.`;
    
    if (navigator.share) {
        navigator.share({
            title: 'CineFeels - ' + title,
            text: text,
            url: window.location.href
        });
    } else {
        navigator.clipboard.writeText(text + ' ' + window.location.href).then(() => {
            alert('Lien copié dans le presse-papier !');
        });
    }
}
