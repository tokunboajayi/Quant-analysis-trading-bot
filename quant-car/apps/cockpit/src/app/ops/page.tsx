'use client'
/**
 * Ops Page - System health monitoring with real data
 */
import { useEffect } from 'react'
import Link from 'next/link'
import { useTelemetry } from '@/data/store'

export default function OpsPage() {
    const { frame, connected, wsRate, connect } = useTelemetry()

    useEffect(() => {
        connect()
    }, [connect])

    const models = frame?.models || []
    const providers = frame?.providers || []
    const stages = frame?.pipeline_stage_status || {}

    const formatDate = (d?: string) => {
        if (!d) return '--'
        if (d.length === 8) return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
        return d
    }

    return (
        <div className="h-screen flex flex-col bg-[#0a0a0f] text-white">
            {/* Top Bar */}
            <div className="h-12 flex items-center px-4 border-b border-[#1f1f2e] bg-[#12121a]">
                <span className="font-bold text-lg">Ops Console</span>
                <div className="flex items-center gap-2 ml-4">
                    <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`} />
                    <span className="text-xs text-gray-400">{connected ? `${wsRate} msg/s` : 'Disconnected'}</span>
                </div>
                <div className="flex-1" />
                <nav className="flex gap-1">
                    <Link href="/quant" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Quant</Link>
                    <Link href="/research" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Research</Link>
                    <Link href="/compare" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Compare</Link>
                    <Link href="/incidents" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Incidents</Link>
                    <Link href="/ops" className="text-xs px-3 py-1.5 bg-blue-600/40 rounded font-medium">Ops</Link>
                </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 grid grid-cols-3 gap-4 p-4 overflow-auto">
                {/* Pipeline Status */}
                <div className="bg-[#12121a] rounded-lg p-4 border border-[#1f1f2e]">
                    <h3 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
                        <span>⚙️</span> PIPELINE STAGES
                    </h3>
                    <div className="space-y-2">
                        {Object.entries(stages).map(([stage, status]) => {
                            const statusStr = String(status)
                            return (
                                <div key={stage} className="flex items-center justify-between bg-[#0c0c12] p-2 rounded">
                                    <span className="text-sm text-gray-300 capitalize">{stage.replace(/_/g, ' ')}</span>
                                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${statusStr === 'ok' ? 'bg-green-900/50 text-green-300' :
                                            statusStr === 'running' ? 'bg-blue-900/50 text-blue-300' :
                                                statusStr === 'skipped' ? 'bg-gray-800 text-gray-400' :
                                                    'bg-red-900/50 text-red-300'
                                        }`}>
                                        {statusStr.toUpperCase()}
                                    </span>
                                </div>
                            )
                        })}
                    </div>
                </div>

                {/* Models Health */}
                <div className="bg-[#12121a] rounded-lg p-4 border border-[#1f1f2e]">
                    <h3 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
                        <span>🧠</span> MODELS
                    </h3>
                    <div className="space-y-3">
                        {models.map((m, i) => (
                            <div key={i} className="bg-[#0c0c12] p-3 rounded">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-semibold capitalize">{m.name}</span>
                                    <span className={`w-2 h-2 rounded-full ${m.status === 'ok' ? 'bg-green-500' :
                                            m.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                                        }`} />
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="flex-1 h-2 bg-[#1a1a24] rounded-full overflow-hidden">
                                        <div
                                            className={`h-full transition-all ${m.health > 0.8 ? 'bg-gradient-to-r from-green-600 to-green-400' :
                                                    m.health > 0.5 ? 'bg-gradient-to-r from-yellow-600 to-yellow-400' :
                                                        'bg-gradient-to-r from-red-600 to-red-400'
                                                }`}
                                            style={{ width: `${m.health * 100}%` }}
                                        />
                                    </div>
                                    <span className="text-xs text-gray-400 w-10 text-right">
                                        {(m.health * 100).toFixed(0)}%
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Providers Health */}
                <div className="bg-[#12121a] rounded-lg p-4 border border-[#1f1f2e]">
                    <h3 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
                        <span>🔌</span> PROVIDERS
                    </h3>
                    <div className="space-y-3">
                        {providers.map((p, i) => (
                            <div key={i} className="bg-[#0c0c12] p-3 rounded">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-semibold capitalize">{p.name}</span>
                                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${p.status === 'up' ? 'bg-green-900/50 text-green-300' :
                                            p.status === 'degraded' ? 'bg-yellow-900/50 text-yellow-300' :
                                                'bg-red-900/50 text-red-300'
                                        }`}>
                                        {p.status?.toUpperCase()}
                                    </span>
                                </div>
                                {p.latency_ms && (
                                    <div className="text-xs text-gray-500 flex items-center gap-2">
                                        <span>Latency:</span>
                                        <span className={`font-mono ${p.latency_ms > 500 ? 'text-yellow-400' :
                                                p.latency_ms > 200 ? 'text-gray-400' : 'text-green-400'
                                            }`}>
                                            {p.latency_ms}ms
                                        </span>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* System Info */}
                <div className="col-span-3 bg-[#12121a] rounded-lg p-4 border border-[#1f1f2e]">
                    <h3 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
                        <span>📊</span> SYSTEM INFO
                    </h3>
                    <div className="grid grid-cols-5 gap-4">
                        <div className="bg-[#0c0c12] p-4 rounded text-center">
                            <div className="text-2xl font-mono text-blue-400">{formatDate(frame?.trading_date)}</div>
                            <div className="text-xs text-gray-500 mt-1">Trading Date</div>
                        </div>
                        <div className="bg-[#0c0c12] p-4 rounded text-center">
                            <div className={`text-2xl font-mono ${frame?.execution_mode === 'LIVE' ? 'text-red-400' : 'text-green-400'
                                }`}>
                                {frame?.execution_mode || '--'}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">Mode</div>
                        </div>
                        <div className="bg-[#0c0c12] p-4 rounded text-center">
                            <div className="text-2xl font-mono text-yellow-400">
                                {frame?.execution?.positions_count || 0}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">Positions</div>
                        </div>
                        <div className="bg-[#0c0c12] p-4 rounded text-center">
                            <div className="text-2xl font-mono text-purple-400">
                                ${frame?.pnl?.equity?.toLocaleString() || '--'}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">Equity</div>
                        </div>
                        <div className="bg-[#0c0c12] p-4 rounded text-center">
                            <div className={`text-2xl font-mono ${wsRate > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {wsRate}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">Msg/s</div>
                        </div>
                    </div>
                </div>

                {/* Run Info */}
                <div className="col-span-3 bg-[#12121a] rounded-lg p-4 border border-[#1f1f2e]">
                    <h3 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
                        <span>🏷️</span> CURRENT RUN
                    </h3>
                    <div className="font-mono text-sm text-gray-400">
                        <span className="text-gray-500">Run ID:</span> {frame?.run_id || '--'}
                    </div>
                </div>
            </div>
        </div>
    )
}
