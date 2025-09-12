/**
 * Constitution Challenge Game JavaScript
 * Handles all game interactions, API calls, and UI updates
 */

// Game state
let isLeaderboardOpen = false;
let gameController = null;

// Audio cues for better user experience
function playAudioCue(type) {
    try {
        // Create audio context if it doesn't exist
        if (!window.audioContext) {
            window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        const ctx = window.audioContext;
        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);
        
        // Define sound patterns for different interactions
        const sounds = {
            click: { frequency: 800, duration: 0.1, type: 'square' },
            success: { frequency: 600, duration: 0.2, type: 'sine' },
            error: { frequency: 200, duration: 0.3, type: 'sawtooth' },
            notification: { frequency: 1000, duration: 0.15, type: 'triangle' }
        };
        
        const sound = sounds[type] || sounds.click;
        
        oscillator.type = sound.type;
        oscillator.frequency.setValueAtTime(sound.frequency, ctx.currentTime);
        
        gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + sound.duration);
        
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + sound.duration);
        
    } catch (error) {
        // Graceful fallback - audio cues are optional
        console.log('Audio cue not available:', error);
    }
}

// Utility functions
function getCsrfToken() {
    // Try multiple ways to get CSRF token
    let token = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
                document.querySelector('[data-csrf]')?.getAttribute('data-csrf') ||
                '';
    
    console.log('🔍 CSRF Token found:', token ? 'Yes' : 'No', token ? `(${token.substring(0, 10)}...)` : '');
    return token;
}

// UI Functions
function toggleLeaderboard() {
    console.log('🔍 LEADERBOARD DEBUG: toggleLeaderboard() called');
    
    const panel = document.getElementById('leaderboard-panel');
    if (!panel) {
        console.error('❌ Leaderboard panel not found! DOM element missing.');
        showGameNotification('⚠️ Leaderboard panel not available', 'error', 3000);
        return;
    }
    
    console.log('✅ LEADERBOARD DEBUG: Panel found:', panel);
    playAudioCue('click');
    
    // More robust way to check if panel is currently hidden
    const computedStyle = window.getComputedStyle(panel);
    const currentTransform = computedStyle.transform;
    const isHidden = panel.classList.contains('translate-x-full') || 
                     currentTransform.includes('translateX') && !currentTransform.includes('translateX(0px)');
    
    console.log(`📊 Leaderboard toggle - Currently hidden: ${isHidden}`);
    console.log(`📊 Panel classes:`, panel.className);
    console.log(`📊 Computed transform:`, currentTransform);
    
    if (isHidden) {
        // Show leaderboard
        panel.classList.remove('translate-x-full');
        panel.classList.add('translate-x-0'); // Explicitly set to visible position
        console.log('✅ Leaderboard opened - panel should now be visible');
        
        // Load data when opening, with better error handling
        console.log('🔄 Loading leaderboard data...');
        refreshLeaderboard().catch(error => {
            console.error('Failed to refresh leaderboard:', error);
            showGameNotification('⚠️ Failed to load leaderboard data', 'error', 3000);
        });
    } else {
        // Hide leaderboard
        panel.classList.remove('translate-x-0');
        panel.classList.add('translate-x-full');
        console.log('❌ Leaderboard closed - panel should now be hidden');
    }
    
    // Update isLeaderboardOpen state
    isLeaderboardOpen = !isHidden;
    
    // Additional debugging: Check final state
    setTimeout(() => {
        const finalHidden = panel.classList.contains('translate-x-full');
        const finalTransform = window.getComputedStyle(panel).transform;
        console.log(`📊 Final state - Hidden: ${finalHidden}, Transform: ${finalTransform}`);
    }, 350); // Wait for transition to complete
}

function toggleHelp() {
    console.log('🔍 HELP DEBUG: toggleHelp() called');
    
    const modal = document.getElementById('help-modal');
    if (!modal) {
        console.error('❌ Help modal not found! DOM element missing.');
        showGameNotification('⚠️ Help modal not available', 'error', 3000);
        return;
    }
    
    console.log('✅ HELP DEBUG: Help modal found:', modal);
    playAudioCue('click');
    
    // Add debug logging
    const isHidden = modal.classList.contains('hidden');
    console.log(`❓ Help toggle - Currently hidden: ${isHidden}`);
    console.log(`❓ Modal classes before toggle:`, modal.className);
    
    if (isHidden) {
        modal.classList.remove('hidden');
        console.log('✅ Help modal opened - classes after:', modal.className);
    } else {
        modal.classList.add('hidden');
        console.log('❌ Help modal closed - classes after:', modal.className);
    }
}

// Simple notification system - only for important messages
function showGameNotification(message, type = 'info', duration = 2000) {
    // Skip spam notifications, but allow error messages
    if (message.includes('updated') || (type === 'info' && !message.includes('⚠️'))) return;
    
    const existing = document.querySelectorAll('.game-notification');
    existing.forEach(el => el.remove());
    
    const notification = document.createElement('div');
    notification.className = `game-notification fixed bottom-4 right-4 z-50 opacity-0 transition-opacity duration-300`;
    
    const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-gray-800';
    
    notification.innerHTML = `
        <div class="${bgColor} text-white px-4 py-2 rounded-lg shadow-lg text-sm">
            ${message}
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.remove('opacity-0'), 100);
    setTimeout(() => {
        notification.classList.add('opacity-0');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Answer submission
async function submitAnswerDirectly(optionId, optionLetter) {
    const sessionCode = document.querySelector('[data-session-code]')?.getAttribute('data-session-code');
    const teamId = document.querySelector('[data-team-id]')?.getAttribute('data-team-id');
    
    console.log('🔍 DEBUG: Session Code:', sessionCode);
    console.log('🔍 DEBUG: Team ID:', teamId);
    console.log('🔍 DEBUG: Option ID:', optionId);
    console.log('🔍 DEBUG: Option Letter:', optionLetter);
    
    if (!sessionCode || !teamId) {
        console.error('❌ Missing session or team data');
        showGameNotification('⚠️ Session or team data missing. Please refresh the page.', 'error', 3000);
        return;
    }
    
    if (!optionId) {
        console.error('❌ Missing option ID');
        showGameNotification('⚠️ Option ID missing. Please try again.', 'error', 3000);
        return;
    }

    try {
        const response = await fetch(`/learn/api/constitution/${sessionCode}/answer/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken(),
            },
            body: `team_id=${teamId}&option_id=${optionId}`
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            playAudioCue('success');
            showGameNotification(`✅ Answer ${optionLetter} submitted!`, 'success', 2000);
            
            // DEBUG: Log the full response to see learning module data
            console.log('🔍 FULL API RESPONSE:', result);
            
            // Check for learning module data
            if (result.learning_module) {
                console.log('🔍 LEARNING MODULE FOUND:', result.learning_module);
                
                // Show learning module BEFORE page reload
                showLearningModule(result.learning_module);
                
                // Don't auto-reload - let user close modal manually
                // The modal close function will handle reloading
            } else {
                console.log('🔍 NO LEARNING MODULE in response');
                // Refresh page immediately to show next question
                setTimeout(() => window.location.reload(), 800);
            }
        } else {
            throw new Error(result.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Answer submission error:', error);
        playAudioCue('error');
        showGameNotification('❌ Failed to submit answer. Please try again.', 'error', 3000);
    }
}

// Leaderboard refresh
async function refreshLeaderboard() {
    const sessionCode = document.querySelector('[data-session-code]')?.getAttribute('data-session-code');
    if (!sessionCode) {
        throw new Error('Session code not found');
    }
    
    try {
        console.log(`🔄 Refreshing leaderboard for session: ${sessionCode}`);
        const response = await fetch(`/learn/api/constitution/${sessionCode}/leaderboard/`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📊 Leaderboard data received:', data);
        
        if (data.leaderboard && Array.isArray(data.leaderboard)) {
            updateLeaderboardDisplay(data.leaderboard);
            console.log(`✅ Leaderboard updated with ${data.leaderboard.length} teams`);
        } else {
            throw new Error('Invalid leaderboard data format');
        }
        
        return data;
    } catch (error) {
        console.error('Error refreshing leaderboard:', error);
        // Re-throw the error so it can be caught by the caller
        throw error;
    }
}

function updateLeaderboardDisplay(leaderboardData) {
    const container = document.getElementById('leaderboard-content');
    if (!container || !leaderboardData) {
        console.error('❌ Leaderboard container or data missing');
        return;
    }
    
    console.log(`📊 Updating leaderboard display with ${leaderboardData.length} teams`);
    
    // Hide loading state - try multiple possible loading element IDs
    const loading = document.getElementById('leaderboard-loading') || 
                   document.querySelector('#leaderboard-content .animate-pulse') ||
                   document.querySelector('.animate-pulse');
    if (loading) loading.classList.add('hidden');
    
    // Show actual leaderboard
    const actual = document.getElementById('actual-leaderboard');
    if (actual) actual.classList.remove('hidden');
    
    container.innerHTML = leaderboardData.map((team, index) => `
        <div class="flex items-center space-x-3 p-3 rounded-lg ${
            index === 0 ? 'bg-yellow-50 border border-yellow-200' : 
            index === 1 ? 'bg-gray-50 border border-gray-200' : 
            index === 2 ? 'bg-orange-50 border border-orange-200' : 'bg-white'
        } transition-colors duration-300">
            <div class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                index === 0 ? 'bg-yellow-500 text-white' :
                index === 1 ? 'bg-gray-400 text-white' :
                index === 2 ? 'bg-orange-500 text-white' : 'bg-blue-500 text-white'
            }">
                #${team.rank}
            </div>
            <div class="flex-1">
                <div class="font-semibold text-gray-800">${team.flag} ${team.team_name}</div>
                <div class="text-xs text-gray-500">${team.governance_level} ${team.governance_emoji}</div>
            </div>
            <div class="text-right">
                <div class="font-bold text-blue-600">${team.score}</div>
                <div class="text-xs text-gray-500">points</div>
            </div>
        </div>
    `).join('');
}

// Main answer selection function
function selectAnswer(optionId, optionLetter) {
    console.log(`🎯 Answer selected: ${optionLetter} (ID: ${optionId})`);
    playAudioCue('click');
    submitAnswerDirectly(optionId, optionLetter);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('📚 Constitution Challenge initialized');
    
    // Add keyboard shortcut for leaderboard (L key)
    document.addEventListener('keydown', function(event) {
        // Only trigger if not typing in an input field
        if (event.target.tagName !== 'INPUT' && event.target.tagName !== 'TEXTAREA') {
            if (event.key.toLowerCase() === 'l') {
                event.preventDefault();
                toggleLeaderboard();
            }
        }
    });
});

// Main initialization function for external calls
function initializeConstitutionChallenge() {
    console.log('🏛️ Constitution Challenge manually initialized');
    // All initialization logic is handled by the DOMContentLoaded event above
    return true;
}

// Enhanced Learning Module System
function showLearningModule(moduleData) {
    const modal = document.getElementById('learning-module-modal');
    
    if (!modal) {
        console.error('❌ Learning modal not found in DOM');
        return;
    }
    
    if (!moduleData) {
        console.error('❌ Learning module data not provided');
        return;
    }
    
    console.log('📚 Showing learning module:', moduleData.title || 'Untitled Module');
    
    // Get modal elements
    const titleEl = modal.querySelector('#learning-title') || modal.querySelector('h3');
    const loadingDiv = modal.querySelector('#learning-loading');
    const contentDiv = modal.querySelector('#learning-content');
    
    // Show modal
    modal.classList.remove('hidden');
    
    // Set title
    if (titleEl) {
        titleEl.textContent = moduleData.title || 'Constitutional Insight';
    }
    
    // Show loading state initially if elements exist
    if (loadingDiv) loadingDiv.classList.remove('hidden');
    if (contentDiv) contentDiv.classList.add('hidden');
    
    // Populate content after a brief delay for smooth transition
    setTimeout(() => {
        if (contentDiv) {
            populateLearningContent(moduleData);
            if (loadingDiv) loadingDiv.classList.add('hidden');
            contentDiv.classList.remove('hidden');
        }
    }, 500);
    
    // Add escape key listener
    document.addEventListener('keydown', handleLearningModalKeydown);
    
    playAudioCue('notification');
}

function populateLearningContent(moduleData) {
    const modal = document.getElementById('learning-module-modal');
    if (!modal) return;
    
    // Find the content elements within the modal using different possible IDs
    const explanationEl = modal.querySelector('#learning-explanation') || 
                         modal.querySelector('#principle-explanation') ||
                         modal.querySelector('.prose');
    
    const conceptTitleEl = modal.querySelector('#learning-concept-title');
    const conceptContentEl = modal.querySelector('#learning-concept-content');
    const impactEl = modal.querySelector('#learning-impact');
    
    // Populate main explanation
    if (explanationEl) {
        const content = moduleData.principle_explanation || 
                       moduleData.key_takeaways || 
                       'This constitutional decision helps shape your nation\'s governance framework and affects how citizens experience their rights and freedoms.';
        explanationEl.innerHTML = formatContentWithParagraphs(content);
    }
    
    // Populate key concept section
    if (conceptTitleEl && conceptContentEl) {
        conceptTitleEl.textContent = 'Key Constitutional Principle';
        const conceptContent = moduleData.key_takeaways || 
                              moduleData.principle_explanation || 
                              'Every constitutional decision has far-reaching consequences for your nation\'s future.';
        conceptContentEl.innerHTML = formatContentWithParagraphs(conceptContent);
    }
    
    // Populate impact section
    if (impactEl) {
        const impactText = moduleData.real_world_example || 
                          `Your choice affects various aspects of governance: citizen satisfaction, political stability, and long-term prosperity of your nation.`;
        impactEl.innerHTML = formatContentWithParagraphs(impactText);
    }
    
    // Handle optional historical context
    const historicalSection = modal.querySelector('#learning-historical-context');
    const historicalContent = modal.querySelector('#learning-historical-content');
    if (historicalSection && historicalContent && moduleData.historical_context && moduleData.historical_context.trim()) {
        historicalContent.innerHTML = formatContentWithParagraphs(moduleData.historical_context);
        historicalSection.classList.remove('hidden');
    } else if (historicalSection) {
        historicalSection.classList.add('hidden');
    }
    
    // Handle examples section
    const examplesSection = modal.querySelector('#learning-examples');
    const examplesContent = modal.querySelector('#learning-examples-content');
    if (examplesSection && examplesContent && moduleData.real_world_example && moduleData.real_world_example.trim()) {
        examplesContent.innerHTML = formatContentWithParagraphs(moduleData.real_world_example);
        examplesSection.classList.remove('hidden');
    } else if (examplesSection) {
        examplesSection.classList.add('hidden');
    }
    
    console.log('📚 Learning content populated with:', {
        explanation: explanationEl ? 'Found' : 'Not found',
        concept: conceptContentEl ? 'Found' : 'Not found',
        impact: impactEl ? 'Found' : 'Not found',
        moduleData: Object.keys(moduleData)
    });
}

function formatContentWithParagraphs(content) {
    if (!content) return '';
    return content.split('\n\n').map(paragraph => 
        paragraph.trim() ? `<p class="mb-3">${paragraph.trim()}</p>` : ''
    ).join('');
}

function formatBulletPoints(content) {
    if (!content) return '';
    
    // Split by bullet points and format as HTML list
    const points = content.split(/[•·\*\-]\s*/).filter(point => point.trim());
    
    if (points.length <= 1) {
        // If no clear bullet points, just format as paragraphs
        return formatContentWithParagraphs(content);
    }
    
    const listItems = points.map(point => 
        point.trim() ? `<li class="flex items-start mb-2">
            <svg class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
            </svg>
            <span>${point.trim()}</span>
        </li>` : ''
    ).join('');
    
    return `<ul class="space-y-1">${listItems}</ul>`;
}

function closeLearningModule(wasSkipped = false) {
    const modal = document.getElementById('learning-module-modal');
    
    if (!modal) {
        console.log('📚 Learning modal not found for closing');
        return;
    }
    
    // Simple hide without animation for now
    modal.classList.add('hidden');
    
    // Remove keyboard listener
    document.removeEventListener('keydown', handleLearningModalKeydown);
    
    // Hide keyboard hint
    const keyboardHint = document.getElementById('learning-keyboard-hint');
    if (keyboardHint) {
        keyboardHint.classList.add('hidden');
    }
    
    playAudioCue('click');
    
    // Track analytics if we have module data
    if (window.currentLearningModule && wasSkipped) {
        recordLearningModuleSkip(window.currentLearningModule.id);
    }
    
    console.log('📚 Learning module closed' + (wasSkipped ? ' (skipped)' : ''));
    
    // After user closes learning module, proceed to next question
    setTimeout(() => {
        console.log('🔄 Reloading page to show next question...');
        window.location.reload();
    }, 500);
}

function skipLearningModule() {
    closeLearningModule(true);
}

function handleLearningModalKeydown(event) {
    if (event.key === 'Escape') {
        event.preventDefault();
        closeLearningModule();
    }
}

async function recordLearningModuleSkip(moduleId) {
    try {
        const sessionCode = document.querySelector('[data-session-code]')?.getAttribute('data-session-code');
        if (!sessionCode || !moduleId) return;
        
        await fetch(`/learn/api/constitution/${sessionCode}/learning-module/${moduleId}/skip/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            }
        });
    } catch (error) {
        console.error('Failed to record learning module skip:', error);
    }
}

// Global exports
window.selectAnswer = selectAnswer;
window.toggleLeaderboard = toggleLeaderboard;
window.toggleHelp = toggleHelp;
window.showGameNotification = showGameNotification;
window.refreshLeaderboard = refreshLeaderboard;
window.showLearningModule = showLearningModule;
window.closeLearningModule = closeLearningModule;
window.skipLearningModule = skipLearningModule;
window.initializeConstitutionChallenge = initializeConstitutionChallenge;