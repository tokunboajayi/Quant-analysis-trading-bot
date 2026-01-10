/**
 * WeightChangesTable - Top position changes with aligned columns
 */
import Panel from '@/components/Panel'

interface WeightChange {
    ticker: string
    delta: number
}

interface WeightChangesTableProps {
    changes: WeightChange[]
}

export default function WeightChangesTable({ changes }: WeightChangesTableProps) {
    return (
        <Panel title="WEIGHT CHANGES" subtitle="Today's adjustments">
            <div className="space-y-0.5">
                {/* Header */}
                <div className="flex items-center justify-between px-2 py-1 text-[9px] text-[var(--color-text-dim)]">
                    <span>TICKER</span>
                    <span>DELTA</span>
                </div>

                {/* Rows */}
                {changes.slice(0, 8).map((c, i) => (
                    <div key={i} className="flex items-center justify-between h-8 px-2 bg-[var(--card-bg)] rounded">
                        <span className="text-xs font-mono font-medium">{c.ticker}</span>
                        <span className={`text-xs font-mono font-semibold tabular-nums ${c.delta >= 0 ? 'text-[var(--color-positive)]' : 'text-[var(--color-negative)]'
                            }`}>
                            {c.delta >= 0 ? '+' : ''}{(c.delta * 100).toFixed(2)}%
                        </span>
                    </div>
                ))}

                {changes.length === 0 && (
                    <div className="h-8 px-2 flex items-center text-xs text-[var(--color-text-dim)]">
                        No changes today
                    </div>
                )}
            </div>
        </Panel>
    )
}
