/**
 * ModelHealth - Model performance indicators
 */
import Panel from '@/components/Panel'

interface Model {
    name: string
    status: string
    health: number
}

interface ModelHealthProps {
    models: Model[]
}

export default function ModelHealth({ models }: ModelHealthProps) {
    return (
        <Panel title="MODEL HEALTH" subtitle="ML performance scores">
            <div className="space-y-2">
                {models.map((m, i) => (
                    <div key={i} className="flex items-center gap-3 h-8">
                        {/* Status dot */}
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${m.status === 'ok' ? 'bg-[var(--color-positive)]' :
                                m.status === 'degraded' ? 'bg-[var(--color-warning)]' :
                                    'bg-[var(--color-negative)]'
                            }`} />

                        {/* Name */}
                        <span className="text-xs text-[var(--color-text-muted)] w-12 capitalize">{m.name}</span>

                        {/* Progress bar */}
                        <div className="flex-1 progress-bar">
                            <div
                                className={`progress-bar-fill ${m.health > 0.8 ? 'bg-[var(--color-positive)]' :
                                        m.health > 0.5 ? 'bg-[var(--color-warning)]' :
                                            'bg-[var(--color-negative)]'
                                    }`}
                                style={{ width: `${m.health * 100}%` }}
                            />
                        </div>

                        {/* Value */}
                        <span className="text-xs font-mono tabular-nums text-[var(--color-text-dim)] w-8 text-right">
                            {(m.health * 100).toFixed(0)}%
                        </span>
                    </div>
                ))}
            </div>
        </Panel>
    )
}
