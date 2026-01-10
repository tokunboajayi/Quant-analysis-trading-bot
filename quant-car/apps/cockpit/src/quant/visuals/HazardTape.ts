/**
 * HazardTape - Animated event risk tape
 */
import * as PIXI from 'pixi.js'
import { theme } from '../engine/theme'

interface Hazard {
    id: string
    ticker: string
    direction: 'up' | 'down' | 'unknown'
    risk_prob: number
    eta_seconds: number
}

export class HazardTape {
    container: PIXI.Container
    private tags: Map<string, { x: number; opacity: number; g: PIXI.Container }> = new Map()
    private width: number
    private height: number

    constructor(width: number, height: number) {
        this.width = width
        this.height = height
        this.container = new PIXI.Container()

        // Background
        const bg = new PIXI.Graphics()
        bg.beginFill(theme.bg.elevated, 0.5)
        bg.drawRoundedRect(0, 0, width, height, 4)
        bg.endFill()
        this.container.addChild(bg)
    }

    update(hazards: Hazard[], dt: number) {
        hazards.forEach(h => {
            if (!this.tags.has(h.id) && h.eta_seconds > 0) {
                const g = this.createTag(h)
                this.tags.set(h.id, { x: -100, opacity: 1, g })
                this.container.addChild(g)
            }
        })

        this.tags.forEach((tag, id) => {
            tag.x += dt * 40
            if (tag.x > this.width + 100) tag.x = -100
            tag.g.position.set(tag.x, this.height / 2)
        })
    }

    private createTag(h: Hazard): PIXI.Container {
        const c = new PIXI.Container()
        const color = h.direction === 'down' ? theme.semantic.negative : theme.semantic.positive
        const bg = new PIXI.Graphics()
        bg.beginFill(color, 0.3)
        bg.drawRoundedRect(-35, -12, 70, 24, 4)
        bg.endFill()
        c.addChild(bg)

        const t = new PIXI.Text(h.ticker, { fontSize: 10, fill: color })
        t.anchor.set(0.5)
        c.addChild(t)
        return c
    }

    resize(w: number, h: number) { this.width = w; this.height = h }
}
