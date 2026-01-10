/**
 * PortfolioList - Left rail portfolio allocation cards
 */
import Panel from '@/components/Panel'

interface PortfolioNode {
    id: string
    label: string
    weight: number
    weight_change_1d?: number | null
}

interface PortfolioListProps {
    nodes: PortfolioNode[]
}

export default function PortfolioList({ nodes }: PortfolioListProps) {
    const sortedNodes = [...nodes].sort((a, b) => b.weight - a.weight)

    return (
        <Panel title="PORTFOLIO ALLOCATION" subtitle="Top holdings by weight">
            <div className="space-y-1.5">
                {sortedNodes.slice(0, 10).map((node, i) => (
                    <div
                        key={node.id}
                        className="flex items-center h-[var(--card-height)] px-[var(--card-padding-x)] py-[var(--card-padding-y)] bg-[var(--card-bg)] rounded-md"
                    >
                        {/* Rank */}
                        <span className="w-5 text-[10px] text-[var(--color-text-dim)] tabular-nums">
                            {i + 1}
                        </span>

                        {/* Ticker + Weight */}
                        <div className="flex-1 min-w-0">
                            <div className="font-semibold text-sm truncate">{node.label}</div>
                            <div className="text-[10px] text-[var(--color-text-muted)] tabular-nums">
                                {(node.weight * 100).toFixed(2)}%
                            </div>
                        </div>

                        {/* Weight Bar */}
                        <div className="w-16 ml-2">
                            <div className="progress-bar">
                                <div
                                    className="progress-bar-fill bg-[var(--color-chart-blue)]"
                                    style={{ width: `${Math.min(node.weight * 100 / 15, 100)}%` }}
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </Panel>
    )
}
