/**
 * Performance Monitor + Auto Quality Scaling
 */

export interface PerfStats {
    fps: number
    frameTime: number
    particleCount: number
    drawCalls: number
    wsRate: number
}

export type QualityPreset = 'low' | 'medium' | 'high' | 'auto'

export interface QualitySettings {
    particleDensity: number      // 0.2 - 1.0
    enableGlow: boolean
    enableParticles: boolean
    maxHazards: number
    maxNodes: number
}

const PRESETS: Record<Exclude<QualityPreset, 'auto'>, QualitySettings> = {
    low: {
        particleDensity: 0.2,
        enableGlow: false,
        enableParticles: false,
        maxHazards: 10,
        maxNodes: 6,
    },
    medium: {
        particleDensity: 0.5,
        enableGlow: true,
        enableParticles: true,
        maxHazards: 30,
        maxNodes: 10,
    },
    high: {
        particleDensity: 1.0,
        enableGlow: true,
        enableParticles: true,
        maxHazards: 50,
        maxNodes: 20,
    },
}

export class PerfMonitor {
    private frameTimes: number[] = []
    private lastFrameTime = 0
    private particleCount = 0
    private drawCalls = 0
    private wsRate = 0
    private preset: QualityPreset = 'auto'
    private currentSettings: QualitySettings = PRESETS.medium
    private lowFpsFrames = 0

    update(currentTime: number) {
        if (this.lastFrameTime > 0) {
            const delta = currentTime - this.lastFrameTime
            this.frameTimes.push(delta)
            if (this.frameTimes.length > 60) {
                this.frameTimes.shift()
            }
        }
        this.lastFrameTime = currentTime

        // Auto quality scaling
        if (this.preset === 'auto') {
            const fps = this.getFPS()
            if (fps < 55) {
                this.lowFpsFrames++
                if (this.lowFpsFrames > 120) { // ~2 seconds
                    this.downgrade()
                    this.lowFpsFrames = 0
                }
            } else {
                this.lowFpsFrames = 0
            }
        }
    }

    getFPS(): number {
        if (this.frameTimes.length === 0) return 60
        const avg = this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length
        return 1000 / avg
    }

    getStats(): PerfStats {
        return {
            fps: Math.round(this.getFPS()),
            frameTime: this.frameTimes.length > 0 ? this.frameTimes[this.frameTimes.length - 1] : 16.67,
            particleCount: this.particleCount,
            drawCalls: this.drawCalls,
            wsRate: this.wsRate,
        }
    }

    setParticleCount(count: number) {
        this.particleCount = count
    }

    setDrawCalls(count: number) {
        this.drawCalls = count
    }

    setWsRate(rate: number) {
        this.wsRate = rate
    }

    setPreset(preset: QualityPreset) {
        this.preset = preset
        if (preset !== 'auto') {
            this.currentSettings = PRESETS[preset]
        }
    }

    getSettings(): QualitySettings {
        return this.currentSettings
    }

    private downgrade() {
        if (this.currentSettings.particleDensity > 0.5) {
            this.currentSettings = PRESETS.medium
            console.log('⚠️ Auto-downgraded to medium quality')
        } else if (this.currentSettings.particleDensity > 0.2) {
            this.currentSettings = PRESETS.low
            console.log('⚠️ Auto-downgraded to low quality')
        }
    }
}

export const perfMonitor = new PerfMonitor()
