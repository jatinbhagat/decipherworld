/**
 * Constitution Challenge Game Controller
 * Handles game state, API calls, and UI interactions
 */

class ConstitutionGameController {
    constructor(sessionCode, teamId) {
        this.sessionCode = sessionCode;
        this.teamId = teamId;
        this.cityRenderer = null;
        this.audioSystem = null;
        this.isProcessingAnswer = false;
        
        this.initializeGame();
        console.log('🎮 Constitution Game Controller initialized');
    }
    
    async initializeGame() {
        // Initialize audio system
        if (window.AudioSystem) {
            this.audioSystem = new window.AudioSystem();
        }
        
        // Initialize city renderer when available
        this.initializeCityRenderer();
        
        // Load initial game state
        await this.loadGameState();
        
        // Set up keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        console.log('🏙️ Enhanced City game initialized');
    }
    
    initializeCityRenderer() {
        const cityCanvas = document.getElementById('city-canvas');
        if (!cityCanvas) {
            console.warn('⚠️ City canvas element not found');
            return;
        }
        
        if (window.CityRenderer) {
            console.log('🏗️ Initializing CityRenderer...');
            this.cityRenderer = new window.CityRenderer('city-canvas', {
                width: cityCanvas.offsetWidth,
                height: cityCanvas.offsetHeight
            });
            
            // Load initial city state
            this.loadCityState();
            console.log('✅ CityRenderer initialized successfully');
        } else {
            console.warn('⚠️ CityRenderer not available yet, will retry...');
            // Retry after a short delay
            setTimeout(() => this.initializeCityRenderer(), 100);
        }
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            switch (e.key.toLowerCase()) {
                case 'f':
                    this.triggerCityAnimation('fireworks');
                    break;
                case 'p':
                    this.triggerCityAnimation('parade');
                    break;
                case 'c':
                    this.triggerCityAnimation('celebration');
                    break;
                case 'r':
                    this.refreshCity();
                    break;
                case 'm':
                    this.toggleAudio();
                    break;
            }
        });
    }
    
    async loadGameState() {
        try {
            const response = await fetch(`/learn/api/constitution/${this.sessionCode}/state/?team_id=${this.teamId}`);
            const data = await response.json();
            
            if (data.success) {
                this.updateUI(data);
            }
        } catch (error) {
            console.error('Failed to load game state:', error);
            this.showFeedback('Failed to load game state', 'error');
        }
    }
    
    loadCityState() {
        const defaultState = {
            terrain: { type: 'barren', features: [] },
            buildings: { residential: [], civic: [], commercial: [] },
            citizens: { population: 20, mood: 'neutral', activities: [] },
            weather: { type: 'cloudy', effects: [] },
            animations: [],
            sound_cues: []
        };
        
        if (this.cityRenderer) {
            this.cityRenderer.render(defaultState);
        }
    }
    
    async selectAnswer(optionId, optionLetter) {
        if (this.isProcessingAnswer || !this.teamId) {
            this.showFeedback('Please wait or create a team first', 'error');
            return;
        }
        
        this.isProcessingAnswer = true;
        
        // Disable all answer buttons
        const buttons = document.querySelectorAll('.interactive-answer-btn');
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
        });
        
        this.showFeedback('⏳ Making constitutional decision...', 'info');
        
        try {
            const response = await fetch(`/learn/api/constitution/${this.sessionCode}/answer/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: `team_id=${this.teamId}&option_id=${optionId}`
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.handleSuccessfulAnswer(data);
            } else {
                this.showFeedback(data.error || 'Failed to submit answer', 'error');
                this.enableAnswerButtons();
            }
        } catch (error) {
            console.error('Answer submission error:', error);
            this.showFeedback('Network error. Please try again.', 'error');
            this.enableAnswerButtons();
        } finally {
            this.isProcessingAnswer = false;
        }
    }
    
    async handleSuccessfulAnswer(data) {
        // Show answer feedback
        this.showAnswerFeedback(data);
        
        // Update team stats
        this.updateTeamStats(data.team_update);
        
        // Update city state
        this.updateCityState(data.country_state);
        
        // Play sound cues
        this.playSoundCues(data.country_state.visual_elements?.sound_cues || []);
        
        // Show learning module if available
        if (data.learning_module) {
            setTimeout(() => this.showLearningModule(data.learning_module), 3000);
        }
        
        // Handle next question or completion
        if (data.next_question) {
            setTimeout(() => this.loadNextQuestion(), 5000);
        } else {
            setTimeout(() => this.showGameCompletion(data), 5000);
        }
    }
    
    enableAnswerButtons() {
        const buttons = document.querySelectorAll('.interactive-answer-btn');
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('opacity-50', 'cursor-not-allowed');
        });
    }
    
    updateUI(data) {
        // Update team stats
        if (data.team) {
            this.updateTeamStats(data.team);
        }
        
        // Update city state
        if (data.country_state) {
            this.updateCityState(data.country_state);
        }
        
        // Update leaderboard
        if (data.leaderboard) {
            this.updateLeaderboard(data.leaderboard);
        }
    }
    
    updateTeamStats(teamData) {
        if (!teamData) return;
        
        // Update total score
        const totalScoreEl = document.getElementById('total-score');
        if (totalScoreEl) {
            this.animateValue(totalScoreEl, parseInt(totalScoreEl.textContent) || 0, teamData.total_score, 800);
        }
        
        // Update rank
        const rankEl = document.getElementById('team-rank-display');
        if (rankEl && teamData.rank) {
            rankEl.textContent = teamData.rank;
        }
    }
    
    updateCityState(countryState) {
        if (!countryState) return;
        
        // Update governance meters
        const metrics = ['democracy', 'fairness', 'freedom', 'stability'];
        metrics.forEach(metric => {
            const score = countryState[`${metric}_score`];
            const scoreEl = document.getElementById(`${metric}-score`);
            const barEl = scoreEl?.parentElement?.nextElementSibling?.firstElementChild;
            
            if (scoreEl && barEl) {
                const oldScore = parseInt(scoreEl.textContent.split('/')[0]) || 0;
                this.animateValue(scoreEl, oldScore, score, 600, (value) => {
                    scoreEl.textContent = `${Math.round(value)}/10`;
                });
                
                // Animate bar width
                barEl.style.width = `${score * 10}%`;
                barEl.parentElement.classList.add('governance-meter-increase');
                setTimeout(() => {
                    barEl.parentElement.classList.remove('governance-meter-increase');
                }, 600);
            }
        });
        
        // Render updated city
        if (this.cityRenderer && countryState.visual_elements) {
            this.cityRenderer.render(countryState.visual_elements);
        }
    }
    
    playSoundCues(soundCues) {
        if (!Array.isArray(soundCues) || !this.audioSystem) return;
        
        soundCues.forEach((cue, index) => {
            setTimeout(() => {
                this.audioSystem.playSound(cue);
            }, index * 200);
        });
    }
    
    showAnswerFeedback(data) {
        const feedback = data.feedback;
        const points = feedback.points_earned;
        const pointsText = points > 0 ? `+${points}` : `${points}`;
        const pointsColor = points > 0 ? 'text-green-600' : points < 0 ? 'text-red-600' : 'text-gray-600';
        
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-30 z-40 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 transform scale-95">
                <div class="text-center mb-4">
                    <div class="text-4xl mb-2">${points > 0 ? '🎉' : points < 0 ? '😟' : '🤔'}</div>
                    <h3 class="text-xl font-bold text-gray-800">${feedback.governance_principle || 'Your Choice'}</h3>
                    <div class="text-2xl font-bold ${pointsColor} mt-2">${pointsText} points</div>
                </div>
                <p class="text-gray-700 leading-relaxed mb-4">${feedback.explanation || ''}</p>
                <div class="text-sm text-blue-600 bg-blue-50 rounded-lg p-3">
                    ${feedback.constitutional_insight || 'Every decision shapes your nation\'s future.'}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            modal.style.opacity = '0';
            modal.style.transform = 'scale(0.95)';
            setTimeout(() => {
                if (document.body.contains(modal)) {
                    document.body.removeChild(modal);
                }
            }, 300);
        }, 4000);
    }
    
    showFeedback(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-20 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded-full shadow-lg backdrop-blur-sm transition-all duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'info' ? 'bg-blue-500 text-white' : 'bg-gray-700 text-white'
        }`;
        toast.textContent = message;
        toast.style.opacity = '0';
        
        document.body.appendChild(toast);
        
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translate(-50%, 0)';
        });
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }
    
    animateValue(element, start, end, duration, callback = null) {
        const startTime = performance.now();
        const difference = end - start;
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const value = start + difference * this.easeOutQuad(progress);
            
            if (callback) {
                callback(value);
            } else if (element) {
                element.textContent = Math.round(value);
            }
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    easeOutQuad(t) {
        return t * (2 - t);
    }
    
    triggerCityAnimation(animationType) {
        if (this.cityRenderer && this.cityRenderer.createAnimation) {
            this.cityRenderer.createAnimation(animationType);
        }
        
        if (this.audioSystem) {
            this.audioSystem.playSound(animationType);
        }
    }
    
    refreshCity() {
        if (this.cityRenderer) {
            this.loadCityState();
            this.showFeedback('City refreshed', 'success');
        }
    }
    
    toggleAudio() {
        if (this.audioSystem) {
            const enabled = this.audioSystem.toggle();
            this.updateAudioUI(enabled);
        }
    }
    
    updateAudioUI(enabled) {
        const audioIcon = document.getElementById('audio-icon');
        const audioBtn = document.getElementById('audio-toggle-btn');
        
        if (!audioIcon || !audioBtn) return;
        
        if (enabled) {
            audioIcon.textContent = '🔊';
            audioBtn.classList.remove('bg-red-100', 'hover:bg-red-200');
            audioBtn.classList.add('bg-blue-100', 'hover:bg-blue-200');
            audioIcon.classList.remove('text-red-600');
            audioIcon.classList.add('text-blue-600');
        } else {
            audioIcon.textContent = '🔇';
            audioBtn.classList.remove('bg-blue-100', 'hover:bg-blue-200');
            audioBtn.classList.add('bg-red-100', 'hover:bg-red-200');
            audioIcon.classList.remove('text-blue-600');
            audioIcon.classList.add('text-red-600');
        }
    }
    
    testAudio(soundName) {
        if (this.audioSystem) {
            this.audioSystem.playSound(soundName);
            this.showFeedback(`Testing ${soundName} sound`, 'info');
        }
    }
    
    // Cleanup method
    destroy() {
        if (this.audioSystem) {
            this.audioSystem.destroy();
        }
        
        if (this.cityRenderer && this.cityRenderer.destroy) {
            this.cityRenderer.destroy();
        }
        
        console.log('🎮 Game Controller destroyed');
    }
}

// Export for global use
window.ConstitutionGameController = ConstitutionGameController;