/**
 * DecipherWorld Analytics Manager
 * Comprehensive MixPanel event tracking for user interactions and game analytics
 */

class DecipherWorldAnalytics {
    constructor() {
        this.userId = this.getOrCreateUserId();
        this.currentPage = window.location.pathname;
        this.referrer = document.referrer || 'direct';
        this.sessionStartTime = Date.now();
        
        // Initialize analytics when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Generate or retrieve anonymous user ID from cookies
     */
    getOrCreateUserId() {
        const cookieName = 'dw_user_id';
        let userId = this.getCookie(cookieName);
        
        if (!userId) {
            userId = 'anon_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
            this.setCookie(cookieName, userId, 365); // 1 year expiry
        }
        
        return userId;
    }

    /**
     * Cookie utility functions
     */
    setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    }

    getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    /**
     * Get standard event properties for all events
     */
    getBaseProperties() {
        return {
            user_id: this.userId,
            login_status: 'Not Logged In',
            page_from: this.getPreviousPage(),
            current_page: this.currentPage,
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent,
            screen_resolution: `${screen.width}x${screen.height}`,
            viewport_size: `${window.innerWidth}x${window.innerHeight}`,
            referrer: this.referrer,
            session_duration: Math.round((Date.now() - this.sessionStartTime) / 1000)
        };
    }

    /**
     * Get previous page from session storage
     */
    getPreviousPage() {
        return sessionStorage.getItem('dw_previous_page') || 'direct';
    }

    /**
     * Store current page as previous page for next navigation
     */
    storePreviousPage() {
        sessionStorage.setItem('dw_previous_page', this.currentPage);
    }

    /**
     * Initialize analytics tracking
     */
    init() {
        console.log('DecipherWorld Analytics initialized for user:', this.userId);
        
        // Identify user in MixPanel
        if (typeof mixpanel !== 'undefined') {
            mixpanel.identify(this.userId);
            mixpanel.register(this.getBaseProperties());
        }

        // Track page view
        this.trackPageView();
        
        // Set up interaction tracking
        this.setupInteractionTracking();
        
        // Set up form tracking
        this.setupFormTracking();
        
        // Set up game-specific tracking
        this.setupGameTracking();
        
        // Store current page for next navigation
        this.storePreviousPage();
    }

    /**
     * Track page view with enhanced properties
     */
    trackPageView() {
        const pageName = this.getPageName();
        const pageProperties = {
            ...this.getBaseProperties(),
            page_title: document.title,
            page_url: window.location.href,
            page_name: pageName,
            page_category: this.getPageCategory(),
            load_time: performance.now()
        };

        this.track(`Viewed ${pageName}`, pageProperties);
        console.log(`Page view tracked: Viewed ${pageName}`);
    }

    /**
     * Get human-readable page name
     */
    getPageName() {
        const path = window.location.pathname;
        const pageMap = {
            '/': 'Homepage',
            '/about/': 'About Us',
            '/teachers/': 'Teachers Hub',
            '/games/': 'Games Hub',
            '/games/ai-learning/': 'AI Learning Games',
            '/games/ai-learning/robotic-buddy/': 'Robotic Buddy Landing',
            '/games/ai-learning/simple-game/': 'Simple Game Landing',
            '/games/ai-learning/drag-drop-game/': 'Drag Drop Game Landing',
            '/games/group-learning/': 'Group Learning Games',
            '/games/group-learning/monsoon-mayhem/': 'Monsoon Mayhem Landing',
            '/games/cyber-security/': 'Cyber Security Games',
            '/games/financial-literacy/': 'Financial Literacy Games',
            '/games/constitution-basic/': 'Constitution Basic Games',
            '/games/constitution-advanced/': 'Constitution Advanced Games',
            '/games/entrepreneurship/': 'Entrepreneurship Games',
            '/learn/': 'Group Learning Platform',
            '/contact/': 'Contact Us'
        };

        // Check for exact matches first
        if (pageMap[path]) {
            return pageMap[path];
        }

        // Check for pattern matches
        if (path.includes('/learn/design-thinking/')) return 'Design Thinking Game';
        if (path.includes('/learn/climate/')) return 'Climate Game';
        if (path.includes('/buddy/')) return 'Robotic Buddy Game';
        if (path.includes('/robotic-buddy/')) return 'Robotic Buddy Activity';
        
        // Default fallback
        return 'Unknown Page';
    }

    /**
     * Get page category for grouping
     */
    getPageCategory() {
        const path = window.location.pathname;
        if (path.startsWith('/games/')) return 'Games';
        if (path.startsWith('/learn/')) return 'Learning Platform';
        if (path.startsWith('/teachers/')) return 'Teachers';
        if (path.startsWith('/buddy/') || path.startsWith('/robotic-buddy/')) return 'AI Games';
        return 'General';
    }

    /**
     * Set up click tracking for all interactive elements
     */
    setupInteractionTracking() {
        // Track all button clicks
        document.addEventListener('click', (event) => {
            const element = event.target.closest('button, a, .btn, [role="button"]');
            if (!element) return;

            const elementType = this.getElementType(element);
            const elementText = this.getElementText(element);
            const elementLocation = this.getElementLocation(element);

            const interactionProperties = {
                ...this.getBaseProperties(),
                element_type: elementType,
                element_text: elementText,
                element_location: elementLocation,
                element_class: element.className,
                element_id: element.id || 'no-id',
                click_coordinates: `${event.clientX},${event.clientY}`
            };

            this.track(`Interacted ${elementType}`, interactionProperties);
            console.log(`Interaction tracked: ${elementType} - ${elementText}`);
        });
    }

    /**
     * Get element type for interaction tracking
     */
    getElementType(element) {
        if (element.tagName === 'A') return 'Link';
        if (element.tagName === 'BUTTON' || element.type === 'submit') return 'Button';
        if (element.classList.contains('btn')) return 'Button';
        if (element.role === 'button') return 'Button';
        return 'Element';
    }

    /**
     * Get readable text from element
     */
    getElementText(element) {
        // Get text content, but limit length and clean it up
        let text = element.textContent || element.innerText || element.alt || element.title || '';
        text = text.trim().replace(/\s+/g, ' ').substring(0, 100);
        return text || 'No Text';
    }

    /**
     * Get element location context
     */
    getElementLocation(element) {
        // Try to determine where on the page the element is
        if (element.closest('nav')) return 'Navigation';
        if (element.closest('header')) return 'Header';
        if (element.closest('footer')) return 'Footer';
        if (element.closest('.hero')) return 'Hero Section';
        if (element.closest('form')) return 'Form';
        if (element.closest('.game-interface')) return 'Game Interface';
        return 'Main Content';
    }

    /**
     * Set up form tracking
     */
    setupFormTracking() {
        // Track form views
        document.querySelectorAll('form').forEach(form => {
            const formName = this.getFormName(form);
            this.track('Form Viewed', {
                ...this.getBaseProperties(),
                form_name: formName,
                form_id: form.id || 'no-id'
            });
        });

        // Track form submissions
        document.addEventListener('submit', (event) => {
            const form = event.target;
            const formName = this.getFormName(form);
            
            this.track('Form Submitted', {
                ...this.getBaseProperties(),
                form_name: formName,
                form_id: form.id || 'no-id',
                form_method: form.method || 'GET',
                form_action: form.action || window.location.href
            });
            
            console.log(`Form submission tracked: ${formName}`);
        });
    }

    /**
     * Get form name for tracking
     */
    getFormName(form) {
        if (form.id) return form.id;
        if (form.name) return form.name;
        if (form.className.includes('contact')) return 'Contact Form';
        if (form.className.includes('teacher')) return 'Teacher Form';
        if (form.className.includes('game')) return 'Game Form';
        return 'Unknown Form';
    }

    /**
     * Set up game-specific tracking
     */
    setupGameTracking() {
        // Track game starts (look for game initialization)
        this.trackGameEvents();
        
        // Track game progression
        this.trackGameProgression();
    }

    /**
     * Track game-related events
     */
    trackGameEvents() {
        // Monitor for game start indicators
        const gameStartSelectors = [
            '[data-game="start"]',
            '.start-game',
            '.play-game',
            '.create-buddy'
        ];

        gameStartSelectors.forEach(selector => {
            document.addEventListener('click', (event) => {
                if (event.target.matches(selector) || event.target.closest(selector)) {
                    const gameType = this.detectGameType();
                    this.track('Game Started', {
                        ...this.getBaseProperties(),
                        game_type: gameType,
                        game_page: this.getPageName()
                    });
                }
            });
        });
    }

    /**
     * Track game progression milestones
     */
    trackGameProgression() {
        // This will be expanded based on specific game implementations
        // For now, track when users spend significant time on game pages
        if (this.isGamePage()) {
            setTimeout(() => {
                this.track('Game Engagement', {
                    ...this.getBaseProperties(),
                    engagement_duration: 30,
                    game_type: this.detectGameType()
                });
            }, 30000); // Track after 30 seconds on game page
        }
    }

    /**
     * Check if current page is a game page
     */
    isGamePage() {
        const path = window.location.pathname;
        return path.includes('/learn/') || 
               path.includes('/buddy/') || 
               path.includes('/robotic-buddy/') ||
               path.includes('/games/');
    }

    /**
     * Detect game type from current page
     */
    detectGameType() {
        const path = window.location.pathname;
        if (path.includes('design-thinking')) return 'Design Thinking';
        if (path.includes('climate') || path.includes('monsoon')) return 'Climate Game';
        if (path.includes('buddy') || path.includes('robotic')) return 'AI Learning';
        if (path.includes('cyber-security')) return 'Cyber Security';
        if (path.includes('constitution')) return 'Constitution';
        if (path.includes('financial')) return 'Financial Literacy';
        if (path.includes('entrepreneurship')) return 'Entrepreneurship';
        return 'Unknown Game';
    }

    /**
     * Main tracking method - wrapper around MixPanel
     */
    track(eventName, properties = {}) {
        if (typeof mixpanel !== 'undefined') {
            mixpanel.track(eventName, properties);
        } else {
            console.warn('MixPanel not available, event logged:', eventName, properties);
        }
    }

    /**
     * Public API methods for manual tracking
     */
    
    // Track custom game events
    trackGameEvent(action, gameType, additionalProperties = {}) {
        this.track(`Game ${action}`, {
            ...this.getBaseProperties(),
            game_type: gameType,
            ...additionalProperties
        });
    }

    // Track achievements
    trackAchievement(achievementName, gameType, additionalProperties = {}) {
        this.track('Achievement Unlocked', {
            ...this.getBaseProperties(),
            achievement: achievementName,
            game_type: gameType,
            ...additionalProperties
        });
    }

    // Track errors
    trackError(errorType, errorMessage, additionalProperties = {}) {
        this.track('Error Occurred', {
            ...this.getBaseProperties(),
            error_type: errorType,
            error_message: errorMessage,
            ...additionalProperties
        });
    }
}

// Initialize analytics
window.dwAnalytics = new DecipherWorldAnalytics();

// Global error tracking
window.addEventListener('error', (event) => {
    if (window.dwAnalytics) {
        window.dwAnalytics.trackError('JavaScript Error', event.error?.message || 'Unknown error', {
            filename: event.filename,
            line_number: event.lineno,
            column_number: event.colno
        });
    }
});

// Track page unload for session duration
window.addEventListener('beforeunload', () => {
    if (window.dwAnalytics) {
        window.dwAnalytics.track('Page Unloaded', {
            ...window.dwAnalytics.getBaseProperties(),
            time_on_page: Math.round((Date.now() - window.dwAnalytics.sessionStartTime) / 1000)
        });
    }
});

console.log('DecipherWorld Analytics loaded successfully');