/**
 * SignalPipeline - Animated quant system pipeline visualization
 */
import * as PIXI from 'pixi.js'
import { theme } from '../engine/theme'

type StageStatus = 'ok' | 'running' | 'failed' | 'skipped'

interface PipelineStage {
    id: string
    label: string
    status: StageStatus
    latency?: number
}

const STAGES: { id: string; label: string }[] = [
    { id: 'ingest_prices', label: 'Prices' },
    { id: 'ingest_events', label: 'Events' },
    { id: 'build_features', label: 'Features' },
    { id: 'predict', label: 'Models' },
    { id: 'construct_portfolio', label: 'Portfolio' },
    { id: 'execute', label: 'Execution' },
    { id: 'report', label: 'Report' },
]

interface Packet {
    x: number
    progress: number  // 0..1 within current segment
    stageIndex: number
    speed: number
    active: boolean
}

export class SignalPipeline {
    container: PIXI.Container
    private nodesContainer: PIXI.Container
    private connectionsContainer: PIXI.Container
    private packetsContainer: PIXI.Container
    private stages: PipelineStage[] = []
    private stageGraphics: PIXI.Graphics[] = []
    private packets: Packet[] = []
    private packetSprites: PIXI.Graphics[] = []
    private width: number
    private height: number

    constructor(width: number, height: number) {
        this.width = width
        this.height = height
        this.container = new PIXI.Container()

        this.connectionsContainer = new PIXI.Container()
        this.packetsContainer = new PIXI.Container()
        this.nodesContainer = new PIXI.Container()

        this.container.addChild(this.connectionsContainer)
        this.container.addChild(this.packetsContainer)
        this.container.addChild(this.nodesContainer)

        // Initialize stages
        this.stages = STAGES.map(s => ({ ...s, status: 'ok' as StageStatus }))

        // Pre-allocate packet sprites
        for (let i = 0; i < 50; i++) {
            const p = new PIXI.Graphics()
            p.beginFill(theme.semantic.info, 0.9)
            p.drawRoundedRect(-4, -2, 8, 4, 2)
            p.endFill()
            p.visible = false
            this.packetSprites.push(p)
            this.packetsContainer.addChild(p)
        }

        this.renderPipeline()
    }

    update(
        stageStatus: Record<string, StageStatus>,
        latencyMs: Record<string, number> | undefined,
        warnings: { code: string; severity: number }[],
        dt: number
    ) {
        // Update stage status
        this.stages.forEach(stage => {
            stage.status = stageStatus[stage.id] || 'ok'
            stage.latency = latencyMs?.[stage.id]
        })

        // Re-render nodes with updated status
        this.renderNodes()

        // Spawn packets
        this.spawnPackets(latencyMs)

        // Update packets
        this.updatePackets(dt)
    }

    private renderPipeline() {
        this.renderConnections()
        this.renderNodes()
    }

    private renderConnections() {
        this.connectionsContainer.removeChildren()

        const g = new PIXI.Graphics()
        const stageWidth = this.width / (this.stages.length + 1)
        const centerY = this.height / 2

        // Draw connecting lines
        g.lineStyle(2, theme.border.normal, 0.5)

        for (let i = 0; i < this.stages.length - 1; i++) {
            const x1 = stageWidth * (i + 1) + 25
            const x2 = stageWidth * (i + 2) - 25
            g.moveTo(x1, centerY)
            g.lineTo(x2, centerY)
        }

        this.connectionsContainer.addChild(g)
    }

    private renderNodes() {
        this.nodesContainer.removeChildren()
        this.stageGraphics = []

        const stageWidth = this.width / (this.stages.length + 1)
        const nodeSize = 50
        const centerY = this.height / 2

        this.stages.forEach((stage, i) => {
            const x = stageWidth * (i + 1)

            const g = new PIXI.Graphics()

            // Status color
            let color = theme.pipeline.ok
            let bgAlpha = 0.3
            if (stage.status === 'running') {
                color = theme.pipeline.running
                bgAlpha = 0.5
            } else if (stage.status === 'failed') {
                color = theme.pipeline.failed
                bgAlpha = 0.5
            } else if (stage.status === 'skipped') {
                color = theme.pipeline.skipped
                bgAlpha = 0.2
            }

            // Node circle
            g.beginFill(color, bgAlpha)
            g.lineStyle(2, color, 0.8)
            g.drawCircle(0, 0, nodeSize / 2)
            g.endFill()

            // Glow for running
            if (stage.status === 'running') {
                g.lineStyle(0)
                g.beginFill(color, 0.1)
                g.drawCircle(0, 0, nodeSize / 2 + 8)
                g.endFill()
            }

            g.position.set(x, centerY)

            // Label
            const label = new PIXI.Text(stage.label, {
                fontFamily: 'Inter, sans-serif',
                fontSize: 10,
                fill: theme.text.secondary,
            })
            label.anchor.set(0.5)
            label.position.set(0, nodeSize / 2 + 12)
            g.addChild(label)

            // Latency
            if (stage.latency) {
                const latencyText = new PIXI.Text(`${Math.round(stage.latency)}ms`, {
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 9,
                    fill: stage.latency > 3000 ? theme.semantic.warning : theme.text.dim,
                })
                latencyText.anchor.set(0.5)
                latencyText.position.set(0, -nodeSize / 2 - 10)
                g.addChild(latencyText)
            }

            this.nodesContainer.addChild(g)
            this.stageGraphics.push(g)
        })
    }

    private spawnPackets(latencyMs: Record<string, number> | undefined) {
        // Spawn rate based on inverse latency
        const avgLatency = latencyMs
            ? Object.values(latencyMs).reduce((a, b) => a + b, 0) / Object.values(latencyMs).length
            : 1000

        const spawnRate = Math.min(0.1, 500 / avgLatency)

        if (Math.random() < spawnRate && this.packets.length < 30) {
            this.packets.push({
                x: 0,
                progress: 0,
                stageIndex: 0,
                speed: 0.5 + Math.random() * 0.5,
                active: true,
            })
        }
    }

    private updatePackets(dt: number) {
        const stageWidth = this.width / (this.stages.length + 1)
        const centerY = this.height / 2

        this.packets.forEach((packet, i) => {
            if (!packet.active) return

            packet.progress += packet.speed * dt

            if (packet.progress >= 1) {
                packet.stageIndex++
                packet.progress = 0

                if (packet.stageIndex >= this.stages.length - 1) {
                    packet.active = false
                    if (this.packetSprites[i]) {
                        this.packetSprites[i].visible = false
                    }
                    return
                }
            }

            // Calculate position
            const fromX = stageWidth * (packet.stageIndex + 1) + 25
            const toX = stageWidth * (packet.stageIndex + 2) - 25
            packet.x = fromX + (toX - fromX) * packet.progress

            if (this.packetSprites[i]) {
                this.packetSprites[i].position.set(packet.x, centerY)
                this.packetSprites[i].visible = true
            }
        })

        // Cleanup
        this.packets = this.packets.filter(p => p.active)
    }

    resize(width: number, height: number) {
        this.width = width
        this.height = height
        this.renderPipeline()
    }
}
