/**
 * WarningsPanel - Active system warnings
 */
import Panel from '@/components/Panel'

interface Warning {
    code: string
    severity: number
    message?: string
}

interface WarningsPanelProps {
    warnings: Warning[]
}

export default function WarningsPanel({ warnings }: WarningsPanelProps) {
    return (
        <Panel title="ACTIVE WARNINGS" subtitle="System alerts">
            <div className="space-y-1.5">
                {warnings.length === 0 ? (
                    <div className="flex items-center gap-2 h-8 px-2 text-xs text-[var(--color-text-dim)]">
                        <span className="w-2 h-2 rounded-full bg-[var(--color-positive)]" />
                        No active warnings
                    </div>
                ) : (
                    warnings.map((w, i) => (
                        <div key={i} className="flex items-start gap-2 p-2 bg-[var(--card-bg)] rounded">
                            <span className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${w.severity === 3 ? 'bg-[var(--color-negative)]' :
                                    w.severity === 2 ? 'bg-[var(--color-warning)]' :
                                        'bg-[var(--color-info)]'
                                }`} />
                            <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium">{w.code}</div>
                                {w.message && (
                                    <div className="text-[10px] text-[var(--color-text-dim)] truncate">{w.message}</div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </Panel>
    )
}
