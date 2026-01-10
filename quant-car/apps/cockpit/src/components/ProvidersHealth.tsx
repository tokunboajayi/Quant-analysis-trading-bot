/**
 * ProvidersHealth - Data provider status
 */
import Panel from '@/components/Panel'

interface Provider {
    name: string
    status: string
    latency_ms?: number
}

interface ProvidersHealthProps {
    providers: Provider[]
}

export default function ProvidersHealth({ providers }: ProvidersHealthProps) {
    return (
        <Panel title="DATA PROVIDERS" subtitle="External connections">
            <div className="space-y-1.5">
                {providers.map((p, i) => (
                    <div key={i} className="flex items-center justify-between h-8 px-2 bg-[var(--card-bg)] rounded">
                        {/* Status + Name */}
                        <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${p.status === 'up' ? 'bg-[var(--color-positive)]' :
                                    p.status === 'degraded' ? 'bg-[var(--color-warning)]' :
                                        'bg-[var(--color-negative)]'
                                }`} />
                            <span className="text-xs capitalize">{p.name}</span>
                        </div>

                        {/* Status badge + Latency */}
                        <div className="flex items-center gap-2">
                            <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium w-16 text-center ${p.status === 'up' ? 'bg-[var(--color-positive)]/20 text-[var(--color-positive)]' :
                                    p.status === 'degraded' ? 'bg-[var(--color-warning)]/20 text-[var(--color-warning)]' :
                                        'bg-[var(--color-negative)]/20 text-[var(--color-negative)]'
                                }`}>
                                {p.status?.toUpperCase()}
                            </span>
                            {p.latency_ms !== undefined && (
                                <span className={`text-[10px] font-mono tabular-nums w-12 text-right ${p.latency_ms > 300 ? 'text-[var(--color-warning)]' : 'text-[var(--color-text-dim)]'
                                    }`}>
                                    {p.latency_ms}ms
                                </span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </Panel>
    )
}
