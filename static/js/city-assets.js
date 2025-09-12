/**
 * Comprehensive Visual Feature Mapping System
 * Maps game state to SVG city elements and animations
 */

// SVG Asset Library - Free cartoon-style city elements
const CityAssets = {
    
    // Terrain Elements
    terrain: {
        barren: {
            background: '#E8D5C4',
            ground: '#D4B896',
            svg: `<rect x="0" y="70" width="100" height="30" fill="#D4B896"/>
                  <circle cx="20" cy="85" r="3" fill="#C4A373" opacity="0.5"/>
                  <circle cx="60" cy="80" r="2" fill="#C4A373" opacity="0.5"/>`,
            description: 'Dry, barren landscape with scattered rocks'
        },
        dusty: {
            background: '#E8D5C4',
            ground: '#D4B896',
            svg: `<rect x="0" y="70" width="100" height="30" fill="#D4B896"/>
                  <rect x="10" y="75" width="8" height="2" fill="#B8A082" rx="1"/>
                  <rect x="70" y="78" width="6" height="2" fill="#B8A082" rx="1"/>`,
            description: 'Dusty terrain with small vegetation patches'
        },
        green: {
            background: '#C8E6C9',
            ground: '#81C784',
            svg: `<rect x="0" y="70" width="100" height="30" fill="#81C784"/>
                  <circle cx="15" cy="75" r="2" fill="#4CAF50"/>
                  <circle cx="85" cy="78" r="1.5" fill="#4CAF50"/>`,
            description: 'Green grass beginning to grow'
        },
        lush: {
            background: '#A5D6A7',
            ground: '#66BB6A',
            svg: `<rect x="0" y="70" width="100" height="30" fill="#66BB6A"/>
                  <circle cx="12" cy="72" r="3" fill="#2E7D32"/>
                  <circle cx="88" cy="75" r="2.5" fill="#2E7D32"/>
                  <rect x="30" y="76" width="20" height="3" fill="#4CAF50" rx="1.5"/>`,
            description: 'Lush green landscape with healthy vegetation'
        },
        fertile: {
            background: '#81C784',
            ground: '#4CAF50',
            svg: `<rect x="0" y="70" width="100" height="30" fill="#4CAF50"/>
                  <circle cx="10" cy="70" r="4" fill="#2E7D32"/>
                  <circle cx="90" cy="73" r="3" fill="#2E7D32"/>
                  <rect x="25" y="74" width="30" height="4" fill="#388E3C" rx="2"/>`,
            description: 'Rich, fertile ground with abundant growth'
        },
        paradise: {
            background: '#C8E6C9',
            ground: '#4CAF50',
            svg: `<rect x="0" y="70" width="100" height="30" fill="#4CAF50"/>
                  <circle cx="8" cy="68" r="5" fill="#2E7D32"/>
                  <circle cx="92" cy="71" r="4" fill="#2E7D32"/>
                  <rect x="20" y="72" width="40" height="5" fill="#388E3C" rx="2.5"/>
                  <circle cx="50" cy="65" r="2" fill="#FFB74D" opacity="0.8"/>`,
            description: 'Paradise-like landscape with flowers and perfect vegetation'
        }
    },
    
    // Building Assets
    buildings: {
        residential: {
            hut: {
                svg: `<g>
                    <rect x="0" y="5" width="12" height="8" fill="#8D6E63" rx="1"/>
                    <polygon points="0,5 6,0 12,5" fill="#5D4037"/>
                    <rect x="3" y="8" width="2" height="3" fill="#3E2723"/>
                    <rect x="8" y="7" width="2" height="2" fill="#FFE082" opacity="0.7"/>
                </g>`,
                width: 12,
                height: 13,
                description: 'Simple wooden hut'
            },
            house: {
                svg: `<g>
                    <rect x="0" y="4" width="16" height="12" fill="#FFCC02" rx="1"/>
                    <polygon points="0,4 8,0 16,4" fill="#D32F2F"/>
                    <rect x="4" y="10" width="3" height="6" fill="#8D6E63"/>
                    <rect x="10" y="8" width="3" height="3" fill="#81C784" stroke="#4CAF50"/>
                    <circle cx="11.5" cy="9.5" r="0.5" fill="#2196F3"/>
                </g>`,
                width: 16,
                height: 16,
                description: 'Comfortable family house'
            },
            apartment: {
                svg: `<g>
                    <rect x="0" y="0" width="20" height="20" fill="#F5F5F5" stroke="#9E9E9E"/>
                    <rect x="2" y="2" width="3" height="3" fill="#81C784" stroke="#4CAF50"/>
                    <rect x="6" y="2" width="3" height="3" fill="#81C784" stroke="#4CAF50"/>
                    <rect x="2" y="6" width="3" height="3" fill="#81C784" stroke="#4CAF50"/>
                    <rect x="6" y="6" width="3" height="3" fill="#81C784" stroke="#4CAF50"/>
                    <rect x="12" y="15" width="4" height="5" fill="#8D6E63"/>
                </g>`,
                width: 20,
                height: 20,
                description: 'Modern apartment building'
            }
        },
        civic: {
            school: {
                svg: `<g>
                    <rect x="0" y="5" width="24" height="15" fill="#FFEB3B" rx="2"/>
                    <polygon points="0,5 12,0 24,5" fill="#FF5722"/>
                    <rect x="10" y="12" width="4" height="8" fill="#8D6E63"/>
                    <rect x="4" y="9" width="4" height="4" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="16" y="9" width="4" height="4" fill="#03A9F4" stroke="#0277BD"/>
                    <text x="12" y="18" text-anchor="middle" font-size="4" fill="#333">📚</text>
                </g>`,
                width: 24,
                height: 20,
                description: 'Educational school building'
            },
            courthouse: {
                svg: `<g>
                    <rect x="2" y="8" width="20" height="12" fill="#F5F5F5" stroke="#757575"/>
                    <rect x="0" y="6" width="24" height="3" fill="#9E9E9E"/>
                    <rect x="4" y="10" width="2" height="10" fill="#616161"/>
                    <rect x="8" y="10" width="2" height="10" fill="#616161"/>
                    <rect x="12" y="10" width="2" height="10" fill="#616161"/>
                    <rect x="16" y="10" width="2" height="10" fill="#616161"/>
                    <rect x="20" y="10" width="2" height="10" fill="#616161"/>
                    <text x="12" y="17" text-anchor="middle" font-size="4" fill="#333">⚖️</text>
                </g>`,
                width: 24,
                height: 20,
                description: 'Justice courthouse with columns'
            },
            hospital: {
                svg: `<g>
                    <rect x="0" y="4" width="20" height="16" fill="#FFFFFF" stroke="#E0E0E0"/>
                    <rect x="8" y="0" width="4" height="4" fill="#F44336"/>
                    <rect x="10" y="1" width="2" height="2" fill="#FFFFFF"/>
                    <rect x="9" y="1.5" width="4" height="1" fill="#FFFFFF"/>
                    <rect x="2" y="8" width="4" height="4" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="14" y="8" width="4" height="4" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="8" y="15" width="4" height="5" fill="#8D6E63"/>
                </g>`,
                width: 20,
                height: 20,
                description: 'Medical hospital facility'
            },
            parliament: {
                svg: `<g>
                    <rect x="4" y="8" width="24" height="12" fill="#F5F5F5" stroke="#757575"/>
                    <rect x="0" y="6" width="32" height="4" fill="#9E9E9E"/>
                    <polygon points="0,6 16,0 32,6" fill="#8BC34A"/>
                    <rect x="6" y="10" width="2" height="10" fill="#616161"/>
                    <rect x="10" y="10" width="2" height="10" fill="#616161"/>
                    <rect x="14" y="10" width="2" height="10" fill="#616161"/>
                    <rect x="18" y="10" width="2" height="10" fill="#616161"/>
                    <rect x="22" y="10" width="2" height="10" fill="#616161"/>
                    <rect x="26" y="10" width="2" height="10" fill="#616161"/>
                    <text x="16" y="17" text-anchor="middle" font-size="5" fill="#333">🏛️</text>
                </g>`,
                width: 32,
                height: 20,
                description: 'Grand parliament building'
            },
            university: {
                svg: `<g>
                    <rect x="2" y="6" width="28" height="14" fill="#FFEB3B" rx="2"/>
                    <polygon points="2,6 16,0 30,6" fill="#FF9800"/>
                    <rect x="6" y="10" width="3" height="3" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="12" y="10" width="3" height="3" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="18" y="10" width="3" height="3" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="24" y="10" width="3" height="3" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="13" y="16" width="4" height="4" fill="#8D6E63"/>
                    <text x="16" y="18" text-anchor="middle" font-size="4" fill="#333">🎓</text>
                </g>`,
                width: 32,
                height: 20,
                description: 'University education center'
            }
        },
        commercial: {
            marketplace: {
                svg: `<g>
                    <rect x="2" y="8" width="16" height="10" fill="#FFB74D" rx="1"/>
                    <polygon points="2,8 10,4 18,8" fill="#F57C00"/>
                    <rect x="0" y="12" width="20" height="2" fill="#FF8F00"/>
                    <rect x="4" y="10" width="2" height="2" fill="#4CAF50"/>
                    <rect x="8" y="10" width="2" height="2" fill="#F44336"/>
                    <rect x="12" y="10" width="2" height="2" fill="#2196F3"/>
                    <rect x="14" y="10" width="2" height="2" fill="#9C27B0"/>
                </g>`,
                width: 20,
                height: 18,
                description: 'Bustling marketplace'
            },
            mall: {
                svg: `<g>
                    <rect x="0" y="4" width="28" height="16" fill="#E1F5FE" stroke="#0277BD"/>
                    <rect x="4" y="8" width="4" height="4" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="10" y="8" width="4" height="4" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="16" y="8" width="4" height="4" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="22" y="8" width="4" height="4" fill="#03A9F4" stroke="#0277BD"/>
                    <rect x="12" y="16" width="4" height="4" fill="#8D6E63"/>
                    <text x="14" y="11" text-anchor="middle" font-size="3" fill="#333">🏪</text>
                </g>`,
                width: 28,
                height: 20,
                description: 'Modern shopping mall'
            }
        }
    },
    
    // Natural Features
    features: {
        river: {
            svg: `<path d="M0,50 Q25,45 50,50 Q75,55 100,50" stroke="#2196F3" stroke-width="4" fill="none" opacity="0.7"/>
                  <path d="M5,52 Q30,47 55,52 Q80,57 95,52" stroke="#81C784" stroke-width="2" fill="none" opacity="0.5"/>`,
            description: 'Winding river flowing through the landscape',
            animated: true
        },
        hills: {
            svg: `<ellipse cx="20" cy="65" rx="15" ry="8" fill="#4CAF50" opacity="0.6"/>
                  <ellipse cx="80" cy="68" rx="12" ry="6" fill="#66BB6A" opacity="0.6"/>`,
            description: 'Rolling green hills'
        },
        trees: {
            svg: `<g>
                <circle cx="25" cy="60" r="5" fill="#4CAF50"/>
                <rect x="24" y="60" width="2" height="6" fill="#8D6E63"/>
                <circle cx="75" cy="62" r="4" fill="#4CAF50"/>
                <rect x="74" y="62" width="2" height="5" fill="#8D6E63"/>
            </g>`,
            description: 'Scattered trees across the landscape'
        },
        gardens: {
            svg: `<g>
                <rect x="30" y="65" width="8" height="6" fill="#4CAF50" rx="1"/>
                <circle cx="32" cy="66" r="1" fill="#FF5722"/>
                <circle cx="36" cy="68" r="1" fill="#FFEB3B"/>
                <rect x="60" y="67" width="6" height="4" fill="#4CAF50" rx="1"/>
                <circle cx="62" cy="68" r="0.8" fill="#E91E63"/>
                <circle cx="64" cy="69" r="0.8" fill="#2196F3"/>
            </g>`,
            description: 'Beautiful flower gardens'
        },
        fountains: {
            svg: `<g>
                <circle cx="50" cy="68" r="3" fill="#81C784" stroke="#4CAF50"/>
                <circle cx="50" cy="68" r="1.5" fill="#2196F3" opacity="0.8"/>
                <circle cx="50" cy="65" r="0.5" fill="#81C784" opacity="0.6"/>
            </g>`,
            description: 'Ornate water fountain',
            animated: true
        }
    },
    
    // Weather Effects
    weather: {
        sunny: {
            svg: `<g>
                <circle cx="80" cy="15" r="6" fill="#FFB74D"/>
                <g transform="translate(80,15)">
                    <line x1="-10" y1="0" x2="-8" y2="0" stroke="#FFB74D" stroke-width="1"/>
                    <line x1="8" y1="0" x2="10" y2="0" stroke="#FFB74D" stroke-width="1"/>
                    <line x1="0" y1="-10" x2="0" y2="-8" stroke="#FFB74D" stroke-width="1"/>
                    <line x1="0" y1="8" x2="0" y2="10" stroke="#FFB74D" stroke-width="1"/>
                </g>
            </g>`,
            description: 'Bright sunny day'
        },
        partly_cloudy: {
            svg: `<g>
                <circle cx="75" cy="15" r="5" fill="#FFB74D"/>
                <circle cx="85" cy="20" r="4" fill="#F5F5F5" stroke="#E0E0E0"/>
                <circle cx="90" cy="18" r="3" fill="#F5F5F5" stroke="#E0E0E0"/>
            </g>`,
            description: 'Partly cloudy skies'
        },
        cloudy: {
            svg: `<g>
                <circle cx="75" cy="20" r="6" fill="#E0E0E0" stroke="#BDBDBD"/>
                <circle cx="85" cy="18" r="5" fill="#E0E0E0" stroke="#BDBDBD"/>
                <circle cx="90" cy="22" r="4" fill="#E0E0E0" stroke="#BDBDBD"/>
            </g>`,
            description: 'Overcast cloudy weather'
        },
        stormy: {
            svg: `<g>
                <circle cx="70" cy="20" r="7" fill="#757575" stroke="#424242"/>
                <circle cx="82" cy="18" r="6" fill="#757575" stroke="#424242"/>
                <circle cx="90" cy="23" r="5" fill="#757575" stroke="#424242"/>
                <polygon points="78,25 80,30 76,27 78,32 74,28" fill="#FFB74D"/>
            </g>`,
            description: 'Dark storm clouds with lightning',
            animated: true
        }
    },
    
    // Citizens and Activities
    citizens: {
        moods: {
            happy: { color: '#4CAF50', emoji: '😊' },
            neutral: { color: '#FF9800', emoji: '😐' },
            angry: { color: '#F44336', emoji: '😠' }
        },
        activities: {
            celebration: {
                svg: `<g>
                    <circle cx="30" cy="75" r="2" fill="#FFB74D"/>
                    <circle cx="35" cy="73" r="2" fill="#FF5722"/>
                    <circle cx="25" cy="77" r="1.5" fill="#4CAF50"/>
                    <text x="30" y="70" text-anchor="middle" font-size="4" fill="#333">🎉</text>
                </g>`,
                description: 'Citizens celebrating'
            },
            protest: {
                svg: `<g>
                    <circle cx="40" cy="75" r="2" fill="#F44336"/>
                    <circle cx="45" cy="73" r="2" fill="#F44336"/>
                    <rect x="42" y="65" width="1" height="8" fill="#8D6E63"/>
                    <rect x="39" y="65" width="6" height="2" fill="#FFEB3B"/>
                </g>`,
                description: 'Citizens protesting'
            },
            work: {
                svg: `<g>
                    <circle cx="60" cy="75" r="2" fill="#FF9800"/>
                    <circle cx="65" cy="73" r="2" fill="#FF9800"/>
                    <rect x="58" y="70" width="2" height="3" fill="#8D6E63"/>
                </g>`,
                description: 'Citizens working'
            }
        }
    }
};

// Visual Feature Mapping System
const VisualMapper = {
    
    /**
     * Map visual elements to SVG components
     */
    mapElements(visualElements) {
        const svgElements = {
            terrain: this.mapTerrain(visualElements.terrain),
            buildings: this.mapBuildings(visualElements.buildings),
            features: this.mapFeatures(visualElements.terrain?.features || []),
            weather: this.mapWeather(visualElements.weather),
            citizens: this.mapCitizens(visualElements.citizens),
            effects: this.mapEffects(visualElements.animations || [])
        };
        
        return svgElements;
    },
    
    mapTerrain(terrain) {
        const terrainData = CityAssets.terrain[terrain?.type] || CityAssets.terrain.barren;
        return {
            svg: terrainData.svg,
            background: terrainData.background,
            ground: terrainData.ground,
            description: terrainData.description
        };
    },
    
    mapBuildings(buildings) {
        const mappedBuildings = {
            residential: [],
            civic: [],
            commercial: []
        };
        
        // Map each building type
        Object.keys(mappedBuildings).forEach(type => {
            const buildingList = buildings[type] || [];
            mappedBuildings[type] = buildingList.map(building => {
                const asset = CityAssets.buildings[type][building.type];
                if (asset) {
                    return {
                        ...building,
                        svg: asset.svg,
                        width: asset.width,
                        height: asset.height,
                        description: asset.description
                    };
                }
                return building;
            });
        });
        
        return mappedBuildings;
    },
    
    mapFeatures(features) {
        return features.map(featureName => {
            const feature = CityAssets.features[featureName];
            if (feature) {
                return {
                    name: featureName,
                    svg: feature.svg,
                    description: feature.description,
                    animated: feature.animated || false
                };
            }
            return { name: featureName, svg: '', description: featureName };
        });
    },
    
    mapWeather(weather) {
        const weatherData = CityAssets.weather[weather?.type] || CityAssets.weather.cloudy;
        return {
            svg: weatherData.svg,
            description: weatherData.description,
            animated: weatherData.animated || false,
            effects: weather?.effects || []
        };
    },
    
    mapCitizens(citizens) {
        const mood = citizens?.mood || 'neutral';
        const population = citizens?.population || 10;
        const activities = citizens?.activities || ['work'];
        
        return {
            mood: CityAssets.citizens.moods[mood],
            population: population,
            activities: activities.map(activityName => {
                const activity = CityAssets.citizens.activities[activityName];
                return activity ? {
                    name: activityName,
                    svg: activity.svg,
                    description: activity.description
                } : { name: activityName, svg: '', description: activityName };
            })
        };
    },
    
    mapEffects(animations) {
        const effectMap = {
            'fireworks': '🎆',
            'construction': '🏗️',
            'parade': '🎊',
            'building_complete': '✨'
        };
        
        return animations.map(animName => ({
            name: animName,
            emoji: effectMap[animName] || '✨',
            duration: 2000
        }));
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CityAssets, VisualMapper };
}