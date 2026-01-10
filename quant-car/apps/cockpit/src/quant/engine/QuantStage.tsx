'use client'
/**
 * QuantStage - Main Pixi renderer with labeled visuals
 */
import { useEffect, useRef } from 'react'
import * as PIXI from 'pixi.js'
import type { TelemetryFrame } from '@/data/store'
import { theme } from './theme'
import { SankeyFlow } from '../visuals/SankeyFlow'
import { SignalPipeline } from '../visuals/SignalPipeline'
import { EquityRibbon } from '../visuals/EquityRibbon'
import { HazardTape } from '../visuals/HazardTape'
import { RiskHeatmap } from '../visuals/RiskHeatmap'
import { RegimeRiver } from '../visuals/RegimeRiver'
import { Waterfall } from '../visuals/Waterfall'

interface QuantStageProps {
    frame: TelemetryFrame | null
    prevFrame: TelemetryFrame | null
    wsRate: number
}

// Helper to create section labels
function createLabel(text: string, x: number, y: number): PIXI.Text {
    const label = new PIXI.Text(text, {
        fontSize: 11,
        fontWeight: 'bold',
        fill: 0x6b7280, // gray-500
        fontFamily: 'system-ui, sans-serif',
    })
    label.position.set(x, y)
    return label
}

// Helper to create sublabel/description
function createSubLabel(text: string, x: number, y: number): PIXI.Text {
    const label = new PIXI.Text(text, {
        fontSize: 9,
        fill: 0x4b5563, // gray-600
        fontFamily: 'system-ui, sans-serif',
    })
    label.position.set(x, y)
    return label
}

export default function QuantStage({ frame, prevFrame, wsRate }: QuantStageProps) {
    const containerRef = useRef<HTMLDivElement>(null)
    const appRef = useRef<PIXI.Application | null>(null)
    const visualsRef = useRef<{
        sankey: SankeyFlow | null
        pipeline: SignalPipeline | null
        equity: EquityRibbon | null
        hazards: HazardTape | null
        heatmap: RiskHeatmap | null
        regime: RegimeRiver | null
        waterfall: Waterfall | null
    }>({
        sankey: null, pipeline: null, equity: null,
        hazards: null, heatmap: null, regime: null, waterfall: null
    })
    const frameRef = useRef<TelemetryFrame | null>(null)
    const lastFrameTime = useRef(performance.now())

    useEffect(() => {
        if (!containerRef.current) return

        const width = containerRef.current.clientWidth || 800
        const height = containerRef.current.clientHeight || 600

        const app = new PIXI.Application({
            width, height,
            backgroundColor: theme.bg.primary,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
        })

        containerRef.current.appendChild(app.view as HTMLCanvasElement)
        appRef.current = app

        // Create visuals with layout
        const v = visualsRef.current
        const labelHeight = 35

        // ===== LEFT: SANKEY FLOW =====
        app.stage.addChild(createLabel('PORTFOLIO ALLOCATION', 10, 10))
        app.stage.addChild(createSubLabel('Asset weights by ticker • Size = weight %', 10, 24))
        v.sankey = new SankeyFlow(width * 0.35, height * 0.5)
        v.sankey.container.position.set(10, labelHeight + 20)
        app.stage.addChild(v.sankey.container)

        // ===== CENTER TOP: SIGNAL PIPELINE =====
        app.stage.addChild(createLabel('PIPELINE STATUS', width * 0.36, 10))
        app.stage.addChild(createSubLabel('Data processing stages • Green = OK • Yellow = Slow', width * 0.36, 24))
        v.pipeline = new SignalPipeline(width * 0.35, 70)
        v.pipeline.container.position.set(width * 0.36, labelHeight + 20)
        app.stage.addChild(v.pipeline.container)

        // ===== CENTER: WATERFALL =====
        app.stage.addChild(createLabel('WEIGHT CHANGES', width * 0.36, 130))
        app.stage.addChild(createSubLabel('Top position changes today • Green = Buy • Red = Sell', width * 0.36, 144))
        v.waterfall = new Waterfall(width * 0.35, 120)
        v.waterfall.container.position.set(width * 0.36, 160)
        app.stage.addChild(v.waterfall.container)

        // ===== RIGHT: RISK HEATMAP =====
        app.stage.addChild(createLabel('RISK CONCENTRATION', width * 0.72, 10))
        app.stage.addChild(createSubLabel('Top holdings risk intensity • Darker = Higher exposure', width * 0.72, 24))
        v.heatmap = new RiskHeatmap(width * 0.27, height * 0.32)
        v.heatmap.container.position.set(width * 0.72, labelHeight + 20)
        app.stage.addChild(v.heatmap.container)

        // ===== BOTTOM LEFT: EQUITY RIBBON =====
        const bottomY = height * 0.55
        app.stage.addChild(createLabel('EQUITY CURVE', 10, bottomY - 15))
        app.stage.addChild(createSubLabel('Portfolio value over time • Red shading = Drawdown', 10, bottomY - 2))
        v.equity = new EquityRibbon(width * 0.48, height * 0.35)
        v.equity.container.position.set(10, bottomY + 15)
        app.stage.addChild(v.equity.container)

        // ===== BOTTOM CENTER: REGIME RIVER =====
        app.stage.addChild(createLabel('MARKET REGIME', width * 0.5, bottomY - 15))
        app.stage.addChild(createSubLabel('Clear ☀️ | Rain 🌧️ | Storm ⛈️ market conditions', width * 0.5, bottomY - 2))
        v.regime = new RegimeRiver(width * 0.48, height * 0.08)
        v.regime.container.position.set(width * 0.5, bottomY + 15)
        app.stage.addChild(v.regime.container)

        // ===== BOTTOM RIGHT: HAZARD TAPE =====
        app.stage.addChild(createLabel('EVENT HAZARDS', width * 0.5, bottomY + height * 0.1))
        app.stage.addChild(createSubLabel('Upcoming events affecting positions • ↑ Bullish • ↓ Bearish', width * 0.5, bottomY + height * 0.1 + 14))
        v.hazards = new HazardTape(width * 0.48, 50)
        v.hazards.container.position.set(width * 0.5, bottomY + height * 0.13 + 15)
        app.stage.addChild(v.hazards.container)

        // 60fps render loop
        app.ticker.add(() => {
            const now = performance.now()
            const dt = Math.min((now - lastFrameTime.current) / 1000, 0.1)
            lastFrameTime.current = now

            const f = frameRef.current
            if (!f) return

            v.sankey?.update(f.portfolio_flow?.nodes || [], f.portfolio_flow?.edges || [], dt)
            v.pipeline?.update(
                f.pipeline_stage_status as Record<string, 'ok' | 'running' | 'failed' | 'skipped'> || {},
                f.pipeline_latency_ms || {},
                f.warnings || [],
                dt
            )
            v.equity?.update(dt)
            v.hazards?.update(
                (f.hazards || []).map(h => ({ ...h, direction: h.direction as 'up' | 'down' | 'unknown' })),
                dt
            )
            v.heatmap?.update(f.portfolio_flow?.nodes || [], f.traction_risk?.value ?? 0.5, f.brake_var_pressure?.value ?? 0.25, dt)
            v.regime?.update(dt)
            v.waterfall?.update(computeContributions(f), dt)
        })

        const handleResize = () => {
            if (!appRef.current || !containerRef.current) return
            const w = containerRef.current.clientWidth
            const h = containerRef.current.clientHeight
            appRef.current.renderer.resize(w, h)
        }
        window.addEventListener('resize', handleResize)

        return () => {
            window.removeEventListener('resize', handleResize)
            app.destroy(true, { children: true })
        }
    }, [])

    useEffect(() => {
        if (frame) {
            frameRef.current = frame
            const equity = frame.pnl?.equity || 100000
            const drawdown = frame.pnl?.drawdown || 0
            visualsRef.current.equity?.addPoint(equity, drawdown)
            const regime = (frame.regime_state as 'clear' | 'rain' | 'storm') || 'clear'
            const confidence = frame.regime_confidence ?? 0.75
            visualsRef.current.regime?.addRegime(regime, confidence)
        }
    }, [frame?.ts_utc])

    return <div ref={containerRef} className="w-full h-full" style={{ minHeight: 500 }} />
}

function computeContributions(frame: TelemetryFrame) {
    const changes = frame.top_weight_changes || []
    const alpha = frame.speed_alpha?.value ?? 0.5
    return changes.slice(0, 6).map(c => ({
        label: c.ticker,
        value: c.delta * alpha * 500
    }))
}
