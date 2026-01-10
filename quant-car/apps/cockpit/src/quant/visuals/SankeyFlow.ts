/**
 * SankeyFlow - Animated portfolio flow graph with particle streams
 */
import * as PIXI from 'pixi.js'
import { theme, getSectorColor } from '../engine/theme'
import { perfMonitor } from '../engine/perf'

interface FlowNode {
    id: string
    label: string
    weight: number
    weight_change_1d?: number
    x: number
    y: number
    width: number
    height: number
}

interface FlowEdge {
    from: string
    to: string
    value: number
}

interface Particle {
    x: number
    y: number
    t: number  // 0..1 progress along path
    speed: number
    edgeIndex: number
    active: boolean
}

export class SankeyFlow {
    container: PIXI.Container
    private nodesContainer: PIXI.Container
    private edgesContainer: PIXI.Container
    private particlesContainer: PIXI.Container
    private nodes: Map<string, FlowNode> = new Map()
    private edges: FlowEdge[] = []
    private nodeGraphics: Map<string, PIXI.Graphics> = new Map()
    private edgePaths: { from: FlowNode; to: FlowNode; value: number }[] = []
    private particles: Particle[] = []
    private particlePool: PIXI.Graphics[] = []
    private width: number
    private height: number

    constructor(width: number, height: number) {
        this.width = width
        this.height = height
        this.container = new PIXI.Container()

        this.edgesContainer = new PIXI.Container()
        this.nodesContainer = new PIXI.Container()
        this.particlesContainer = new PIXI.Container()

        this.container.addChild(this.edgesContainer)
        this.container.addChild(this.particlesContainer)
        this.container.addChild(this.nodesContainer)

        // Pre-allocate particle pool
        for (let i = 0; i < 200; i++) {
            const p = new PIXI.Graphics()
            p.beginFill(0xffffff, 0.8)
            p.drawCircle(0, 0, 2)
            p.endFill()
            p.visible = false
            this.particlePool.push(p)
            this.particlesContainer.addChild(p)
        }
    }

    update(
        nodes: { id: string; label: string; weight: number; weight_change_1d?: number }[],
        edges: { from: string; to: string; value: number }[],
        dt: number
    ) {
        // Update node positions (layout)
        this.layoutNodes(nodes)

        // Store edges
        this.edges = edges

        // Render nodes
        this.renderNodes()

        // Render edges
        this.renderEdges()

        // Update particles
        this.updateParticles(dt)
    }

    private layoutNodes(nodes: { id: string; label: string; weight: number; weight_change_1d?: number }[]) {
        const padding = 20
        const nodeWidth = 100
        const nodeHeight = 40
        const spacing = 15

        // Sort by weight
        const sorted = [...nodes].sort((a, b) => b.weight - a.weight)

        // Layout vertically
        let y = padding
        sorted.forEach((node, i) => {
            const flowNode: FlowNode = {
                ...node,
                x: padding,
                y,
                width: nodeWidth,
                height: nodeHeight,
            }
            this.nodes.set(node.id, flowNode)
            y += nodeHeight + spacing
        })
    }

    private renderNodes() {
        // Clear existing
        this.nodesContainer.removeChildren()
        this.nodeGraphics.clear()

        this.nodes.forEach((node, id) => {
            const g = new PIXI.Graphics()

            // Background
            const color = getSectorColor(node.label)
            g.beginFill(color, 0.3)
            g.lineStyle(1, color, 0.8)
            g.drawRoundedRect(0, 0, node.width, node.height, 4)
            g.endFill()

            // Weight bar
            const barWidth = node.width * Math.min(node.weight * 3, 1)  // Scale for visibility
            g.beginFill(color, 0.6)
            g.drawRoundedRect(2, node.height - 8, barWidth - 4, 6, 2)
            g.endFill()

            g.position.set(node.x, node.y)

            // Label
            const text = new PIXI.Text(node.label, {
                fontFamily: 'Inter, sans-serif',
                fontSize: 11,
                fill: theme.text.primary,
            })
            text.position.set(6, 6)
            g.addChild(text)

            // Weight text
            const weightText = new PIXI.Text(`${(node.weight * 100).toFixed(1)}%`, {
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: 10,
                fill: theme.text.secondary,
            })
            weightText.position.set(6, 22)
            g.addChild(weightText)

            this.nodesContainer.addChild(g)
            this.nodeGraphics.set(id, g)
        })
    }

    private renderEdges() {
        this.edgesContainer.removeChildren()
        this.edgePaths = []

        const g = new PIXI.Graphics()

        this.edges.forEach(edge => {
            const fromNode = this.nodes.get(edge.from)
            const toNode = this.nodes.get(edge.to)

            if (!fromNode || !toNode) return

            this.edgePaths.push({ from: fromNode, to: toNode, value: edge.value })

            const fromX = fromNode.x + fromNode.width
            const fromY = fromNode.y + fromNode.height / 2
            const toX = toNode.x
            const toY = toNode.y + toNode.height / 2

            const cpOffset = (toX - fromX) * 0.5

            g.lineStyle(Math.max(1, edge.value * 20), getSectorColor(fromNode.label), 0.3)
            g.moveTo(fromX, fromY)
            g.bezierCurveTo(
                fromX + cpOffset, fromY,
                toX - cpOffset, toY,
                toX, toY
            )
        })

        this.edgesContainer.addChild(g)
    }

    private updateParticles(dt: number) {
        const settings = perfMonitor.getSettings()
        if (!settings.enableParticles || this.edgePaths.length === 0) {
            this.particles = []
            this.particlePool.forEach(p => p.visible = false)
            return
        }

        // Spawn new particles
        const spawnRate = 0.1 * settings.particleDensity
        if (Math.random() < spawnRate && this.particles.length < 100) {
            const edgeIndex = Math.floor(Math.random() * this.edgePaths.length)
            this.particles.push({
                x: 0,
                y: 0,
                t: 0,
                speed: 0.3 + Math.random() * 0.3,
                edgeIndex,
                active: true,
            })
        }

        // Update particles
        let activeCount = 0
        this.particles.forEach((particle, i) => {
            if (!particle.active) return

            particle.t += particle.speed * dt

            if (particle.t >= 1) {
                particle.active = false
                if (this.particlePool[i]) {
                    this.particlePool[i].visible = false
                }
                return
            }

            const edge = this.edgePaths[particle.edgeIndex]
            if (!edge) return

            // Bezier interpolation
            const fromX = edge.from.x + edge.from.width
            const fromY = edge.from.y + edge.from.height / 2
            const toX = edge.to.x
            const toY = edge.to.y + edge.to.height / 2
            const cpOffset = (toX - fromX) * 0.5

            const t = particle.t
            const mt = 1 - t
            particle.x = mt * mt * mt * fromX + 3 * mt * mt * t * (fromX + cpOffset) + 3 * mt * t * t * (toX - cpOffset) + t * t * t * toX
            particle.y = mt * mt * mt * fromY + 3 * mt * mt * t * fromY + 3 * mt * t * t * toY + t * t * t * toY

            if (this.particlePool[i]) {
                this.particlePool[i].position.set(particle.x, particle.y)
                this.particlePool[i].visible = true
                this.particlePool[i].tint = getSectorColor(edge.from.label)
            }

            activeCount++
        })

        // Cleanup inactive
        this.particles = this.particles.filter(p => p.active)

        perfMonitor.setParticleCount(activeCount)
    }

    resize(width: number, height: number) {
        this.width = width
        this.height = height
    }
}
