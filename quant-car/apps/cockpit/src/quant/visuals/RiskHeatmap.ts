/**
 * RiskHeatmap - Animated sector x risk intensity grid
 */
import * as PIXI from 'pixi.js'
import { theme, getSectorColor } from '../engine/theme'

interface Node { id: string; label: string; weight: number }

export class RiskHeatmap {
    container: PIXI.Container
    private cells: PIXI.Graphics[] = []
    private width: number
    private height: number

    constructor(width: number, height: number) {
        this.width = width
        this.height = height
        this.container = new PIXI.Container()
    }

    update(nodes: Node[], tractionRisk: number, varPressure: number, dt: number) {
        this.container.removeChildren()
        this.cells = []

        const sorted = [...nodes].sort((a, b) => b.weight - a.weight).slice(0, 6)
        const cellW = this.width / 3
        const cellH = this.height / 2

        sorted.forEach((node, i) => {
            const col = i % 3
            const row = Math.floor(i / 3)
            const x = col * cellW
            const y = row * cellH

            const risk = (1 - tractionRisk) * 0.5 + varPressure * 0.5
            const intensity = Math.min(1, node.weight * 3 + risk)

            const g = new PIXI.Graphics()
            const color = getSectorColor(node.label)
            g.beginFill(color, intensity * 0.6)
            g.lineStyle(1, theme.border.subtle)
            g.drawRect(x + 2, y + 2, cellW - 4, cellH - 4)
            g.endFill()

            const label = new PIXI.Text(node.label.replace('sector:', ''), {
                fontSize: 10, fill: theme.text.secondary
            })
            label.position.set(x + 6, y + 6)
            g.addChild(label)

            const pct = new PIXI.Text(`${(node.weight * 100).toFixed(1)}%`, {
                fontSize: 9, fill: theme.text.dim
            })
            pct.position.set(x + 6, y + 22)
            g.addChild(pct)

            this.container.addChild(g)
            this.cells.push(g)
        })
    }

    resize(w: number, h: number) { this.width = w; this.height = h }
}
