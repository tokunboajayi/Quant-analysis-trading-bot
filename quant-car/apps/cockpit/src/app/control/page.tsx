'use client'
/**
 * Control Page - Start/Stop/Monitor the RiskFusion bot
 * Includes full portfolio management capabilities
 */
import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import Panel from '@/components/Panel'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8005'

// ============ Types ============

interface BotStatus {
    status: 'stopped' | 'starting' | 'running' | 'stopping' | 'error'
    mode: 'paper' | 'live'
    started_at: string | null
    uptime_seconds: number | null
    last_output: string
    error_message: string | null
}

interface Position {
    symbol: string
    qty: number
    market_value: number
    cost_basis: number
    unrealized_pl: number
    unrealized_plpc: number
    current_price: number
    avg_entry_price: number
    side: string
    pct_of_portfolio: number
}

interface PortfolioSummary {
    equity: number
    cash: number
    buying_power: number
    positions_count: number
    day_pl: number
    day_pl_pct: number
    total_pl: number
    total_pl_pct: number
}

interface Recommendation {
    type: string
    symbol: string | null
    reason: string
    priority: string
    suggested_action: string
}

interface Order {
    id: string
    symbol: string
    side: string
    qty: number | null
    notional: number | null
    status: string
    created_at: string
    filled_qty: number | null
    filled_avg_price: number | null
}

// ============ Component ============

export default function ControlPage() {
    // Bot state
    const [botStatus, setBotStatus] = useState<BotStatus | null>(null)
    const [loading, setLoading] = useState(true)
    const [actionLoading, setActionLoading] = useState(false)
    const [selectedMode, setSelectedMode] = useState<'paper' | 'live'>('paper')

    // Portfolio state
    const [positions, setPositions] = useState<Position[]>([])
    const [summary, setSummary] = useState<PortfolioSummary | null>(null)
    const [recommendations, setRecommendations] = useState<Recommendation[]>([])
    const [orders, setOrders] = useState<Order[]>([])
    const [portfolioLoading, setPortfolioLoading] = useState(true)

    // UI state
    const [activeTab, setActiveTab] = useState<'positions' | 'orders' | 'recommendations'>('positions')
    const [closingPosition, setClosingPosition] = useState<string | null>(null)

    // ============ Fetchers ============

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

    const fetchPortfolio = useCallback(async () => {
        try {
            const [posRes, sumRes, recRes, ordRes] = await Promise.all([
                fetch(`${API_BASE}/portfolio/positions`),
                fetch(`${API_BASE}/portfolio/summary`),
                fetch(`${API_BASE}/portfolio/recommendations`),
                fetch(`${API_BASE}/portfolio/orders?status=open`),
            ])

            if (posRes.ok) setPositions(await posRes.json())
            if (sumRes.ok) setSummary(await sumRes.json())
            if (recRes.ok) setRecommendations(await recRes.json())
            if (ordRes.ok) setOrders(await ordRes.json())
        } catch (e) {
            console.error('Failed to fetch portfolio:', e)
        } finally {
            setPortfolioLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchStatus()
        fetchPortfolio()
        const statusInterval = setInterval(fetchStatus, 2000)
        const portfolioInterval = setInterval(fetchPortfolio, 5000)
        return () => {
            clearInterval(statusInterval)
            clearInterval(portfolioInterval)
        }
    }, [fetchStatus, fetchPortfolio])

    // ============ Actions ============

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

    const closePosition = async (symbol: string) => {
        if (!confirm(`Close entire position in ${symbol}?`)) return
        setClosingPosition(symbol)
        try {
            const res = await fetch(`${API_BASE}/portfolio/close/${symbol}`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to close position')
            await fetchPortfolio()
        } catch (e) {
            console.error('Failed to close position:', e)
            alert(`Failed to close ${symbol}: ${e}`)
        } finally {
            setClosingPosition(null)
        }
    }

    const closeAllPositions = async () => {
        if (!confirm('⚠️ LIQUIDATE ALL POSITIONS? This cannot be undone!')) return
        if (!confirm('Are you absolutely sure? Type YES to confirm.')) return
        setActionLoading(true)
        try {
            await fetch(`${API_BASE}/portfolio/close-all`, { method: 'POST' })
            await fetchPortfolio()
        } catch (e) {
            console.error('Failed to close all:', e)
            alert(`Failed: ${e}`)
        } finally {
            setActionLoading(false)
        }
    }

    const cancelAllOrders = async () => {
        if (!confirm('Cancel all pending orders?')) return
        setActionLoading(true)
        try {
            await fetch(`${API_BASE}/portfolio/cancel-orders`, { method: 'POST' })
            await fetchPortfolio()
        } catch (e) {
            console.error('Failed to cancel orders:', e)
        } finally {
            setActionLoading(false)
        }
    }

    // ============ Helpers ============

    const formatUptime = (seconds: number) => {
        const h = Math.floor(seconds / 3600)
        const m = Math.floor((seconds % 3600) / 60)
        const s = seconds % 60
        return `${h}h ${m}m ${s}s`
    }

    const formatMoney = (val: number) => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)
    }

    const formatPct = (val: number) => `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`

    const plColor = (val: number) => val >= 0 ? 'text-green-400' : 'text-red-400'

    const statusColors: Record<string, string> = {
        stopped: 'bg-gray-600',
        starting: 'bg-yellow-500 animate-pulse',
        running: 'bg-green-500',
        stopping: 'bg-yellow-500 animate-pulse',
        error: 'bg-red-500',
    }

    const priorityColors: Record<string, string> = {
        high: 'bg-red-500/20 border-red-500 text-red-300',
        medium: 'bg-yellow-500/20 border-yellow-500 text-yellow-300',
        low: 'bg-blue-500/20 border-blue-500 text-blue-300',
    }

    // ============ Render ============

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
            <div className="p-6 max-w-7xl mx-auto space-y-6">
                <h1 className="text-2xl font-bold">Bot Control Center</h1>
                <p className="text-[var(--color-text-muted)]">
                    Start, stop, and monitor the RiskFusion trading bot. Full portfolio control.
                </p>

                {/* Portfolio Summary Strip */}
                {summary && (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                        <div className="bg-[var(--panel-bg)] rounded-lg p-4 border border-[var(--panel-border)]">
                            <div className="text-xs text-[var(--color-text-muted)]">Equity</div>
                            <div className="text-xl font-bold">{formatMoney(summary.equity)}</div>
                        </div>
                        <div className="bg-[var(--panel-bg)] rounded-lg p-4 border border-[var(--panel-border)]">
                            <div className="text-xs text-[var(--color-text-muted)]">Cash</div>
                            <div className="text-xl font-bold">{formatMoney(summary.cash)}</div>
                        </div>
                        <div className="bg-[var(--panel-bg)] rounded-lg p-4 border border-[var(--panel-border)]">
                            <div className="text-xs text-[var(--color-text-muted)]">Day P&L</div>
                            <div className={`text-xl font-bold ${plColor(summary.day_pl)}`}>
                                {formatMoney(summary.day_pl)} ({formatPct(summary.day_pl_pct)})
                            </div>
                        </div>
                        <div className="bg-[var(--panel-bg)] rounded-lg p-4 border border-[var(--panel-border)]">
                            <div className="text-xs text-[var(--color-text-muted)]">Total P&L</div>
                            <div className={`text-xl font-bold ${plColor(summary.total_pl)}`}>
                                {formatMoney(summary.total_pl)} ({formatPct(summary.total_pl_pct)})
                            </div>
                        </div>
                        <div className="bg-[var(--panel-bg)] rounded-lg p-4 border border-[var(--panel-border)]">
                            <div className="text-xs text-[var(--color-text-muted)]">Positions</div>
                            <div className="text-xl font-bold">{summary.positions_count}</div>
                        </div>
                        <div className="bg-[var(--panel-bg)] rounded-lg p-4 border border-[var(--panel-border)]">
                            <div className="text-xs text-[var(--color-text-muted)]">Buying Power</div>
                            <div className="text-xl font-bold">{formatMoney(summary.buying_power)}</div>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column - Bot Controls */}
                    <div className="space-y-6">
                        {/* Status Card */}
                        <Panel title="BOT STATUS">
                            {loading ? (
                                <div className="text-[var(--color-text-muted)]">Loading...</div>
                            ) : botStatus ? (
                                <div className="space-y-4">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-3 h-3 rounded-full ${statusColors[botStatus.status]}`} />
                                        <span className="text-lg font-semibold uppercase">{botStatus.status}</span>
                                        <span className="text-sm text-[var(--color-text-muted)]">
                                            Mode: <span className={botStatus.mode === 'live' ? 'text-red-400' : 'text-green-400'}>{botStatus.mode.toUpperCase()}</span>
                                        </span>
                                    </div>
                                    {botStatus.uptime_seconds !== null && (
                                        <div className="text-sm text-[var(--color-text-muted)]">
                                            Uptime: <span className="font-mono">{formatUptime(botStatus.uptime_seconds)}</span>
                                        </div>
                                    )}
                                    {botStatus.error_message && (
                                        <div className="bg-red-900/30 border border-red-700 rounded p-3 text-sm text-red-300">
                                            {botStatus.error_message}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-[var(--color-text-muted)]">Unable to connect to API</div>
                            )}
                        </Panel>

                        {/* Control Panel */}
                        <Panel title="BOT CONTROLS">
                            <div className="space-y-4">
                                <div className="flex items-center gap-4">
                                    <span className="text-sm text-[var(--color-text-muted)]">Mode:</span>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setSelectedMode('paper')}
                                            className={`px-3 py-1.5 rounded text-xs font-medium transition ${selectedMode === 'paper' ? 'bg-green-600 text-white' : 'bg-[var(--card-bg)] text-[var(--color-text-muted)]'}`}
                                        >
                                            Paper
                                        </button>
                                        <button
                                            onClick={() => setSelectedMode('live')}
                                            className={`px-3 py-1.5 rounded text-xs font-medium transition ${selectedMode === 'live' ? 'bg-red-600 text-white' : 'bg-[var(--card-bg)] text-[var(--color-text-muted)]'}`}
                                        >
                                            Live
                                        </button>
                                    </div>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {botStatus?.status === 'stopped' || botStatus?.status === 'error' ? (
                                        <>
                                            <button onClick={startBot} disabled={actionLoading} className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded text-sm font-medium">
                                                ▶ Start
                                            </button>
                                            <button onClick={runOnce} disabled={actionLoading} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded text-sm font-medium">
                                                ⚡ Run Once
                                            </button>
                                        </>
                                    ) : (
                                        <button onClick={stopBot} disabled={actionLoading || botStatus?.status === 'stopping'} className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 rounded text-sm font-medium">
                                            ⏹ Stop
                                        </button>
                                    )}
                                </div>
                            </div>
                        </Panel>

                        {/* Quick Actions */}
                        <Panel title="PORTFOLIO ACTIONS">
                            <div className="space-y-3">
                                <button onClick={cancelAllOrders} disabled={actionLoading} className="w-full px-4 py-2 bg-yellow-600/20 border border-yellow-600 hover:bg-yellow-600/40 disabled:opacity-50 rounded text-sm font-medium text-yellow-300">
                                    Cancel All Orders ({orders.length} open)
                                </button>
                                <button onClick={closeAllPositions} disabled={actionLoading} className="w-full px-4 py-2 bg-red-600/20 border border-red-600 hover:bg-red-600/40 disabled:opacity-50 rounded text-sm font-medium text-red-300">
                                    ⚠ Liquidate All Positions
                                </button>
                            </div>
                        </Panel>
                    </div>

                    {/* Right Column - Portfolio Management */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Tab Navigation */}
                        <div className="flex gap-2 border-b border-[var(--panel-border)] pb-2">
                            {(['positions', 'orders', 'recommendations'] as const).map(tab => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-4 py-2 rounded-t text-sm font-medium transition ${activeTab === tab ? 'bg-[var(--panel-bg)] text-white' : 'text-[var(--color-text-muted)] hover:text-white'}`}
                                >
                                    {tab === 'positions' && `Positions (${positions.length})`}
                                    {tab === 'orders' && `Orders (${orders.length})`}
                                    {tab === 'recommendations' && `AI Insights (${recommendations.length})`}
                                </button>
                            ))}
                        </div>

                        {/* Positions Tab */}
                        {activeTab === 'positions' && (
                            <Panel title="POSITIONS">
                                {portfolioLoading ? (
                                    <div className="text-[var(--color-text-muted)]">Loading positions...</div>
                                ) : positions.length === 0 ? (
                                    <div className="text-[var(--color-text-muted)]">No open positions</div>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="text-left text-[var(--color-text-muted)] border-b border-[var(--panel-border)]">
                                                    <th className="pb-2">Symbol</th>
                                                    <th className="pb-2 text-right">Qty</th>
                                                    <th className="pb-2 text-right">Value</th>
                                                    <th className="pb-2 text-right">P&L</th>
                                                    <th className="pb-2 text-right">%</th>
                                                    <th className="pb-2 text-right">Weight</th>
                                                    <th className="pb-2"></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {positions.map(pos => (
                                                    <tr key={pos.symbol} className="border-b border-[var(--panel-border)]/50 hover:bg-white/5">
                                                        <td className="py-2 font-medium">{pos.symbol}</td>
                                                        <td className="py-2 text-right font-mono">{pos.qty.toFixed(2)}</td>
                                                        <td className="py-2 text-right">{formatMoney(pos.market_value)}</td>
                                                        <td className={`py-2 text-right ${plColor(pos.unrealized_pl)}`}>
                                                            {formatMoney(pos.unrealized_pl)}
                                                        </td>
                                                        <td className={`py-2 text-right ${plColor(pos.unrealized_plpc)}`}>
                                                            {formatPct(pos.unrealized_plpc)}
                                                        </td>
                                                        <td className="py-2 text-right text-[var(--color-text-muted)]">
                                                            {pos.pct_of_portfolio.toFixed(1)}%
                                                        </td>
                                                        <td className="py-2 text-right">
                                                            <button
                                                                onClick={() => closePosition(pos.symbol)}
                                                                disabled={closingPosition === pos.symbol}
                                                                className="px-2 py-1 bg-red-600/20 border border-red-600 hover:bg-red-600/40 disabled:opacity-50 rounded text-xs text-red-300"
                                                            >
                                                                {closingPosition === pos.symbol ? '...' : 'Close'}
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </Panel>
                        )}

                        {/* Orders Tab */}
                        {activeTab === 'orders' && (
                            <Panel title="OPEN ORDERS">
                                {orders.length === 0 ? (
                                    <div className="text-[var(--color-text-muted)]">No open orders</div>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="text-left text-[var(--color-text-muted)] border-b border-[var(--panel-border)]">
                                                    <th className="pb-2">Symbol</th>
                                                    <th className="pb-2">Side</th>
                                                    <th className="pb-2 text-right">Qty/Notional</th>
                                                    <th className="pb-2">Status</th>
                                                    <th className="pb-2">Time</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {orders.map(order => (
                                                    <tr key={order.id} className="border-b border-[var(--panel-border)]/50">
                                                        <td className="py-2 font-medium">{order.symbol}</td>
                                                        <td className={`py-2 ${order.side === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                                                            {order.side.toUpperCase()}
                                                        </td>
                                                        <td className="py-2 text-right font-mono">
                                                            {order.qty ? order.qty : order.notional ? formatMoney(order.notional) : '-'}
                                                        </td>
                                                        <td className="py-2">{order.status}</td>
                                                        <td className="py-2 text-[var(--color-text-muted)]">
                                                            {new Date(order.created_at).toLocaleTimeString()}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </Panel>
                        )}

                        {/* Recommendations Tab */}
                        {activeTab === 'recommendations' && (
                            <Panel title="AI RECOMMENDATIONS">
                                {recommendations.length === 0 ? (
                                    <div className="text-[var(--color-text-muted)]">No recommendations at this time. Portfolio looks healthy!</div>
                                ) : (
                                    <div className="space-y-3">
                                        {recommendations.map((rec, idx) => (
                                            <div key={idx} className={`p-4 rounded border ${priorityColors[rec.priority]}`}>
                                                <div className="flex items-start gap-3">
                                                    <div className="flex-1">
                                                        <div className="font-medium">
                                                            {rec.symbol && <span className="font-bold">{rec.symbol}: </span>}
                                                            {rec.reason}
                                                        </div>
                                                        <div className="text-sm mt-1 opacity-80">
                                                            💡 {rec.suggested_action}
                                                        </div>
                                                    </div>
                                                    <div className="text-xs uppercase font-bold opacity-60">{rec.priority}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </Panel>
                        )}

                        {/* Console Output */}
                        <Panel title="CONSOLE OUTPUT">
                            <div className="bg-black rounded p-4 h-48 overflow-auto font-mono text-xs text-green-400 whitespace-pre-wrap">
                                {botStatus?.last_output || 'No output yet. Start the bot to see logs.'}
                            </div>
                        </Panel>
                    </div>
                </div>
            </div>
        </div>
    )
}
