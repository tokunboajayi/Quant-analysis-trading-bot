'use client'
/**
 * Control Page - Start/Stop/Monitor the RiskFusion bot
 */
import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import Panel from '@/components/Panel'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

interface BotStatus {
    status: 'stopped' | 'starting' | 'running' | 'stopping' | 'error'
    mode: 'paper' | 'live'
    started_at: string | null
    uptime_seconds: number | null
    last_output: string
    error_message: string | null
}

export default function ControlPage() {
    const [botStatus, setBotStatus] = useState<BotStatus | null>(null)
    const [loading, setLoading] = useState(true)
    const [actionLoading, setActionLoading] = useState(false)
    const [selectedMode, setSelectedMode] = useState<'paper' | 'live'>('paper')

    const fetchStatus = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/bot/status`)
            const data = await res.json()
            setBotStatus(data)
        } catch (e) {
            console.error('Failed to fetch bot status:', e)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchStatus()
        const interval = setInterval(fetchStatus, 2000)
        return () => clearInterval(interval)
    }, [fetchStatus])

    const startBot = async () => {
        setActionLoading(true)
        try {
            await fetch(`${API_BASE}/bot/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: selectedMode }),
            })
            await fetchStatus()
        } catch (e) {
            console.error('Failed to start bot:', e)
        } finally {
            setActionLoading(false)
        }
    }

    const stopBot = async () => {
        setActionLoading(true)
        try {
            await fetch(`${API_BASE}/bot/stop`, { method: 'POST' })
            await fetchStatus()
        } catch (e) {
            console.error('Failed to stop bot:', e)
        } finally {
            setActionLoading(false)
        }
    }

    const runOnce = async () => {
        setActionLoading(true)
        try {
            await fetch(`${API_BASE}/bot/run-once`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: selectedMode }),
            })
            await fetchStatus()
        } catch (e) {
            console.error('Failed to run once:', e)
        } finally {
            setActionLoading(false)
        }
    }

    const formatUptime = (seconds: number) => {
        const h = Math.floor(seconds / 3600)
        const m = Math.floor((seconds % 3600) / 60)
        const s = seconds % 60
        return `${h}h ${m}m ${s}s`
    }

    const statusColors: Record<string, string> = {
        stopped: 'bg-gray-600',
        starting: 'bg-yellow-500 animate-pulse',
        running: 'bg-green-500',
        stopping: 'bg-yellow-500 animate-pulse',
        error: 'bg-red-500',
    }

    return (
        <div className="min-h-screen bg-[var(--color-bg)] text-white">
            {/* Top Bar */}
            <div className="h-12 flex items-center px-6 border-b border-[var(--panel-border)] bg-[var(--panel-bg)]">
                <div className="font-bold text-base tracking-tight mr-6">QuantDash</div>
                <div className="flex-1" />
                <nav className="flex gap-0.5">
                    {[
                        { href: '/quant', label: 'Quant' },
                        { href: '/research', label: 'Research' },
                        { href: '/compare', label: 'Compare' },
                        { href: '/incidents', label: 'Incidents' },
                        { href: '/ops', label: 'Ops' },
                        { href: '/control', label: 'Control', active: true },
                    ].map(link => (
                        <Link
                            key={link.href}
                            href={link.href}
                            className={`text-[11px] px-3 py-1.5 rounded font-medium transition-colors ${link.active
                                    ? 'bg-[var(--color-info)]/30 text-[var(--color-info)]'
                                    : 'text-[var(--color-text-muted)] hover:bg-white/5'
                                }`}
                        >
                            {link.label}
                        </Link>
                    ))}
                </nav>
            </div>

            {/* Main Content */}
            <div className="p-6 max-w-4xl mx-auto space-y-6">
                <h1 className="text-2xl font-bold">Bot Control Center</h1>
                <p className="text-[var(--color-text-muted)]">
                    Start, stop, and monitor the RiskFusion trading bot.
                </p>

                {/* Status Card */}
                <Panel title="BOT STATUS">
                    {loading ? (
                        <div className="text-[var(--color-text-muted)]">Loading...</div>
                    ) : botStatus ? (
                        <div className="space-y-4">
                            {/* Status Badge */}
                            <div className="flex items-center gap-4">
                                <div className={`w-3 h-3 rounded-full ${statusColors[botStatus.status]}`} />
                                <span className="text-lg font-semibold uppercase">{botStatus.status}</span>
                                <span className="text-sm text-[var(--color-text-muted)]">
                                    Mode: <span className={botStatus.mode === 'live' ? 'text-red-400' : 'text-green-400'}>{botStatus.mode.toUpperCase()}</span>
                                </span>
                            </div>

                            {/* Uptime */}
                            {botStatus.uptime_seconds !== null && (
                                <div className="text-sm text-[var(--color-text-muted)]">
                                    Uptime: <span className="font-mono">{formatUptime(botStatus.uptime_seconds)}</span>
                                </div>
                            )}

                            {/* Started At */}
                            {botStatus.started_at && (
                                <div className="text-sm text-[var(--color-text-muted)]">
                                    Started: <span className="font-mono">{new Date(botStatus.started_at).toLocaleString()}</span>
                                </div>
                            )}

                            {/* Error */}
                            {botStatus.error_message && (
                                <div className="bg-red-900/30 border border-red-700 rounded p-3 text-sm text-red-300">
                                    ⚠️ {botStatus.error_message}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="text-[var(--color-text-muted)]">Unable to connect to API</div>
                    )}
                </Panel>

                {/* Control Panel */}
                <Panel title="CONTROLS">
                    <div className="space-y-4">
                        {/* Mode Selector */}
                        <div className="flex items-center gap-4">
                            <span className="text-sm text-[var(--color-text-muted)]">Trading Mode:</span>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setSelectedMode('paper')}
                                    className={`px-4 py-2 rounded text-sm font-medium transition ${selectedMode === 'paper'
                                            ? 'bg-green-600 text-white'
                                            : 'bg-[var(--card-bg)] text-[var(--color-text-muted)] hover:bg-[var(--panel-bg-hover)]'
                                        }`}
                                >
                                    📄 Paper Trading
                                </button>
                                <button
                                    onClick={() => setSelectedMode('live')}
                                    className={`px-4 py-2 rounded text-sm font-medium transition ${selectedMode === 'live'
                                            ? 'bg-red-600 text-white'
                                            : 'bg-[var(--card-bg)] text-[var(--color-text-muted)] hover:bg-[var(--panel-bg-hover)]'
                                        }`}
                                >
                                    🔴 Live Trading
                                </button>
                            </div>
                        </div>

                        {/* Live Trading Warning */}
                        {selectedMode === 'live' && (
                            <div className="bg-red-900/30 border border-red-700 rounded p-3 text-sm text-red-300">
                                ⚠️ <strong>WARNING:</strong> Live trading uses real money! Make sure you understand the risks.
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex gap-3 pt-2">
                            {botStatus?.status === 'stopped' || botStatus?.status === 'error' ? (
                                <>
                                    <button
                                        onClick={startBot}
                                        disabled={actionLoading}
                                        className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded-lg text-white font-semibold transition flex items-center gap-2"
                                    >
                                        ▶️ Start Bot
                                    </button>
                                    <button
                                        onClick={runOnce}
                                        disabled={actionLoading}
                                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-white font-semibold transition flex items-center gap-2"
                                    >
                                        ⚡ Run Once
                                    </button>
                                </>
                            ) : (
                                <button
                                    onClick={stopBot}
                                    disabled={actionLoading || botStatus?.status === 'stopping'}
                                    className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:opacity-50 rounded-lg text-white font-semibold transition flex items-center gap-2"
                                >
                                    ⏹️ Stop Bot
                                </button>
                            )}
                        </div>
                    </div>
                </Panel>

                {/* Output Console */}
                <Panel title="CONSOLE OUTPUT">
                    <div className="bg-black rounded p-4 h-64 overflow-auto font-mono text-xs text-green-400 whitespace-pre-wrap">
                        {botStatus?.last_output || 'No output yet. Start the bot to see logs.'}
                    </div>
                </Panel>

                {/* Quick Info */}
                <Panel title="QUICK GUIDE">
                    <div className="text-sm text-[var(--color-text-muted)] space-y-2">
                        <p><strong>📄 Paper Trading:</strong> Simulated trades with fake money. Safe for testing.</p>
                        <p><strong>🔴 Live Trading:</strong> Real trades with real money. Requires ALLOW_LIVE_TRADING=1 env var.</p>
                        <p><strong>▶️ Start Bot:</strong> Runs the pipeline continuously (daily at market open).</p>
                        <p><strong>⚡ Run Once:</strong> Executes a single pipeline iteration immediately.</p>
                    </div>
                </Panel>
            </div>
        </div>
    )
}
