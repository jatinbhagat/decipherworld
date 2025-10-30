// Password Fortress Game JavaScript
// Extracted from template for Azure deployment optimization

window.PasswordFortress = {
    // Global variables
    selectedAnswer: null,
    sessionCode: null,
    currentChallengeId: null,
    
    // Initialize the game with Django template variables
    init: function(sessionCode, challengeId) {
        this.sessionCode = sessionCode;
        this.currentChallengeId = challengeId;
    },

    // CSRF Cookie Helper
    getCookie: function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    // Start Mission Function
    startMission: function() {
        fetch(`/cyber-city/${this.sessionCode}/action/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                action_type: 'start_mission'
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert('Failed to start mission. Please try again.');
            }
        })
        .catch(error => {
            console.error('Start mission error:', error);
            alert('Failed to start mission. Please try again.');
        });
    },

    // Voice synthesis function for Captain Tessa
    speakText: function(text) {
        if (!text || text.trim() === '') return;
        
        try {
            speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            
            utterance.rate = 1.3;
            utterance.pitch = 1.1;
            utterance.volume = 0.8;
            
            const voices = speechSynthesis.getVoices();
            const friendlyVoice = voices.find(voice => 
                voice.name.includes('Female') || 
                voice.name.includes('Samantha') ||
                voice.name.includes('Zira') ||
                voice.name.includes('Susan')
            );
            
            if (friendlyVoice) {
                utterance.voice = friendlyVoice;
            }
            
            const voiceIndicator = document.getElementById('voiceIndicator');
            if (voiceIndicator) {
                voiceIndicator.style.display = 'block';
                utterance.onend = () => {
                    voiceIndicator.style.display = 'none';
                };
                utterance.onerror = () => {
                    voiceIndicator.style.display = 'none';
                };
            }
            
            speechSynthesis.speak(utterance);
        } catch (error) {
            console.log('Voice synthesis not available:', error);
        }
    },

    // Update Tessa's dialogue
    updateTessaDialogue: function(message, useVoice = true) {
        const tessaDialogue = document.getElementById('tessaDialogue');
        if (tessaDialogue) {
            tessaDialogue.innerHTML = message;
            
            setTimeout(() => {
                tessaDialogue.scrollTop = tessaDialogue.scrollHeight;
            }, 100);
            
            if (useVoice) {
                const spokenText = message.replace(/<[^>]*>/g, '');
                this.speakText(spokenText);
            }
        }
    },

    // Select answer option
    selectOption: function(option) {
        this.selectedAnswer = option;
        
        // Clear all option selections first
        document.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.remove('btn-primary', 'ring-2', 'ring-primary', 'border-primary');
            btn.classList.add('btn-outline');
            btn.style.borderColor = '';
        });
        
        // Find and highlight the clicked option
        const selectedBtn = event.target.closest('.option-btn');
        if (selectedBtn) {
            selectedBtn.classList.remove('btn-outline');
            selectedBtn.classList.add('btn-primary', 'ring-2', 'ring-primary');
            selectedBtn.style.borderColor = '#3b82f6';
        }
        
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('btn-disabled');
            submitBtn.classList.add('btn-success');
        }
    },

    // Submit answer
    submitAnswer: function() {
        if (!this.selectedAnswer) {
            alert('Please select an answer first!');
            return;
        }

        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading loading-spinner loading-sm"></span> Submitting...';
        }

        fetch(`/cyber-city/${this.sessionCode}/action/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                action_type: 'submit_answer',
                challenge_id: this.currentChallengeId,
                answer: this.selectedAnswer
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            this.showResult(data);
        })
        .catch(error => {
            console.error('Submit answer error:', error);
            alert('Failed to submit answer. Please try again.');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Submit Answer';
            }
        });
    },

    // Show answer result
    showResult: function(data) {
        if (data.mission_complete) {
            this.showPasswordGameCompletion(data);
            return;
        }

        let resultMessage = '';
        let resultClass = '';
        let iconClass = '';
        
        if (data.correct) {
            resultClass = 'alert-success';
            iconClass = 'fas fa-check-circle text-green-600';
            resultMessage = `
                <div class="flex items-center gap-3">
                    <i class="${iconClass} text-2xl"></i>
                    <div>
                        <h3 class="font-bold text-lg">Excellent work, Agent!</h3>
                        <p>${data.explanation || 'You\'ve successfully identified the correct security practice.'}</p>
                    </div>
                </div>
            `;
        } else {
            resultClass = 'alert-error';
            iconClass = 'fas fa-times-circle text-red-600';
            resultMessage = `
                <div class="flex items-center gap-3">
                    <i class="${iconClass} text-2xl"></i>
                    <div>
                        <h3 class="font-bold text-lg">Not quite right, Agent.</h3>
                        <p>${data.explanation || 'Let me explain the correct security approach.'}</p>
                    </div>
                </div>
            `;
        }

        document.getElementById('gameArea').innerHTML = `
            <div class="text-center space-y-6">
                <div class="alert ${resultClass} max-w-2xl mx-auto">
                    ${resultMessage}
                </div>
                
                <button onclick="PasswordFortress.continueGame(${data.mission_complete}, ${data.correct})" 
                        class="btn btn-primary btn-lg">
                    <i class="fas fa-arrow-right mr-2"></i>
                    Continue Mission
                </button>
            </div>
        `;

        this.updateTessaDialogue(data.explanation || (data.correct ? 'Great job! Ready for the next challenge?' : 'Let me explain the correct approach, then we\'ll move forward.'));
    },

    // Show game completion screen
    showPasswordGameCompletion: function(data) {
        const correctAnswers = data.correct_answers || 0;
        const totalChallenges = data.total_challenges || 5;
        const securityPercentage = Math.round((correctAnswers / totalChallenges) * 100);
        const completionData = data.completion_message || {};
        
        let completionMessage = '';
        let completionClass = '';
        let completionTitle = '';
        
        if (completionData.performance === 'excellent') {
            completionTitle = completionData.title || 'FORTRESS MASTER!';
            completionMessage = completionData.message || "Outstanding security awareness! You've proven yourself as a true cybersecurity champion.";
            completionClass = 'alert-success';
        } else if (completionData.performance === 'good') {
            completionTitle = completionData.title || 'GOOD WORK!';
            completionMessage = completionData.message || "Well done! You have a solid understanding of password security.";
            completionClass = 'alert-info';
        } else {
            completionTitle = completionData.title || 'MISSION COMPLETE';
            completionMessage = completionData.message || "You've completed the challenges! Consider reviewing cybersecurity best practices to strengthen your digital defense skills.";
            completionClass = 'alert-warning';
        }

        const gameCompletionHTML = `
            <div class="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
                <div class="max-w-2xl w-full bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl p-8 text-center space-y-6">
                    <div class="space-y-4">
                        <div class="text-6xl">🏆</div>
                        <h1 class="text-4xl font-bold text-slate-800">Mission Complete!</h1>
                        <p class="text-xl text-slate-600">Password Fortress Secured</p>
                    </div>
                    
                    <div class="grid md:grid-cols-3 gap-6 my-8">
                        <div class="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-xl">
                            <div class="text-3xl font-bold">${totalChallenges}/5</div>
                            <div class="text-sm opacity-90">Challenges</div>
                        </div>
                        <div class="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-xl">
                            <div class="text-3xl font-bold">${correctAnswers}/5</div>
                            <div class="text-sm opacity-90">Correct Answers</div>
                        </div>
                        <div class="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-xl">
                            <div class="text-3xl font-bold">${securityPercentage}%</div>
                            <div class="text-sm opacity-90">Security Level</div>
                        </div>
                    </div>
                    
                    <div class="alert ${completionClass} text-left">
                        <div class="flex items-start gap-3">
                            <i class="fas fa-shield-alt text-2xl mt-1"></i>
                            <div>
                                <h3 class="font-bold text-lg">${completionTitle}</h3>
                                <p>${completionMessage}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="flex flex-col sm:flex-row gap-4 justify-center pt-6">
                        <a href="/cyber-city/" class="btn btn-primary btn-lg">
                            <i class="fas fa-city mr-2"></i>
                            Return to Cyber City
                        </a>
                        <a href="/games/" class="btn btn-outline btn-lg">
                            <i class="fas fa-gamepad mr-2"></i>
                            More Games
                        </a>
                    </div>
                </div>
            </div>
        `;

        document.body.innerHTML = gameCompletionHTML;
        this.createCelebrationEffects();
    },

    // Create celebration effects
    createCelebrationEffects: function() {
        for (let i = 0; i < 50; i++) {
            setTimeout(() => {
                const confetti = document.createElement('div');
                confetti.innerHTML = ['🎉', '✨', '🎊', '⭐', '💫'][Math.floor(Math.random() * 5)];
                confetti.style.position = 'fixed';
                confetti.style.left = Math.random() * 100 + 'vw';
                confetti.style.top = '-10px';
                confetti.style.fontSize = '20px';
                confetti.style.zIndex = '9999';
                confetti.style.pointerEvents = 'none';
                confetti.style.animation = 'fall 3s linear forwards';
                
                document.body.appendChild(confetti);
                
                setTimeout(() => {
                    if (confetti.parentNode) {
                        confetti.parentNode.removeChild(confetti);
                    }
                }, 3000);
            }, i * 100);
        }
    },

    // Continue game after answer
    continueGame: function(missionComplete, isCorrect = true) {
        if (missionComplete) {
            window.location.href = '/cyber-city/';
            return;
        }

        // Always progress to next question regardless of correct/incorrect
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    },

    // Progress after wrong answer for Password Fortress
    progressPasswordAfterWrongAnswer: function() {
        fetch(`/cyber-city/${this.sessionCode}/action/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                action_type: 'progress_password_after_wrong_answer',
                challenge_id: this.currentChallengeId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.action_result === 'progress_success') {
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                console.error('Failed to progress:', data);
                window.location.reload();
            }
        })
        .catch(error => {
            console.error('Progress error:', error);
            window.location.reload();
        });
    },

    // Legacy function for compatibility
    progressAfterWrongAnswer: function() {
        return this.progressPasswordAfterWrongAnswer();
    },

    // Rating system
    setRating: function(rating) {
        document.querySelectorAll('.star').forEach((star, index) => {
            if (index < rating) {
                star.classList.add('text-yellow-400');
                star.classList.remove('text-gray-300');
            } else {
                star.classList.add('text-gray-300');
                star.classList.remove('text-yellow-400');
            }
        });
        
        document.getElementById('selectedRating').value = rating;
        document.getElementById('submitReview').disabled = false;
    },

    // Submit game review
    submitGameReview: function() {
        const rating = document.getElementById('selectedRating').value;
        const feedback = document.getElementById('feedbackText').value;
        
        if (!rating) {
            alert('Please select a rating!');
            return;
        }

        fetch(`/cyber-city/${this.sessionCode}/action/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                action_type: 'submit_review',
                rating: rating,
                feedback: feedback
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('reviewSection').innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle"></i>
                        <span>Thank you for your feedback! Your review helps us improve the game.</span>
                    </div>
                `;
            } else {
                alert('Failed to submit review. Please try again.');
            }
        })
        .catch(error => {
            console.error('Review submission error:', error);
            alert('Failed to submit review. Please try again.');
        });
    },

    // Music controls
    toggleMusic: function() {
        const music = document.getElementById('backgroundMusic');
        const toggleBtn = document.getElementById('musicToggle');
        
        if (music && toggleBtn) {
            if (music.paused) {
                music.play().catch(e => console.log('Audio play failed:', e));
                toggleBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
                toggleBtn.classList.remove('btn-outline');
                toggleBtn.classList.add('btn-primary');
            } else {
                music.pause();
                toggleBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
                toggleBtn.classList.remove('btn-primary');
                toggleBtn.classList.add('btn-outline');
            }
        }
    },

    // Initialize music
    initializeMusic: function() {
        const music = document.getElementById('backgroundMusic');
        if (music) {
            music.volume = 0.3;
            music.play().catch(e => console.log('Auto-play prevented:', e));
        }
    },

    // Theme toggle (if needed)
    toggleTheme: function() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }
};

// Global functions for backwards compatibility
function startMission() { return PasswordFortress.startMission(); }
function selectOption(option) { return PasswordFortress.selectOption(option); }
function submitAnswer() { return PasswordFortress.submitAnswer(); }
function continueGame(missionComplete, isCorrect) { return PasswordFortress.continueGame(missionComplete, isCorrect); }
function progressAfterWrongAnswer() { return PasswordFortress.progressAfterWrongAnswer(); }
function setRating(rating) { return PasswordFortress.setRating(rating); }
function submitGameReview() { return PasswordFortress.submitGameReview(); }
function toggleMusic() { return PasswordFortress.toggleMusic(); }

// CSS for falling animation
const style = document.createElement('style');
style.textContent = `
@keyframes fall {
    to {
        transform: translateY(100vh) rotate(360deg);
    }
}
`;
document.head.appendChild(style);