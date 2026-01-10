'use client'
/**
 * RightPanel - Warnings, weight changes, health tables with clear labels
 */

interface WarningItem { code: string; severity: number; message?: string }
interface WeightChange { ticker: string; delta: number }
interface ModelHealth { name: string; status: string; health: number }
interface ProviderHealth { name: string; status: string; latency_ms?: number }

interface RightPanelProps {
    warnings: WarningItem[]
    weightChanges: WeightChange[]
    models: ModelHealth[]
    providers: ProviderHealth[]
}

export default function RightPanel({ warnings, weightChanges, models, providers }: RightPanelProps) {
    return (
        <div className="w-80 border-l border-[#1f1f2e] bg-[#0a0a0f] overflow-auto p-4">
            {/* Warnings Section */}
            <div className="mb-6">
                <h3 className="text-xs font-bold text-gray-400 mb-1 flex items-center gap-2">
                    <span>⚠️</span> ACTIVE WARNINGS
                </h3>
                <p className="text-[10px] text-gray-600 mb-3">System alerts requiring attention</p>
                <div className="space-y-1">
                    {warnings.length === 0 ? (
                        <div className="text-gray-600 text-xs bg-[#12121a] p-2 rounded">✓ No active warnings</div>
                    ) : (
                        warnings.map((w, i) => (
                            <div key={i} className="flex items-center gap-2 bg-[#1a1a24] p-2 rounded text-xs">
                                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${w.severity === 3 ? 'bg-red-500' :
                                        w.severity === 2 ? 'bg-yellow-500' : 'bg-blue-500'
                                    }`} />
                                <div className="flex-1 min-w-0">
                                    <div className="text-gray-300 font-medium">{w.code}</div>
                                    {w.message && <div className="text-gray-500 text-[10px] truncate">{w.message}</div>}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Weight Changes Section */}
            <div className="mb-6">
                <h3 className="text-xs font-bold text-gray-400 mb-1 flex items-center gap-2">
                    <span>📊</span> TOP WEIGHT CHANGES
                </h3>
                <p className="text-[10px] text-gray-600 mb-3">Largest position adjustments today</p>
                <div className="space-y-1">
                    {weightChanges.slice(0, 8).map((c, i) => (
                        <div key={i} className="flex items-center justify-between bg-[#1a1a24] p-2 rounded text-xs">
                            <span className="font-mono font-medium">{c.ticker}</span>
                            <span className={`font-mono font-bold ${c.delta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {c.delta >= 0 ? '+' : ''}{(c.delta * 100).toFixed(2)}%
                            </span>
                        </div>
                    ))}
                    {weightChanges.length === 0 && (
                        <div className="text-gray-600 text-xs bg-[#12121a] p-2 rounded">No changes today</div>
                    )}
                </div>
            </div>

            {/* Models Section */}
            <div className="mb-6">
                <h3 className="text-xs font-bold text-gray-400 mb-1 flex items-center gap-2">
                    <span>🧠</span> MODEL HEALTH
                </h3>
                <p className="text-[10px] text-gray-600 mb-3">ML model performance scores (0-100%)</p>
                <div className="space-y-2">
                    {models.map((m, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${m.status === 'ok' ? 'bg-green-500' :
                                        m.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                                    }`} />
                                <span className="text-gray-400 capitalize">{m.name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-16 h-1.5 bg-[#2a2a3a] rounded overflow-hidden">
                                    <div
                                        className={`h-full ${m.health > 0.8 ? 'bg-green-500' : m.health > 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                        style={{ width: `${m.health * 100}%` }}
                                    />
                                </div>
                                <span className="text-gray-500 w-8 text-right">{(m.health * 100).toFixed(0)}%</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Providers Section */}
            <div>
                <h3 className="text-xs font-bold text-gray-400 mb-1 flex items-center gap-2">
                    <span>🔌</span> DATA PROVIDERS
                </h3>
                <p className="text-[10px] text-gray-600 mb-3">External data source status & latency</p>
                <div className="space-y-2">
                    {providers.map((p, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${p.status === 'up' ? 'bg-green-500' :
                                        p.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                                    }`} />
                                <span className="text-gray-400 capitalize">{p.name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={`text-[10px] px-1.5 py-0.5 rounded ${p.status === 'up' ? 'bg-green-900/30 text-green-400' :
                                        p.status === 'degraded' ? 'bg-yellow-900/30 text-yellow-400' :
                                            'bg-red-900/30 text-red-400'
                                    }`}>
                                    {p.status?.toUpperCase()}
                                </span>
                                {p.latency_ms && (
                                    <span className={`text-gray-500 text-[10px] ${p.latency_ms > 300 ? 'text-yellow-500' : ''}`}>
                                        {p.latency_ms}ms
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Legend */}
            <div className="mt-6 pt-4 border-t border-[#1f1f2e]">
                <p className="text-[9px] text-gray-600 mb-2">LEGEND</p>
                <div className="grid grid-cols-3 gap-2 text-[9px]">
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-green-500" />
                        <span className="text-gray-500">Healthy</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-yellow-500" />
                        <span className="text-gray-500">Warning</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-red-500" />
                        <span className="text-gray-500">Critical</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
