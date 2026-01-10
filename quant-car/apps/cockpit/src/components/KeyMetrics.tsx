/**
 * KeyMetrics - Bottom of left rail, key performance indicators
 */
import Panel from '@/components/Panel'

interface KeyMetricsProps {
    alpha?: number
    equity?: number
    drawdown?: number
    return1d?: number
    turnover?: number
    regime?: string
}

export default function KeyMetrics({ alpha, equity, drawdown, return1d, turnover, regime }: KeyMetricsProps) {
    const metrics = [
        { label: 'Alpha (IC)', value: alpha?.toFixed(2) || '--', color: 'text-[var(--color-positive)]' },
        { label: 'Equity', value: equity ? `$${equity.toLocaleString()}` : '--', color: 'text-[var(--color-chart-blue)]' },
        { label: 'Drawdown', value: drawdown ? `${(drawdown * 100).toFixed(2)}%` : '--', color: 'text-[var(--color-negative)]' },
        { label: 'Daily Return', value: return1d !== undefined ? `${(return1d * 100).toFixed(2)}%` : '--', color: return1d && return1d >= 0 ? 'text-[var(--color-positive)]' : 'text-[var(--color-negative)]' },
        { label: 'Turnover', value: turnover ? `${(turnover * 100).toFixed(1)}%` : '--', color: 'text-[var(--color-chart-purple)]' },
    ]

    return (
        <Panel title="KEY METRICS" subtitle="Real-time performance">
            <div className="space-y-2">
                {metrics.map((m, i) => (
                    <div key={i} className="flex items-center justify-between h-8">
                        <span className="text-xs text-[var(--color-text-muted)]">{m.label}</span>
                        <span className={`text-sm font-mono font-semibold tabular-nums ${m.color}`}>
                            {m.value}
                        </span>
                    </div>
                ))}

                {/* Regime indicator */}
                {regime && (
                    <div className="flex items-center justify-between h-8 pt-2 border-t border-[var(--panel-border)]">
                        <span className="text-xs text-[var(--color-text-muted)]">Regime</span>
                        <span className={`text-sm font-semibold uppercase ${regime === 'storm' ? 'text-[var(--color-negative)]' :
                                regime === 'rain' ? 'text-[var(--color-warning)]' :
                                    'text-[var(--color-positive)]'
                            }`}>
                            {regime === 'storm' ? '⛈️' : regime === 'rain' ? '🌧️' : '☀️'} {regime}
                        </span>
                    </div>
                )}
            </div>
        </Panel>
    )
}
