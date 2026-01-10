/**
 * Telemetry Store - Simplified version using HTTP polling
 */

const API_BASE = 'http://localhost:8000'

// Types inline to avoid import issues
interface TelemetryFrame {
    schema_version: string
    ts_utc: string
    trading_date?: string
    execution_mode?: string
    pipeline_status?: string
    pipeline_stage_status?: Record<string, string>
    pipeline_latency_ms?: Record<string, number>
    speed_alpha?: { value: number; raw?: number; unit?: string }
    rpm_turnover?: { value: number; raw?: number; unit?: string }
    traction_risk?: { value: number; raw?: number; unit?: string }
    brake_var_pressure?: { value: number; raw?: number; unit?: string }
    regime_state?: string
    regime_confidence?: number
    warnings?: Array<{ code: string; severity: number; message?: string }>
    hazards?: Array<{
        id: string
        ticker: string
        direction: string
        risk_prob: number
        eta_seconds: number
        title?: string
    }>
    portfolio_flow?: {
        nodes: Array<{ id: string; label: string; weight: number; weight_change_1d?: number }>
        edges: Array<{ from: string; to: string; value: number }>
    }
    top_weight_changes?: Array<{
        ticker: string
        delta: number
        weight_prev?: number
        weight_new?: number
        reason_codes?: string[]
    }>
    models?: Array<{ name: string; status: string; health: number; stage?: string }>
    providers?: Array<{ name: string; status: string; latency_ms?: number }>
    execution?: {
        positions_count?: number
        orders_open?: number
        fills_1d?: number
        rejects_1d?: number
    }
    pnl?: { equity: number; drawdown: number; return_1d?: number }
    run_id?: string
}

interface TelemetryState {
    frame: TelemetryFrame | null
    prevFrame: TelemetryFrame | null
    connected: boolean
    error: string | null
    wsRate: number
}

type Listener = () => void

class TelemetryStore {
    private state: TelemetryState = {
        frame: null,
        prevFrame: null,
        connected: false,
        error: null,
        wsRate: 0,
    }

    private listeners = new Set<Listener>()
    private pollInterval: ReturnType<typeof setInterval> | null = null
    private rateInterval: ReturnType<typeof setInterval> | null = null
    private msgCount = 0
    private lastTs = ''
    private isPolling = false

    subscribe = (listener: Listener): (() => void) => {
        this.listeners.add(listener)
        return () => this.listeners.delete(listener)
    }

    getSnapshot = (): TelemetryState => this.state

    private notify() {
        this.listeners.forEach(l => l())
    }

    connect() {
        if (this.pollInterval) return // Already connected

        this.fetchLatest() // Immediate first fetch
        this.pollInterval = setInterval(() => this.fetchLatest(), 500)
        this.rateInterval = setInterval(() => {
            this.state = { ...this.state, wsRate: this.msgCount }
            this.msgCount = 0
            this.notify()
        }, 1000)
    }

    disconnect() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval)
            this.pollInterval = null
        }
        if (this.rateInterval) {
            clearInterval(this.rateInterval)
            this.rateInterval = null
        }
        this.state = { ...this.state, connected: false }
        this.notify()
    }

    private async fetchLatest() {
        if (this.isPolling) return
        this.isPolling = true

        try {
            const res = await fetch(`${API_BASE}/telemetry/latest`)
            if (!res.ok) throw new Error('API error')

            const frame = await res.json() as TelemetryFrame

            // Skip duplicate frames
            if (frame.ts_utc === this.lastTs) {
                this.isPolling = false
                return
            }
            this.lastTs = frame.ts_utc

            // Update state
            this.state = {
                prevFrame: this.state.frame,
                frame,
                connected: true,
                error: null,
                wsRate: this.state.wsRate,
            }
            this.msgCount++
            this.notify()

        } catch (e) {
            if (this.state.connected) {
                this.state = { ...this.state, connected: false, error: 'Connection error' }
                this.notify()
            }
        } finally {
            this.isPolling = false
        }
    }
}

// Singleton
export const telemetryStore = new TelemetryStore()

// React hook
import { useSyncExternalStore } from 'react'

export function useTelemetry() {
    const state = useSyncExternalStore(
        telemetryStore.subscribe,
        telemetryStore.getSnapshot,
        telemetryStore.getSnapshot
    )

    return {
        ...state,
        connect: () => telemetryStore.connect(),
        disconnect: () => telemetryStore.disconnect(),
    }
}

// Export type for components
export type { TelemetryFrame }
