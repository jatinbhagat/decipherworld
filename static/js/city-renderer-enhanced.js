/**
 * Enhanced SVG City Renderer with GSAP Animations
 * Professional-grade immersive cityscape for Constitution Challenge
 */

class EnhancedCityRenderer extends CityRenderer {
    constructor(containerId, options = {}) {
        super(containerId, options);
        this.gsapTimelines = new Map();
        this.eventListeners = [];
        this.animationFrames = [];
        this.timeouts = [];
        this.intervals = [];
        this.observerTargets = new Set();
        
        // Bind methods to avoid memory leaks
        this.handleResize = this.handleResize.bind(this);
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
        
        // Set up automatic cleanup listeners
        this.setupCleanupListeners();
        
        console.log('🎬 Enhanced City Renderer with GSAP initialized');
    }
    
    // Override parent animations with GSAP-powered versions
    createAnimation(animName) {
        switch (animName) {
            case 'construction':
                return this.animateConstructionGSAP();
            case 'fireworks':
                return this.animateFireworksGSAP();
            case 'parade':
                return this.animateParadeGSAP();
            case 'building_complete':
                return this.animateBuildingCompleteGSAP();
            case 'celebration':
                return this.animateCelebrationGSAP();
            default:
                return super.createAnimation(animName);
        }
    }
    
    // GSAP-Powered Professional Animations
    animateConstructionGSAP() {
        const buildings = this.layers.buildings.querySelectorAll('.under-construction');
        const tl = this.createTimeline('construction');
        
        if (!tl) return { stop: () => {} };
        
        buildings.forEach((building, index) => {
            // Construction dust particles
            this.createConstructionDust(building);
            
            // Building grow animation with elastic bounce
            tl.fromTo(building, {
                scaleX: 0.3,
                scaleY: 0.1,
                opacity: 0.5,
                transformOrigin: "center bottom"
            }, {
                scaleX: 1,
                scaleY: 1,
                opacity: 1,
                duration: 1.5,
                ease: "elastic.out(1, 0.3)",
                onComplete: () => {
                    building.classList.remove('under-construction');
                    building.classList.add('construction-complete');
                    this.createCompletionCelebration(building);
                }
            }, index * 0.3);
            
            console.log('🔊 Construction completed for building');
        });
        
        this.gsapTimelines.push(tl);
        return { stop: () => tl.kill() };
    }
    
    animateFireworksGSAP() {
        const tl = gsap.timeline();
        
        // Create multiple firework bursts with professional timing
        for (let i = 0; i < 8; i++) {
            const x = 100 + Math.random() * (this.width - 200);
            const y = 30 + Math.random() * 60;
            const color = `hsl(${Math.random() * 360}, 80%, 60%)`;
            
            this.createProfessionalFirework(x, y, color, tl, i * 0.2);
        }
        
        this.gsapTimelines.push(tl);
        return { stop: () => tl.kill() };
    }
    
    animateParadeGSAP() {
        const citizensLayer = this.layers.citizens;
        const tl = gsap.timeline();
        
        // Create enhanced parade with multiple elements
        const parade = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        parade.innerHTML = `
            <g class="parade-float">
                <rect x="-15" y="-8" width="50" height="15" fill="#FFD700" rx="8"/>
                <circle cx="0" cy="-3" r="5" fill="#FF5722"/>
                <circle cx="12" cy="-3" r="5" fill="#4CAF50"/>
                <circle cx="24" cy="-3" r="5" fill="#2196F3"/>
                <text x="12" y="-20" text-anchor="middle" font-size="14">🎪</text>
                <text x="6" y="2" text-anchor="middle" font-size="10">🎉</text>
                <text x="18" y="2" text-anchor="middle" font-size="10">🎊</text>
            </g>
        `;
        
        citizensLayer.appendChild(parade);
        
        // Professional parade animation with physics
        tl.fromTo(parade, {
            x: -80,
            y: this.height - 80
        }, {
            x: this.width + 80,
            duration: 6,
            ease: "power1.inOut",
            onComplete: () => {
                if (parade.parentNode) {
                    citizensLayer.removeChild(parade);
                }
            }
        });
        
        // Add realistic bouncing motion
        tl.to(parade, {
            y: this.height - 85,
            duration: 0.4,
            ease: "power2.inOut",
            repeat: -1,
            yoyo: true
        }, 0);
        
        // Create professional confetti trail
        this.createAdvancedConfettiTrail(parade, tl);
        
        this.gsapTimelines.push(tl);
        return { stop: () => tl.kill() };
    }
    
    animateBuildingCompleteGSAP() {
        const buildings = this.layers.buildings.querySelectorAll('.construction-complete');
        const tl = gsap.timeline();
        
        buildings.forEach((building, index) => {
            // Professional building completion sequence
            tl.to(building, {
                scale: 1.15,
                duration: 0.3,
                ease: "back.out(1.7)"
            }, index * 0.1)
            .to(building, {
                scale: 1,
                duration: 0.4,
                ease: "elastic.out(1, 0.5)"
            })
            .call(() => this.createProfessionalSparkles(building), null, index * 0.1);
        });
        
        this.gsapTimelines.push(tl);
        return { stop: () => tl.kill() };
    }
    
    animateCelebrationGSAP() {
        const effectsLayer = this.layers.effects;
        const tl = gsap.timeline();
        
        // Create celebration text with advanced typography animation
        const celebText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        celebText.setAttribute('x', this.width / 2);
        celebText.setAttribute('y', this.height / 2);
        celebText.setAttribute('text-anchor', 'middle');
        celebText.setAttribute('font-size', '28');
        celebText.setAttribute('font-weight', 'bold');
        celebText.setAttribute('fill', '#FFD700');
        celebText.setAttribute('stroke', '#FF6B35');
        celebText.setAttribute('stroke-width', '1');
        celebText.textContent = '🎉 DEMOCRACY ACHIEVED! 🎉';
        
        effectsLayer.appendChild(celebText);
        
        // Professional text animation sequence
        tl.fromTo(celebText, {
            scale: 0,
            rotation: -180,
            opacity: 0
        }, {
            scale: 1.3,
            rotation: 0,
            opacity: 1,
            duration: 1,
            ease: "back.out(2)"
        })
        .to(celebText, {
            scale: 1,
            duration: 0.5,
            ease: "power2.out"
        })
        .to(celebText, {
            y: this.height / 2 - 30,
            opacity: 0,
            duration: 1.5,
            ease: "power2.out",
            onComplete: () => effectsLayer.removeChild(celebText)
        }, "+=2");
        
        // Add cascading celebration particles
        this.createCascadingCelebration(tl);
        
        this.gsapTimelines.push(tl);
        return { stop: () => tl.kill() };
    }
    
    // Advanced Effect Creation Methods
    createProfessionalFirework(x, y, color, timeline, delay) {
        const effectsLayer = this.layers.effects;
        
        // Main burst with advanced physics
        const burst = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        burst.setAttribute('cx', x);
        burst.setAttribute('cy', y);
        burst.setAttribute('r', '0');
        burst.setAttribute('fill', color);
        burst.setAttribute('opacity', '1');
        effectsLayer.appendChild(burst);
        
        // Create multiple sparkle layers
        const sparkles = [];
        const sparkleCount = 12;
        
        for (let i = 0; i < sparkleCount; i++) {
            const sparkle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            sparkle.setAttribute('cx', x);
            sparkle.setAttribute('cy', y);
            sparkle.setAttribute('r', '2');
            sparkle.setAttribute('fill', color);
            sparkle.setAttribute('opacity', '0.9');
            effectsLayer.appendChild(sparkle);
            sparkles.push(sparkle);
        }
        
        // Professional burst animation
        timeline.to(burst, {
            attr: { r: 30 },
            opacity: 0,
            duration: 1.4,
            ease: "power3.out",
            onComplete: () => effectsLayer.removeChild(burst)
        }, delay);
        
        // Advanced sparkle physics
        sparkles.forEach((sparkle, index) => {
            const angle = (index / sparkleCount) * Math.PI * 2;
            const distance = 45 + Math.random() * 25;
            const endX = x + Math.cos(angle) * distance;
            const endY = y + Math.sin(angle) * distance;
            
            timeline.to(sparkle, {
                attr: { cx: endX, cy: endY, r: 0 },
                opacity: 0,
                duration: 1.8,
                ease: "power2.out",
                onComplete: () => effectsLayer.removeChild(sparkle)
            }, delay + 0.1);
        });
        
        // Add secondary explosion
        setTimeout(() => {
            this.createSecondaryExplosion(x, y, color);
        }, (delay + 0.8) * 1000);
    }
    
    createAdvancedConfettiTrail(parade, timeline) {
        const effectsLayer = this.layers.effects;
        
        // Professional confetti system
        const confettiInterval = setInterval(() => {
            if (!parade.parentNode) {
                clearInterval(confettiInterval);
                return;
            }
            
            // Get parade position
            const transform = parade.getAttribute('transform') || 'translate(0,0)';
            const match = transform.match(/translate\(([^,]+),([^)]+)\)/);
            const paradeX = match ? parseFloat(match[1]) : 0;
            const paradeY = match ? parseFloat(match[2]) : this.height - 80;
            
            // Create multiple confetti types
            for (let i = 0; i < 5; i++) {
                this.createSingleConfetti(paradeX + Math.random() * 60 - 30, paradeY - 20);
            }
        }, 150);
        
        timeline.call(() => clearInterval(confettiInterval), null, 6);
    }
    
    createSingleConfetti(x, y) {
        const effectsLayer = this.layers.effects;
        const shapes = ['rect', 'circle', 'polygon'];
        const shape = shapes[Math.floor(Math.random() * shapes.length)];
        
        let confetti;
        const color = `hsl(${Math.random() * 360}, 70%, 60%)`;
        
        if (shape === 'rect') {
            confetti = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            confetti.setAttribute('width', '4');
            confetti.setAttribute('height', '4');
            confetti.setAttribute('rx', '1');
        } else if (shape === 'circle') {
            confetti = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            confetti.setAttribute('r', '2');
        } else {
            confetti = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            confetti.setAttribute('points', '0,-3 2,0 0,3 -2,0');
        }
        
        confetti.setAttribute('fill', color);
        confetti.setAttribute('opacity', '0.9');
        
        if (shape === 'rect' || shape === 'polygon') {
            confetti.setAttribute('transform', `translate(${x}, ${y})`);
        } else {
            confetti.setAttribute('cx', x);
            confetti.setAttribute('cy', y);
        }
        
        effectsLayer.appendChild(confetti);
        
        // Advanced confetti physics
        gsap.to(confetti, {
            y: this.height + 20,
            x: x + (Math.random() - 0.5) * 60,
            rotation: Math.random() * 720,
            opacity: 0,
            duration: 2.5 + Math.random() * 2,
            ease: "power2.in",
            onComplete: () => effectsLayer.removeChild(confetti)
        });
    }
    
    createSecondaryExplosion(x, y, baseColor) {
        const effectsLayer = this.layers.effects;
        
        // Create secondary burst
        for (let i = 0; i < 6; i++) {
            const particle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            particle.setAttribute('cx', x);
            particle.setAttribute('cy', y);
            particle.setAttribute('r', '1');
            particle.setAttribute('fill', baseColor);
            particle.setAttribute('opacity', '0.7');
            
            effectsLayer.appendChild(particle);
            
            const angle = (i / 6) * Math.PI * 2;
            const distance = 15 + Math.random() * 10;
            
            gsap.to(particle, {
                attr: {
                    cx: x + Math.cos(angle) * distance,
                    cy: y + Math.sin(angle) * distance,
                    r: 0
                },
                opacity: 0,
                duration: 0.8,
                ease: "power2.out",
                onComplete: () => effectsLayer.removeChild(particle)
            });
        }
    }
    
    createConstructionDust(building) {
        const effectsLayer = this.layers.effects;
        const bbox = building.getBBox();
        const x = bbox.x + bbox.width / 2;
        const y = bbox.y + bbox.height;
        
        // Professional dust particle system
        for (let i = 0; i < 8; i++) {
            const dust = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            dust.setAttribute('cx', x + (Math.random() - 0.5) * 30);
            dust.setAttribute('cy', y);
            dust.setAttribute('r', '2');
            dust.setAttribute('fill', '#D4B896');
            dust.setAttribute('opacity', '0.6');
            
            effectsLayer.appendChild(dust);
            
            gsap.to(dust, {
                y: y + 25,
                x: x + (Math.random() - 0.5) * 50,
                opacity: 0,
                duration: 2,
                ease: "power2.out",
                onComplete: () => effectsLayer.removeChild(dust)
            });
        }
    }
    
    createCompletionCelebration(building) {
        const effectsLayer = this.layers.effects;
        const bbox = building.getBBox();
        const x = bbox.x + bbox.width / 2;
        const y = bbox.y + bbox.height / 2;
        
        // Professional completion effect
        const burst = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        burst.setAttribute('cx', x);
        burst.setAttribute('cy', y);
        burst.setAttribute('r', '0');
        burst.setAttribute('fill', '#FFD700');
        burst.setAttribute('opacity', '0.8');
        burst.setAttribute('stroke', '#FF6B35');
        burst.setAttribute('stroke-width', '2');
        
        effectsLayer.appendChild(burst);
        
        gsap.timeline()
            .to(burst, {
                attr: { r: 35 },
                opacity: 0,
                duration: 1.2,
                ease: "power3.out",
                onComplete: () => effectsLayer.removeChild(burst)
            })
            .call(() => this.createSuccessRipple(x, y), null, 0.3);
    }
    
    createSuccessRipple(x, y) {
        const effectsLayer = this.layers.effects;
        
        for (let i = 0; i < 3; i++) {
            const ripple = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            ripple.setAttribute('cx', x);
            ripple.setAttribute('cy', y);
            ripple.setAttribute('r', '5');
            ripple.setAttribute('fill', 'none');
            ripple.setAttribute('stroke', '#4CAF50');
            ripple.setAttribute('stroke-width', '3');
            ripple.setAttribute('opacity', '0.8');
            
            effectsLayer.appendChild(ripple);
            
            gsap.to(ripple, {
                attr: { r: 50 + i * 10 },
                opacity: 0,
                duration: 1.5,
                ease: "power2.out",
                delay: i * 0.2,
                onComplete: () => effectsLayer.removeChild(ripple)
            });
        }
    }
    
    createProfessionalSparkles(building) {
        const effectsLayer = this.layers.effects;
        const bbox = building.getBBox();
        const x = bbox.x + bbox.width / 2;
        const y = bbox.y + bbox.height / 2;
        
        // Create professional sparkle system
        for (let i = 0; i < 12; i++) {
            const sparkle = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            sparkle.setAttribute('points', '0,-4 1,-1 4,0 1,1 0,4 -1,1 -4,0 -1,-1');
            sparkle.setAttribute('fill', '#FFD700');
            sparkle.setAttribute('opacity', '0.9');
            sparkle.setAttribute('transform', `translate(${x}, ${y})`);
            
            effectsLayer.appendChild(sparkle);
            
            const angle = (i / 12) * Math.PI * 2;
            const distance = 25 + Math.random() * 20;
            const endX = x + Math.cos(angle) * distance;
            const endY = y + Math.sin(angle) * distance;
            
            gsap.timeline()
                .to(sparkle, {
                    x: endX - x,
                    y: endY - y,
                    rotation: 360,
                    opacity: 0,
                    duration: 1.5,
                    ease: "power2.out",
                    delay: Math.random() * 0.5,
                    onComplete: () => effectsLayer.removeChild(sparkle)
                });
        }
    }
    
    createCascadingCelebration(timeline) {
        const effectsLayer = this.layers.effects;
        
        // Create cascading celebration particles
        for (let wave = 0; wave < 3; wave++) {
            for (let i = 0; i < 15; i++) {
                const particle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                particle.setAttribute('cx', Math.random() * this.width);
                particle.setAttribute('cy', this.height + 20);
                particle.setAttribute('r', '3');
                particle.setAttribute('fill', `hsl(${Math.random() * 60 + 30}, 80%, 65%)`);
                particle.setAttribute('opacity', '0.9');
                
                effectsLayer.appendChild(particle);
                
                timeline.to(particle, {
                    y: -30,
                    x: `+=${(Math.random() - 0.5) * 100}`,
                    rotation: Math.random() * 360,
                    opacity: 0,
                    duration: 3 + wave * 0.5,
                    ease: "power1.out",
                    delay: wave * 0.5 + Math.random() * 0.3,
                    onComplete: () => effectsLayer.removeChild(particle)
                });
            }
        }
    }
    
    // Enhanced Interactive Features
    makeFullyInteractive() {
        super.makeInteractive?.() || this.makeInteractive();
        
        // Add advanced gesture support
        this.addGestureSupport();
        
        // Add keyboard navigation
        this.addKeyboardSupport();
        
        console.log('🖱️ City made fully interactive with gestures and keyboard');
    }
    
    addGestureSupport() {
        let isZooming = false;
        let startDistance = 0;
        let startScale = 1;
        
        this.svg.addEventListener('touchstart', (e) => {
            if (e.touches.length === 2) {
                isZooming = true;
                const dx = e.touches[0].clientX - e.touches[1].clientX;
                const dy = e.touches[0].clientY - e.touches[1].clientY;
                startDistance = Math.sqrt(dx * dx + dy * dy);
            }
        });
        
        this.svg.addEventListener('touchmove', (e) => {
            if (isZooming && e.touches.length === 2) {
                e.preventDefault();
                const dx = e.touches[0].clientX - e.touches[1].clientX;
                const dy = e.touches[0].clientY - e.touches[1].clientY;
                const currentDistance = Math.sqrt(dx * dx + dy * dy);
                const scale = (currentDistance / startDistance) * startScale;
                
                gsap.to(this.svg, {
                    scale: Math.max(0.5, Math.min(2, scale)),
                    duration: 0.1,
                    ease: "none"
                });
            }
        });
        
        this.svg.addEventListener('touchend', () => {
            isZooming = false;
        });
    }
    
    addKeyboardSupport() {
        document.addEventListener('keydown', (e) => {
            switch (e.key) {
                case 'f':
                    this.startAnimations(['fireworks']);
                    break;
                case 'p':
                    this.startAnimations(['parade']);
                    break;
                case 'c':
                    this.startAnimations(['celebration']);
                    break;
                case 'r':
                    this.render(this.lastVisualElements);
                    break;
            }
        });
    }
    
    // Enhanced render with caching
    render(visualElements) {
        this.lastVisualElements = visualElements;
        super.render(visualElements);
        
        // Add professional post-processing effects
        setTimeout(() => {
            this.addPostProcessingEffects();
        }, 500);
    }
    
    addPostProcessingEffects() {
        // Add ambient lighting effect
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        filter.setAttribute('id', 'ambient-lighting');
        filter.innerHTML = `
            <feGaussianBlur in="SourceGraphic" stdDeviation="1" result="blur"/>
            <feColorMatrix in="blur" type="matrix" values="1 0 0 0 0.1  0 1 0 0 0.1  0 0 1 0 0.1  0 0 0 1 0"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
        `;
        
        const defs = this.svg.querySelector('defs') || document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        if (!this.svg.querySelector('defs')) {
            this.svg.appendChild(defs);
        }
        defs.appendChild(filter);
        
        // Apply ambient lighting to city elements
        this.layers.buildings.style.filter = 'url(#ambient-lighting)';
    }
    
    // Add clickable building interactions
    addBuildingInteractions() {
        const buildings = this.layers.buildings.querySelectorAll('.building, [class*="building-"]');
        
        buildings.forEach(building => {
            building.classList.add('interactive-element');
            building.style.cursor = 'pointer';
            
            // Add click handler for building info
            building.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showBuildingInfo(building);
            });
            
            // Add hover effects with GSAP
            building.addEventListener('mouseenter', () => {
                gsap.to(building, {
                    scale: 1.05,
                    duration: 0.3,
                    ease: "power2.out",
                    filter: "brightness(1.2) drop-shadow(0 4px 12px rgba(255, 193, 7, 0.4))"
                });
            });
            
            building.addEventListener('mouseleave', () => {
                gsap.to(building, {
                    scale: 1,
                    duration: 0.3,
                    ease: "power2.out",
                    filter: "brightness(1) drop-shadow(none)"
                });
            });
        });
        
        console.log(`🏠 Made ${buildings.length} buildings interactive`);
    }
    
    // Show building information tooltip
    showBuildingInfo(building) {
        const buildingType = this.getBuildingType(building);
        const info = this.getBuildingDescription(buildingType);
        
        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'building-tooltip fixed bg-white rounded-lg shadow-xl p-4 z-50 max-w-xs';
        tooltip.innerHTML = `
            <div class="flex items-center mb-2">
                <div class="text-2xl mr-2">${info.icon}</div>
                <h3 class="font-bold text-gray-800">${info.name}</h3>
            </div>
            <p class="text-sm text-gray-600 mb-2">${info.description}</p>
            <div class="text-xs text-blue-600">${info.impact}</div>
        `;
        
        // Position tooltip
        const rect = building.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.style.top = `${rect.top - 10}px`;
        tooltip.style.transform = 'translateX(-50%) translateY(-100%)';
        
        document.body.appendChild(tooltip);
        
        // Animate tooltip appearance
        gsap.fromTo(tooltip, {
            opacity: 0,
            scale: 0.8,
            y: 20
        }, {
            opacity: 1,
            scale: 1,
            y: 0,
            duration: 0.3,
            ease: "back.out(1.7)"
        });
        
        // Auto-remove tooltip after 3 seconds
        setTimeout(() => {
            gsap.to(tooltip, {
                opacity: 0,
                scale: 0.8,
                y: -20,
                duration: 0.2,
                ease: "power2.in",
                onComplete: () => {
                    if (document.body.contains(tooltip)) {
                        document.body.removeChild(tooltip);
                    }
                }
            });
        }, 3000);
        
        // Remove tooltip on click outside
        const removeTooltip = (e) => {
            if (!tooltip.contains(e.target) && !building.contains(e.target)) {
                gsap.to(tooltip, {
                    opacity: 0,
                    scale: 0.8,
                    duration: 0.2,
                    onComplete: () => {
                        if (document.body.contains(tooltip)) {
                            document.body.removeChild(tooltip);
                        }
                    }
                });
                document.removeEventListener('click', removeTooltip);
            }
        };
        
        setTimeout(() => {
            document.addEventListener('click', removeTooltip);
        }, 100);
    }
    
    // Get building type from element classes
    getBuildingType(building) {
        const classes = building.className.baseVal || building.className;
        
        if (classes.includes('residential')) return 'residential';
        if (classes.includes('civic')) return 'civic';
        if (classes.includes('commercial')) return 'commercial';
        if (classes.includes('school')) return 'school';
        if (classes.includes('courthouse')) return 'courthouse';
        if (classes.includes('parliament')) return 'parliament';
        if (classes.includes('hospital')) return 'hospital';
        if (classes.includes('market')) return 'market';
        
        return 'building';
    }
    
    // Get building information
    getBuildingDescription(type) {
        const descriptions = {
            residential: {
                name: 'Residential Area',
                icon: '🏠',
                description: 'Homes where citizens live and raise their families.',
                impact: 'Provides housing security and community stability'
            },
            civic: {
                name: 'Civic Building',
                icon: '🏛️',
                description: 'Government buildings that serve the public.',
                impact: 'Strengthens democratic institutions and governance'
            },
            commercial: {
                name: 'Commercial District',
                icon: '🏬',
                description: 'Businesses and shops that drive the economy.',
                impact: 'Boosts economic prosperity and job creation'
            },
            school: {
                name: 'Educational Institution',
                icon: '🏫',
                description: 'Schools that educate the next generation.',
                impact: 'Increases literacy and democratic participation'
            },
            courthouse: {
                name: 'Courthouse',
                icon: '⚖️',
                description: 'Courts that uphold justice and the rule of law.',
                impact: 'Ensures fair trials and constitutional rights'
            },
            parliament: {
                name: 'Parliament Building',
                icon: '🏛️',
                description: 'Legislature where laws are debated and passed.',
                impact: 'Central to democratic governance and representation'
            },
            hospital: {
                name: 'Healthcare Facility',
                icon: '🏥',
                description: 'Medical facilities that care for citizens.',
                impact: 'Improves public health and quality of life'
            },
            market: {
                name: 'Marketplace',
                icon: '🏪',
                description: 'Trading centers for goods and services.',
                impact: 'Facilitates commerce and economic growth'
            },
            building: {
                name: 'City Building',
                icon: '🏢',
                description: 'An important part of your growing nation.',
                impact: 'Contributes to overall development and prosperity'
            }
        };
        
        return descriptions[type] || descriptions.building;
    }
    
    // Enhanced render with building interactions
    render(visualElements) {
        this.lastVisualElements = visualElements;
        super.render(visualElements);
        
        // Add building interactions after rendering
        setTimeout(() => {
            this.addBuildingInteractions();
            this.addPostProcessingEffects();
        }, 500);
    }

    // Set up automatic cleanup listeners
    setupCleanupListeners() {
        // Handle window resize
        this.addEventListener(window, 'resize', this.handleResize);
        
        // Handle page visibility changes (cleanup when hidden)
        this.addEventListener(document, 'visibilitychange', this.handleVisibilityChange);
        
        // Handle page unload
        this.addEventListener(window, 'beforeunload', () => this.destroy());
    }
    
    // Safe event listener helper that tracks listeners for cleanup
    addEventListener(target, type, listener, options) {
        target.addEventListener(type, listener, options);
        this.eventListeners.push({ target, type, listener, options });
    }
    
    // Safe timeout helper
    setTimeout(callback, delay) {
        const id = setTimeout(() => {
            callback();
            this.timeouts = this.timeouts.filter(t => t !== id);
        }, delay);
        this.timeouts.push(id);
        return id;
    }
    
    // Safe interval helper
    setInterval(callback, delay) {
        const id = setInterval(callback, delay);
        this.intervals.push(id);
        return id;
    }
    
    // Safe animation frame helper
    requestAnimationFrame(callback) {
        const id = requestAnimationFrame(() => {
            callback();
            this.animationFrames = this.animationFrames.filter(f => f !== id);
        });
        this.animationFrames.push(id);
        return id;
    }
    
    // Handle resize events
    handleResize() {
        // Throttled resize handling
        if (this.resizeTimeout) return;
        
        this.resizeTimeout = this.setTimeout(() => {
            if (this.svg && this.container) {
                const rect = this.container.getBoundingClientRect();
                this.svg.setAttribute('width', rect.width);
                this.svg.setAttribute('height', rect.height);
            }
            this.resizeTimeout = null;
        }, 250);
    }
    
    // Handle visibility changes
    handleVisibilityChange() {
        if (document.hidden) {
            // Pause animations when page is hidden
            this.pauseAnimations();
        } else {
            // Resume animations when page becomes visible
            this.resumeAnimations();
        }
    }
    
    // Pause all running animations
    pauseAnimations() {
        this.gsapTimelines.forEach((timeline, key) => {
            if (timeline && timeline.pause) {
                timeline.pause();
            }
        });
    }
    
    // Resume all paused animations
    resumeAnimations() {
        this.gsapTimelines.forEach((timeline, key) => {
            if (timeline && timeline.resume) {
                timeline.resume();
            }
        });
    }
    
    // Enhanced timeline management
    createTimeline(key) {
        // Kill existing timeline with same key
        if (this.gsapTimelines.has(key)) {
            const existingTimeline = this.gsapTimelines.get(key);
            if (existingTimeline && existingTimeline.kill) {
                existingTimeline.kill();
            }
        }
        
        if (typeof gsap !== 'undefined') {
            const timeline = gsap.timeline({
                onComplete: () => {
                    // Auto-cleanup completed timelines
                    this.gsapTimelines.delete(key);
                }
            });
            
            this.gsapTimelines.set(key, timeline);
            return timeline;
        }
        
        return null;
    }
    
    // Clean up observer targets
    cleanupObservers() {
        this.observerTargets.forEach(observer => {
            if (observer && observer.disconnect) {
                observer.disconnect();
            }
        });
        this.observerTargets.clear();
    }
    
    // Comprehensive cleanup
    destroy() {
        // Clean up GSAP timelines
        this.gsapTimelines.forEach((timeline, key) => {
            if (timeline && timeline.kill) {
                timeline.kill();
            }
        });
        this.gsapTimelines.clear();
        
        // Clean up event listeners
        this.eventListeners.forEach(({ target, type, listener, options }) => {
            target.removeEventListener(type, listener, options);
        });
        this.eventListeners = [];
        
        // Clear timeouts
        this.timeouts.forEach(id => clearTimeout(id));
        this.timeouts = [];
        
        // Clear intervals
        this.intervals.forEach(id => clearInterval(id));
        this.intervals = [];
        
        // Cancel animation frames
        this.animationFrames.forEach(id => cancelAnimationFrame(id));
        this.animationFrames = [];
        
        // Clean up observers
        this.cleanupObservers();
        
        // Clear resize timeout
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }
        
        // Call parent destroy
        super.destroy();
        
        console.log('🎬 Enhanced City Renderer destroyed with full cleanup');
    }
}

// Export enhanced renderer
window.CityRenderer = EnhancedCityRenderer;