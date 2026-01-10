/**
 * RegimeRiver - Animated regime band timeline
 */
import * as PIXI from 'pixi.js'
import { theme } from '../engine/theme'

type Regime = 'clear' | 'rain' | 'storm'

export class RegimeRiver {
    container: PIXI.Container
    private bands: { regime: Regime; width: number }[] = []
    private maxBands = 60
    private width: number
    private height: number

    constructor(width: number, height: number) {
        this.width = width
        this.height = height
        this.container = new PIXI.Container()
    }

    addRegime(regime: Regime, confidence: number) {
        this.bands.push({ regime, width: 1 + confidence * 2 })
        if (this.bands.length > this.maxBands) this.bands.shift()
    }

    update(dt: number) {
        this.container.removeChildren()

        const g = new PIXI.Graphics()
        let x = 0
        const bandWidth = this.width / this.maxBands

        this.bands.forEach((band, i) => {
            const color = theme.regime[band.regime]
            g.beginFill(color, 0.4 + (i / this.bands.length) * 0.4)
            g.drawRect(x, (this.height - band.width * 10) / 2, bandWidth, band.width * 10)
            g.endFill()
            x += bandWidth
        })

        this.container.addChild(g)
    }

    resize(w: number, h: number) { this.width = w; this.height = h }
}
