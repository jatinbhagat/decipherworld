/**
 * Enhanced Web Audio System Module
 * Procedural sound effects for Constitution Challenge
 */

class AudioSystem {
    constructor() {
        this.audioContext = null;
        this.audioBuffers = new Map();
        this.soundEffects = new Map();
        this.masterVolume = 0.7;
        this.enabled = true;
        
        // Initialize Web Audio Context
        this.initAudioContext();
        
        // Create procedural sound effects
        this.createProceduralSounds();
        
        console.log('🔊 Enhanced Audio System initialized');
    }
    
    async initAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Resume context on first user interaction
            document.addEventListener('click', () => {
                if (this.audioContext.state === 'suspended') {
                    this.audioContext.resume();
                }
            }, { once: true });
            
        } catch (error) {
            console.warn('Web Audio API not supported:', error);
            this.enabled = false;
        }
    }
    
    // Create procedural sound effects using Web Audio API
    createProceduralSounds() {
        this.soundEffects.set('cheers', () => this.createCheerSound());
        this.soundEffects.set('construction_sound', () => this.createConstructionSound());
        this.soundEffects.set('celebration_music', () => this.createCelebrationChord());
        this.soundEffects.set('building_complete', () => this.createSuccessSound());
        this.soundEffects.set('notification', () => this.createNotificationSound());
        this.soundEffects.set('fireworks', () => this.createFireworkSound());
        this.soundEffects.set('applause', () => this.createApplauseSound());
    }
    
    // Create cheer sound effect
    createCheerSound() {
        if (!this.audioContext || !this.enabled) return;
        
        const duration = 0.8;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        // Cheer-like frequency sweep
        oscillator.frequency.setValueAtTime(200, this.audioContext.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(800, this.audioContext.currentTime + 0.1);
        oscillator.frequency.exponentialRampToValueAtTime(400, this.audioContext.currentTime + duration);
        
        // Volume envelope
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(this.masterVolume * 0.3, this.audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
        
        oscillator.type = 'sawtooth';
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration);
    }
    
    // Create construction sound effect
    createConstructionSound() {
        if (!this.audioContext || !this.enabled) return;
        
        const duration = 0.5;
        
        // Create noise for construction sound
        const bufferSize = this.audioContext.sampleRate * duration;
        const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
        const output = buffer.getChannelData(0);
        
        for (let i = 0; i < bufferSize; i++) {
            output[i] = (Math.random() * 2 - 1) * 0.1;
        }
        
        const noise = this.audioContext.createBufferSource();
        const filter = this.audioContext.createBiquadFilter();
        const gainNode = this.audioContext.createGain();
        
        noise.buffer = buffer;
        noise.connect(filter);
        filter.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(200, this.audioContext.currentTime);
        
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(this.masterVolume * 0.2, this.audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
        
        noise.start(this.audioContext.currentTime);
        noise.stop(this.audioContext.currentTime + duration);
    }
    
    // Create celebration chord
    createCelebrationChord() {
        if (!this.audioContext || !this.enabled) return;
        
        const duration = 1.0;
        const frequencies = [261.63, 329.63, 392.00]; // C major chord
        
        frequencies.forEach((freq, index) => {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            oscillator.frequency.setValueAtTime(freq, this.audioContext.currentTime);
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(this.masterVolume * 0.15, this.audioContext.currentTime + 0.1);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
            
            oscillator.start(this.audioContext.currentTime + index * 0.05);
            oscillator.stop(this.audioContext.currentTime + duration);
        });
    }
    
    // Create success sound
    createSuccessSound() {
        if (!this.audioContext || !this.enabled) return;
        
        const duration = 0.6;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        // Success sound frequency progression
        oscillator.frequency.setValueAtTime(523.25, this.audioContext.currentTime); // C5
        oscillator.frequency.setValueAtTime(659.25, this.audioContext.currentTime + 0.15); // E5
        oscillator.frequency.setValueAtTime(783.99, this.audioContext.currentTime + 0.3); // G5
        
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(this.masterVolume * 0.25, this.audioContext.currentTime + 0.02);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
        
        oscillator.type = 'triangle';
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration);
    }
    
    // Create notification sound
    createNotificationSound() {
        if (!this.audioContext || !this.enabled) return;
        
        const duration = 0.2;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, this.audioContext.currentTime);
        oscillator.frequency.setValueAtTime(600, this.audioContext.currentTime + 0.1);
        
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(this.masterVolume * 0.2, this.audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
        
        oscillator.type = 'sine';
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration);
    }
    
    // Create firework sound
    createFireworkSound() {
        if (!this.audioContext || !this.enabled) return;
        
        // Launch sound
        setTimeout(() => {
            this.createSuccessSound();
        }, 0);
        
        // Explosion sound
        setTimeout(() => {
            const duration = 0.8;
            const bufferSize = this.audioContext.sampleRate * duration;
            const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
            const output = buffer.getChannelData(0);
            
            for (let i = 0; i < bufferSize; i++) {
                output[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufferSize, 2);
            }
            
            const noise = this.audioContext.createBufferSource();
            const gainNode = this.audioContext.createGain();
            
            noise.buffer = buffer;
            noise.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            gainNode.gain.setValueAtTime(this.masterVolume * 0.3, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
            
            noise.start(this.audioContext.currentTime);
        }, 200);
    }
    
    // Create applause sound
    createApplauseSound() {
        if (!this.audioContext || !this.enabled) return;
        
        const duration = 2.0;
        
        // Multiple clap sounds to simulate applause
        for (let i = 0; i < 20; i++) {
            setTimeout(() => {
                const bufferSize = this.audioContext.sampleRate * 0.1;
                const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
                const output = buffer.getChannelData(0);
                
                for (let j = 0; j < bufferSize; j++) {
                    output[j] = (Math.random() * 2 - 1) * Math.exp(-j / bufferSize * 10);
                }
                
                const noise = this.audioContext.createBufferSource();
                const filter = this.audioContext.createBiquadFilter();
                const gainNode = this.audioContext.createGain();
                
                noise.buffer = buffer;
                noise.connect(filter);
                filter.connect(gainNode);
                gainNode.connect(this.audioContext.destination);
                
                filter.type = 'highpass';
                filter.frequency.setValueAtTime(1000, this.audioContext.currentTime);
                
                gainNode.gain.setValueAtTime(this.masterVolume * 0.1, this.audioContext.currentTime);
                
                noise.start(this.audioContext.currentTime);
            }, Math.random() * duration * 1000);
        }
    }
    
    // Play sound effect
    playSound(soundName) {
        if (!this.enabled || !this.soundEffects.has(soundName)) {
            console.log('🔊 Audio cue:', soundName);
            return;
        }
        
        const soundFunction = this.soundEffects.get(soundName);
        try {
            soundFunction();
            console.log('🎵 Played sound:', soundName);
        } catch (error) {
            console.warn('Audio playback error:', error);
        }
    }
    
    // Set master volume
    setVolume(volume) {
        this.masterVolume = Math.max(0, Math.min(1, volume));
    }
    
    // Toggle audio system
    toggle() {
        this.enabled = !this.enabled;
        console.log(`🔊 Audio system ${this.enabled ? 'enabled' : 'disabled'}`);
        return this.enabled;
    }
    
    // Cleanup method with comprehensive memory management
    destroy() {
        // Close and clear audio context
        if (this.audioContext) {
            if (this.audioContext.state !== 'closed') {
                this.audioContext.close().then(() => {
                    console.log('🔊 AudioContext closed');
                }).catch(error => {
                    console.warn('Error closing AudioContext:', error);
                });
            }
            this.audioContext = null;
        }
        
        // Clear all sound effects and buffers
        this.soundEffects.clear();
        this.audioBuffers.clear();
        
        // Reset state
        this.enabled = false;
        this.masterVolume = 0;
        
        console.log('🔊 Audio System destroyed with full cleanup');
    }
    
    // Memory usage monitoring
    getMemoryUsage() {
        const bufferSize = Array.from(this.audioBuffers.values()).reduce((total, buffer) => {
            return total + (buffer.length * buffer.numberOfChannels * 4); // 4 bytes per float32
        }, 0);
        
        return {
            bufferCount: this.audioBuffers.size,
            bufferSizeBytes: bufferSize,
            soundEffectCount: this.soundEffects.size,
            contextState: this.audioContext?.state || 'none'
        };
    }
}

// Export for module use
window.AudioSystem = AudioSystem;