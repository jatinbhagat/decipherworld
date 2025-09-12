/**
 * SVG City Renderer - Layered City Canvas System
 * Creates immersive animated cityscape for Constitution Challenge
 */

class CityRenderer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.width = options.width || 400;
        this.height = options.height || 300;
        
        this.svg = null;
        this.layers = {};
        this.animations = [];
        
        this.init();
    }
    
    init() {
        // Create main SVG container
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('viewBox', `0 0 ${this.width} ${this.height}`);
        this.svg.setAttribute('width', '100%');
        this.svg.setAttribute('height', '100%');
        this.svg.style.background = 'linear-gradient(to bottom, #87CEEB 0%, #98FB98 70%, #90EE90 100%)';
        
        // Create layers in order (bottom to top)
        this.createLayers();
        
        this.container.appendChild(this.svg);
        
        console.log('🎨 City Renderer initialized');
    }
    
    createLayers() {
        const layerNames = [
            'background',    // Sky, terrain base
            'terrain',      // Ground features, rivers
            'buildings',    // All buildings  
            'citizens',     // People and activities
            'weather',      // Weather effects, clouds
            'effects'       // Animations, fireworks, etc.
        ];
        
        layerNames.forEach(name => {
            const layer = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            layer.setAttribute('id', `layer-${name}`);
            layer.setAttribute('class', `city-layer city-layer-${name}`);
            this.layers[name] = layer;
            this.svg.appendChild(layer);
        });
        
        console.log('🏗️ City layers created:', Object.keys(this.layers));
    }
    
    /**
     * Main render method - updates entire city based on visual elements
     */
    render(visualElements) {
        console.log('🖼️ Rendering city with elements:', visualElements);
        
        // Clear existing content (except structure)
        Object.values(this.layers).forEach(layer => {
            layer.innerHTML = '';
        });
        
        // Map visual elements to SVG components
        const mappedElements = VisualMapper.mapElements(visualElements);
        
        // Render each layer
        this.renderBackground(mappedElements.terrain);
        this.renderTerrain(mappedElements.terrain, mappedElements.features);
        this.renderBuildings(mappedElements.buildings);
        this.renderCitizens(mappedElements.citizens);
        this.renderWeather(mappedElements.weather);
        this.renderEffects(mappedElements.effects);
        
        // Apply animations
        this.startAnimations(visualElements.animations || []);
        
        console.log('✨ City render complete');
    }
    
    renderBackground(terrain) {
        const backgroundLayer = this.layers.background;
        
        // Sky gradient
        const skyGradient = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        skyGradient.innerHTML = `
            <linearGradient id="skyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#87CEEB;stop-opacity:1" />
                <stop offset="70%" style="stop-color:${terrain.background};stop-opacity:0.8" />
                <stop offset="100%" style="stop-color:${terrain.ground};stop-opacity:0.6" />
            </linearGradient>
        `;
        backgroundLayer.appendChild(skyGradient);
        
        // Sky rectangle
        const sky = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        sky.setAttribute('x', '0');
        sky.setAttribute('y', '0');
        sky.setAttribute('width', this.width);
        sky.setAttribute('height', '70');
        sky.setAttribute('fill', 'url(#skyGradient)');
        backgroundLayer.appendChild(sky);
    }
    
    renderTerrain(terrain, features) {
        const terrainLayer = this.layers.terrain;
        
        // Base terrain
        if (terrain.svg) {
            const terrainGroup = this.createSVGGroup(terrain.svg);
            terrainGroup.setAttribute('transform', `scale(${this.width/100}, 1)`);
            terrainLayer.appendChild(terrainGroup);
        }
        
        // Natural features
        features.forEach(feature => {
            if (feature.svg) {
                const featureGroup = this.createSVGGroup(feature.svg);
                featureGroup.setAttribute('transform', `scale(${this.width/100}, 1)`);
                featureGroup.setAttribute('class', `feature-${feature.name}`);
                terrainLayer.appendChild(featureGroup);
                
                // Add animation class for animated features
                if (feature.animated) {
                    featureGroup.classList.add('animated-feature');
                }
            }
        });
    }
    
    renderBuildings(buildings) {
        const buildingsLayer = this.layers.buildings;
        
        // Render buildings by type
        ['residential', 'civic', 'commercial'].forEach(type => {
            const buildingList = buildings[type] || [];
            
            buildingList.forEach((building, index) => {
                if (building.svg && building.position) {
                    const buildingGroup = this.createSVGGroup(building.svg);
                    
                    // Position building
                    const x = (building.position[0] / 100) * this.width;
                    const y = (building.position[1] / 100) * this.height;
                    
                    buildingGroup.setAttribute('transform', `translate(${x}, ${y})`);
                    buildingGroup.setAttribute('class', `building building-${type} building-${building.type}`);
                    buildingGroup.setAttribute('data-building-id', `${type}-${index}`);
                    
                    // Add building status indicator
                    if (building.status === 'building') {\n                        buildingGroup.classList.add('under-construction');\n                    }\n                    \n                    buildingsLayer.appendChild(buildingGroup);\n                }\n            });\n        });\n    }\n    \n    renderCitizens(citizens) {\n        const citizensLayer = this.layers.citizens;\n        \n        if (citizens.population > 0) {\n            // Create citizen groups based on activities\n            citizens.activities.forEach((activity, index) => {\n                if (activity.svg) {\n                    const activityGroup = this.createSVGGroup(activity.svg);\n                    \n                    // Position activities across the city\n                    const x = (20 + index * 60) % (this.width - 40);\n                    const y = this.height - 40;\n                    \n                    activityGroup.setAttribute('transform', `translate(${x}, ${y})`);\n                    activityGroup.setAttribute('class', `citizens citizens-${activity.name}`);\n                    \n                    citizensLayer.appendChild(activityGroup);\n                }\n            });\n            \n            // Add population indicator\n            const populationText = document.createElementNS('http://www.w3.org/2000/svg', 'text');\n            populationText.setAttribute('x', '10');\n            populationText.setAttribute('y', '20');\n            populationText.setAttribute('fill', citizens.mood.color);\n            populationText.setAttribute('font-size', '12');\n            populationText.setAttribute('font-weight', 'bold');\n            populationText.textContent = `👥 ${citizens.population}`;\n            citizensLayer.appendChild(populationText);\n            \n            // Add mood indicator\n            const moodIndicator = document.createElementNS('http://www.w3.org/2000/svg', 'text');\n            moodIndicator.setAttribute('x', '10');\n            moodIndicator.setAttribute('y', '35');\n            moodIndicator.setAttribute('font-size', '16');\n            moodIndicator.textContent = citizens.mood.emoji;\n            citizensLayer.appendChild(moodIndicator);\n        }\n    }\n    \n    renderWeather(weather) {\n        const weatherLayer = this.layers.weather;\n        \n        if (weather.svg) {\n            const weatherGroup = this.createSVGGroup(weather.svg);\n            weatherGroup.setAttribute('class', 'weather-effects');\n            weatherLayer.appendChild(weatherGroup);\n            \n            if (weather.animated) {\n                weatherGroup.classList.add('animated-weather');\n            }\n        }\n        \n        // Add weather effects\n        weather.effects.forEach(effect => {\n            const effectElement = this.createWeatherEffect(effect);\n            if (effectElement) {\n                weatherLayer.appendChild(effectElement);\n            }\n        });\n    }\n    \n    renderEffects(effects) {\n        const effectsLayer = this.layers.effects;\n        \n        effects.forEach((effect, index) => {\n            const effectElement = document.createElementNS('http://www.w3.org/2000/svg', 'text');\n            effectElement.setAttribute('x', 50 + (index * 30));\n            effectElement.setAttribute('y', 30);\n            effectElement.setAttribute('font-size', '20');\n            effectElement.setAttribute('class', `effect effect-${effect.name}`);\n            effectElement.textContent = effect.emoji;\n            \n            effectsLayer.appendChild(effectElement);\n            \n            // Auto-remove after duration\n            setTimeout(() => {\n                if (effectElement.parentNode) {\n                    effectElement.parentNode.removeChild(effectElement);\n                }\n            }, effect.duration || 3000);\n        });\n    }\n    \n    createWeatherEffect(effect) {\n        switch (effect) {\n            case 'rainbow':\n                const rainbow = document.createElementNS('http://www.w3.org/2000/svg', 'path');\n                rainbow.setAttribute('d', `M 50 60 Q ${this.width/2} 20 ${this.width-50} 60`);\n                rainbow.setAttribute('stroke', 'url(#rainbowGradient)');\n                rainbow.setAttribute('stroke-width', '4');\n                rainbow.setAttribute('fill', 'none');\n                rainbow.setAttribute('opacity', '0.8');\n                \n                // Add rainbow gradient\n                const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');\n                defs.innerHTML = `\n                    <linearGradient id=\"rainbowGradient\" x1=\"0%\" y1=\"0%\" x2=\"100%\" y2=\"0%\">\n                        <stop offset=\"0%\" style=\"stop-color:#ff0000;stop-opacity:1\" />\n                        <stop offset=\"16.66%\" style=\"stop-color:#ff8000;stop-opacity:1\" />\n                        <stop offset=\"33.33%\" style=\"stop-color:#ffff00;stop-opacity:1\" />\n                        <stop offset=\"50%\" style=\"stop-color:#00ff00;stop-opacity:1\" />\n                        <stop offset=\"66.66%\" style=\"stop-color:#0000ff;stop-opacity:1\" />\n                        <stop offset=\"83.33%\" style=\"stop-color:#8000ff;stop-opacity:1\" />\n                        <stop offset=\"100%\" style=\"stop-color:#ff00ff;stop-opacity:1\" />\n                    </linearGradient>\n                `;\n                \n                const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');\n                group.appendChild(defs);\n                group.appendChild(rainbow);\n                return group;\n                \n            case 'lightning':\n                const lightning = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');\n                lightning.setAttribute('points', '200,30 210,50 205,50 215,80 200,60 205,60');\n                lightning.setAttribute('fill', '#FFB74D');\n                lightning.setAttribute('class', 'lightning-flash');\n                return lightning;\n                \n            default:\n                return null;\n        }\n    }\n    \n    createSVGGroup(svgString) {\n        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');\n        group.innerHTML = svgString;\n        return group;\n    }\n    \n    startAnimations(animationList) {\n        // Clear existing animations\n        this.animations.forEach(animation => {\n            if (animation.stop) animation.stop();\n        });\n        this.animations = [];\n        \n        // Start new animations\n        animationList.forEach(animName => {\n            const animation = this.createAnimation(animName);\n            if (animation) {\n                this.animations.push(animation);\n            }\n        });\n    }\n    \n    createAnimation(animName) {\n        switch (animName) {\n            case 'construction':\n                return this.animateConstruction();\n            case 'fireworks':\n                return this.animateFireworks();\n            case 'parade':\n                return this.animateParade();\n            default:\n                return null;\n        }\n    }\n    \n    animateConstruction() {\n        const buildings = this.layers.buildings.querySelectorAll('.under-construction');\n        buildings.forEach(building => {\n            // Add construction animation class\n            building.classList.add('construction-animate');\n            \n            setTimeout(() => {\n                building.classList.remove('under-construction', 'construction-animate');\n                building.classList.add('construction-complete');\n            }, 2000);\n        });\n        \n        return { stop: () => {} };\n    }\n    \n    animateFireworks() {\n        const effectsLayer = this.layers.effects;\n        let count = 0;\n        \n        const interval = setInterval(() => {\n            if (count >= 5) {\n                clearInterval(interval);\n                return;\n            }\n            \n            // Create firework burst\n            const firework = document.createElementNS('http://www.w3.org/2000/svg', 'circle');\n            firework.setAttribute('cx', 100 + Math.random() * 200);\n            firework.setAttribute('cy', 50 + Math.random() * 100);\n            firework.setAttribute('r', '0');\n            firework.setAttribute('fill', `hsl(${Math.random() * 360}, 70%, 60%)`);\n            firework.setAttribute('opacity', '0.8');\n            firework.setAttribute('class', 'firework-burst');\n            \n            effectsLayer.appendChild(firework);\n            \n            // Animate firework expansion\n            const animation = firework.animate([\n                { r: '0', opacity: '0.8' },\n                { r: '20', opacity: '0.4' },\n                { r: '30', opacity: '0' }\n            ], {\n                duration: 1500,\n                easing: 'ease-out'\n            });\n            \n            animation.onfinish = () => {\n                if (firework.parentNode) {\n                    firework.parentNode.removeChild(firework);\n                }\n            };\n            \n            count++;\n        }, 500);\n        \n        return { stop: () => clearInterval(interval) };\n    }\n    \n    animateParade() {\n        const citizensLayer = this.layers.citizens;\n        \n        // Create parade elements moving across screen\n        const parade = document.createElementNS('http://www.w3.org/2000/svg', 'g');\n        parade.innerHTML = `\n            <circle cx=\"0\" cy=\"0\" r=\"3\" fill=\"#4CAF50\"/>\n            <circle cx=\"10\" cy=\"0\" r=\"3\" fill=\"#FF5722\"/>\n            <circle cx=\"20\" cy=\"0\" r=\"3\" fill=\"#2196F3\"/>\n            <text x=\"10\" y=\"-10\" text-anchor=\"middle\" font-size=\"8\" fill=\"#333\">🎊</text>\n        `;\n        \n        parade.setAttribute('transform', `translate(-50, ${this.height - 60})`);\n        parade.setAttribute('class', 'parade-group');\n        \n        citizensLayer.appendChild(parade);\n        \n        // Animate parade movement\n        const animation = parade.animate([\n            { transform: `translate(-50, ${this.height - 60})` },\n            { transform: `translate(${this.width + 50}, ${this.height - 60})` }\n        ], {\n            duration: 4000,\n            easing: 'linear'\n        });\n        \n        animation.onfinish = () => {\n            if (parade.parentNode) {\n                parade.parentNode.removeChild(parade);\n            }\n        };\n        \n        return { stop: () => animation.cancel() };\n    }\n    \n    // Utility methods\n    addClickableBuilding(buildingElement, onClick) {\n        buildingElement.style.cursor = 'pointer';\n        buildingElement.addEventListener('click', onClick);\n        buildingElement.classList.add('clickable-building');\n    }\n    \n    updateGovernanceMeters(scores) {\n        // This could animate the governance meters with juice effects\n        console.log('📊 Updating governance meters:', scores);\n        \n        // Trigger particle effects for score changes\n        Object.keys(scores).forEach(metric => {\n            this.createScoreChangeEffect(metric, scores[metric]);\n        });\n    }\n    \n    createScoreChangeEffect(metric, newScore) {\n        // Create floating score change indicator\n        const effect = document.createElementNS('http://www.w3.org/2000/svg', 'text');\n        effect.setAttribute('x', Math.random() * this.width);\n        effect.setAttribute('y', '40');\n        effect.setAttribute('font-size', '14');\n        effect.setAttribute('font-weight', 'bold');\n        effect.setAttribute('fill', '#4CAF50');\n        effect.setAttribute('class', 'score-change-effect');\n        effect.textContent = `+${newScore}`;\n        \n        this.layers.effects.appendChild(effect);\n        \n        // Animate upward float and fade\n        const animation = effect.animate([\n            { transform: 'translateY(0)', opacity: '1' },\n            { transform: 'translateY(-30px)', opacity: '0' }\n        ], {\n            duration: 2000,\n            easing: 'ease-out'\n        });\n        \n        animation.onfinish = () => {\n            if (effect.parentNode) {\n                effect.parentNode.removeChild(effect);\n            }\n        };\n    }\n    \n    // Public API methods\n    resize(width, height) {\n        this.width = width || this.width;\n        this.height = height || this.height;\n        this.svg.setAttribute('viewBox', `0 0 ${this.width} ${this.height}`);\n    }\n    \n    clear() {\n        Object.values(this.layers).forEach(layer => {\n            layer.innerHTML = '';\n        });\n    }\n    \n    destroy() {\n        // Stop all animations\n        this.animations.forEach(animation => {\n            if (animation.stop) animation.stop();\n        });\n        \n        // Remove from DOM\n        if (this.svg && this.svg.parentNode) {\n            this.svg.parentNode.removeChild(this.svg);\n        }\n        \n        console.log('🗑️ City Renderer destroyed');\n    }\n}\n\n// Export for global use\nwindow.CityRenderer = CityRenderer;