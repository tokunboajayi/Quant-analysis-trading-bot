'use client'

interface StatusBarProps {
    regime: 'clear' | 'rain' | 'storm'
    mode: 'PAPER' | 'LIVE'
    pipelineStatus: string
    lastRun?: string | null
    connected: boolean
}

export default function StatusBar({ regime, mode, pipelineStatus, lastRun, connected }: StatusBarProps) {
    const regimeColors = {
        clear: { bg: 'bg-green-900/30', text: 'text-green-300', icon: '☀️' },
        rain: { bg: 'bg-yellow-900/30', text: 'text-yellow-300', icon: '🌧️' },
        storm: { bg: 'bg-red-900/30', text: 'text-red-300', icon: '⛈️' },
    }

    const r = regimeColors[regime] || regimeColors.clear

    const statusColors = {
        ok: 'text-green-400',
        degraded: 'text-yellow-400',
        failed: 'text-red-400',
        stale: 'text-gray-400',
    }

    return (
        <div className={`h-12 flex items-center px-6 border-b border-cockpit-border ${r.bg}`}>
            {/* Regime */}
            <div className="flex items-center gap-2">
                <span>{r.icon}</span>
                <span className={`text-sm font-semibold ${r.text}`}>
                    {regime.toUpperCase()}
                </span>
            </div>

            <div className="w-px h-6 bg-cockpit-border mx-4" />

            {/* Mode */}
            <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${mode === 'LIVE' ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`} />
                <span className="text-sm font-mono">{mode}</span>
            </div>

            <div className="w-px h-6 bg-cockpit-border mx-4" />

            {/* Pipeline Status */}
            <div className="flex items-center gap-2">
                <span className="text-cockpit-text-dim text-sm">PIPELINE</span>
                <span className={`text-sm font-semibold ${statusColors[pipelineStatus as keyof typeof statusColors] || 'text-gray-400'}`}>
                    {pipelineStatus.toUpperCase()}
                </span>
            </div>

            <div className="flex-1" />

            {/* Connection Status */}
            <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`} />
                <span className="text-xs text-cockpit-text-dim">
                    {connected ? 'LIVE' : 'RECONNECTING'}
                </span>
            </div>

            {/* Last Run */}
            {lastRun && (
                <>
                    <div className="w-px h-6 bg-cockpit-border mx-4" />
                    <span className="text-xs text-cockpit-text-dim">
                        Last: {new Date(lastRun).toLocaleTimeString()}
                    </span>
                </>
            )}
        </div>
    )
}
