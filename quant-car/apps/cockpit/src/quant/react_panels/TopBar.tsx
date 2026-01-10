'use client'
/**
 * TopBar - Bloomberg-style status bar
 */
import Link from 'next/link'

interface TopBarProps {
    connected: boolean
    wsRate: number
    runId?: string
    tradingDate?: string
    mode: string
    regime: string
}

export default function TopBar({ connected, wsRate, runId, tradingDate, mode, regime }: TopBarProps) {
    const regimeStyles: Record<string, { bg: string; border: string; text: string }> = {
        clear: { bg: 'bg-[var(--color-positive)]/10', border: 'border-[var(--color-positive)]/30', text: 'text-[var(--color-positive)]' },
        rain: { bg: 'bg-[var(--color-warning)]/10', border: 'border-[var(--color-warning)]/30', text: 'text-[var(--color-warning)]' },
        storm: { bg: 'bg-[var(--color-negative)]/10', border: 'border-[var(--color-negative)]/30', text: 'text-[var(--color-negative)]' },
    }

    const rs = regimeStyles[regime] || regimeStyles.clear

    const formatDate = (d?: string) => {
        if (!d) return '--'
        if (d.length === 8) return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
        return d
    }

    return (
        <div className={`h-12 flex items-center px-[var(--grid-gutter)] border-b ${rs.border} ${rs.bg}`}>
            {/* Logo */}
            <div className="font-bold text-base tracking-tight mr-6">QuantDash</div>

            {/* Regime Badge */}
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded ${rs.bg} border ${rs.border}`}>
                <span className="text-sm">
                    {regime === 'storm' ? '⛈️' : regime === 'rain' ? '🌧️' : '☀️'}
                </span>
                <span className={`text-[11px] font-semibold uppercase ${rs.text}`}>{regime}</span>
            </div>

            <div className="w-px h-5 bg-[var(--panel-border)] mx-3" />

            {/* Mode */}
            <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${mode === 'LIVE' ? 'bg-[var(--color-negative)] animate-pulse' : 'bg-[var(--color-positive)]'
                    }`} />
                <span className="text-[11px] font-mono font-medium">{mode}</span>
            </div>

            <div className="w-px h-5 bg-[var(--panel-border)] mx-3" />

            {/* Connection */}
            <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-[var(--color-positive)]' : 'bg-[var(--color-negative)] animate-pulse'}`} />
                <span className="text-[11px] tabular-nums text-[var(--color-text-muted)]">
                    {connected ? `${wsRate} msg/s` : 'Disconnected'}
                </span>
            </div>

            <div className="flex-1" />

            {/* Run Info */}
            <div className="text-[11px] text-[var(--color-text-dim)] font-mono tabular-nums mr-4">
                {formatDate(tradingDate)} | {runId?.slice(0, 16) || '--'}
            </div>

            {/* Navigation */}
            <nav className="flex gap-0.5">
                {[
                    { href: '/quant', label: 'Quant', active: true },
                    { href: '/research', label: 'Research' },
                    { href: '/compare', label: 'Compare' },
                    { href: '/incidents', label: 'Incidents' },
                    { href: '/ops', label: 'Ops' },
                    { href: '/control', label: 'Control' },
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
    )
}
