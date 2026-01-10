/**
 * Waterfall - Factor contribution waterfall chart
 */
import * as PIXI from 'pixi.js'
import { theme } from '../engine/theme'

interface Contribution {
    label: string
    value: number
}

export class Waterfall {
    container: PIXI.Container
    private animatedValues: number[] = []
    private width: number
    private height: number

    constructor(width: number, height: number) {
        this.width = width
        this.height = height
        this.container = new PIXI.Container()
    }

    update(contributions: Contribution[], dt: number) {
        // Animate values
        contributions.forEach((c, i) => {
            if (this.animatedValues[i] === undefined) this.animatedValues[i] = 0
            this.animatedValues[i] += (c.value - this.animatedValues[i]) * 0.1
        })

        this.render(contributions)
    }

    private render(contributions: Contribution[]) {
        this.container.removeChildren()

        if (contributions.length === 0) return

        const barWidth = (this.width - 20) / contributions.length
        const maxVal = Math.max(...contributions.map(c => Math.abs(c.value)), 0.01)
        const centerY = this.height / 2

        let runningTotal = 0

        contributions.forEach((c, i) => {
            const x = 10 + i * barWidth
            const animVal = this.animatedValues[i] || 0
            const barHeight = (animVal / maxVal) * (this.height * 0.4)

            const g = new PIXI.Graphics()
            const color = animVal >= 0 ? theme.semantic.positive : theme.semantic.negative

            g.beginFill(color, 0.7)
            if (animVal >= 0) {
                g.drawRect(x, centerY - barHeight, barWidth - 4, barHeight)
            } else {
                g.drawRect(x, centerY, barWidth - 4, -barHeight)
            }
            g.endFill()

            // Label
            const label = new PIXI.Text(c.label, { fontSize: 8, fill: theme.text.dim })
            label.anchor.set(0.5, 0)
            label.position.set(x + barWidth / 2, this.height - 15)
            label.rotation = -0.3
            g.addChild(label)

            this.container.addChild(g)
            runningTotal += animVal
        })

        // Running total line
        const line = new PIXI.Graphics()
        line.lineStyle(1, theme.text.secondary, 0.5)
        line.moveTo(10, centerY)
        line.lineTo(this.width - 10, centerY)
        this.container.addChild(line)
    }

    resize(w: number, h: number) { this.width = w; this.height = h }
}
