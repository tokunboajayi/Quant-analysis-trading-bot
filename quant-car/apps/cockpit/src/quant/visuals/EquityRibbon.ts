/**
 * EquityRibbon - Animated equity line + drawdown ribbon
 */
import * as PIXI from 'pixi.js'
import { theme } from '../engine/theme'

interface DataPoint {
    equity: number
    drawdown: number
    ts: number
}

export class EquityRibbon {
    container: PIXI.Container
    private equityLine: PIXI.Graphics
    private drawdownRibbon: PIXI.Graphics
    private gridLines: PIXI.Graphics
    private dataPoints: DataPoint[] = []
    private maxPoints = 120  // 1 minute of 2Hz data
    private width: number
    private height: number
    private animatedEquity: number[] = []
    private animatedDrawdown: number[] = []

    constructor(width: number, height: number) {
        this.width = width
        this.height = height
        this.container = new PIXI.Container()

        this.gridLines = new PIXI.Graphics()
        this.drawdownRibbon = new PIXI.Graphics()
        this.equityLine = new PIXI.Graphics()

        this.container.addChild(this.gridLines)
        this.container.addChild(this.drawdownRibbon)
        this.container.addChild(this.equityLine)

        this.renderGrid()
    }

    addPoint(equity: number, drawdown: number) {
        this.dataPoints.push({ equity, drawdown, ts: Date.now() })
        if (this.dataPoints.length > this.maxPoints) {
            this.dataPoints.shift()
        }

        // Initialize animated values
        this.animatedEquity.push(equity)
        this.animatedDrawdown.push(drawdown)
        if (this.animatedEquity.length > this.maxPoints) {
            this.animatedEquity.shift()
            this.animatedDrawdown.shift()
        }
    }

    update(dt: number) {
        // Smooth animation (interpolate toward target)
        for (let i = 0; i < this.dataPoints.length; i++) {
            if (this.animatedEquity[i] !== undefined) {
                this.animatedEquity[i] += (this.dataPoints[i].equity - this.animatedEquity[i]) * 0.1
                this.animatedDrawdown[i] += (this.dataPoints[i].drawdown - this.animatedDrawdown[i]) * 0.1
            }
        }

        this.render()
    }

    private renderGrid() {
        this.gridLines.clear()
        this.gridLines.lineStyle(1, theme.border.subtle, 0.3)

        // Horizontal lines
        for (let i = 0; i <= 4; i++) {
            const y = (i / 4) * this.height
            this.gridLines.moveTo(0, y)
            this.gridLines.lineTo(this.width, y)
        }

        // Vertical lines
        for (let i = 0; i <= 6; i++) {
            const x = (i / 6) * this.width
            this.gridLines.moveTo(x, 0)
            this.gridLines.lineTo(x, this.height)
        }
    }

    private render() {
        if (this.animatedEquity.length < 2) return

        // Find min/max for scaling
        const minEquity = Math.min(...this.animatedEquity) * 0.99
        const maxEquity = Math.max(...this.animatedEquity) * 1.01
        const equityRange = maxEquity - minEquity || 1

        const maxDD = Math.max(...this.animatedDrawdown.map(d => Math.abs(d)))

        // Render drawdown ribbon
        this.drawdownRibbon.clear()
        this.drawdownRibbon.beginFill(theme.semantic.negative, 0.2)

        const ddPoints: { x: number; y: number }[] = []
        this.animatedDrawdown.forEach((dd, i) => {
            const x = (i / (this.maxPoints - 1)) * this.width
            const y = this.height - (Math.abs(dd) / (maxDD || 0.1)) * (this.height * 0.3)
            ddPoints.push({ x, y })
        })

        if (ddPoints.length > 0) {
            this.drawdownRibbon.moveTo(0, this.height)
            ddPoints.forEach(p => this.drawdownRibbon.lineTo(p.x, p.y))
            this.drawdownRibbon.lineTo(this.width, this.height)
            this.drawdownRibbon.closePath()
            this.drawdownRibbon.endFill()
        }

        // Render equity line
        this.equityLine.clear()
        this.equityLine.lineStyle(2, theme.chart.equity, 1)

        this.animatedEquity.forEach((eq, i) => {
            const x = (i / (this.maxPoints - 1)) * this.width
            const y = this.height - ((eq - minEquity) / equityRange) * this.height * 0.8 - this.height * 0.1

            if (i === 0) {
                this.equityLine.moveTo(x, y)
            } else {
                this.equityLine.lineTo(x, y)
            }
        })
    }

    resize(width: number, height: number) {
        this.width = width
        this.height = height
        this.renderGrid()
    }
}
