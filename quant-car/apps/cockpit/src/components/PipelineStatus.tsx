/**
 * PipelineStatus - Horizontal pipeline status strip
 */
import Panel from '@/components/Panel'

interface PipelineStatusProps {
    stages: Record<string, string>
    latency?: Record<string, number>
}

const STAGE_ORDER = [
    { id: 'ingest_prices', label: 'Prices' },
    { id: 'ingest_events', label: 'Events' },
    { id: 'build_features', label: 'Features' },
    { id: 'predict', label: 'Models' },
    { id: 'construct_portfolio', label: 'Portfolio' },
    { id: 'execute', label: 'Execute' },
    { id: 'report', label: 'Report' },
]

export default function PipelineStatus({ stages, latency }: PipelineStatusProps) {
    return (
        <Panel title="PIPELINE STATUS" subtitle="Data processing stages">
            <div className="flex items-center justify-between h-16">
                {STAGE_ORDER.map((stage, i) => {
                    const status = stages[stage.id] || 'ok'
                    const lat = latency?.[stage.id]

                    return (
                        <div key={stage.id} className="flex flex-col items-center flex-1">
                            {/* Latency */}
                            <div className="h-4 text-[9px] tabular-nums text-[var(--color-text-dim)]">
                                {lat ? `${Math.round(lat)}ms` : ''}
                            </div>

                            {/* Status dot */}
                            <div className="relative">
                                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${status === 'ok' ? 'border-[var(--color-positive)] bg-[var(--color-positive)]/20' :
                                        status === 'running' ? 'border-[var(--color-info)] bg-[var(--color-info)]/20 animate-pulse' :
                                            status === 'skipped' ? 'border-gray-600 bg-gray-800' :
                                                'border-[var(--color-negative)] bg-[var(--color-negative)]/20'
                                    }`}>
                                    {status === 'ok' && <span className="text-[8px] text-[var(--color-positive)]">✓</span>}
                                    {status === 'running' && <span className="text-[8px] text-[var(--color-info)]">●</span>}
                                    {status === 'skipped' && <span className="text-[8px] text-gray-500">–</span>}
                                    {status === 'failed' && <span className="text-[8px] text-[var(--color-negative)]">✗</span>}
                                </div>

                                {/* Connector line */}
                                {i < STAGE_ORDER.length - 1 && (
                                    <div className="absolute top-1/2 left-full w-full h-0.5 bg-[var(--panel-border)]"
                                        style={{ width: 'calc(100% - 12px)', marginLeft: '6px' }} />
                                )}
                            </div>

                            {/* Label */}
                            <div className="h-4 text-[9px] text-[var(--color-text-dim)] mt-1">
                                {stage.label}
                            </div>
                        </div>
                    )
                })}
            </div>
        </Panel>
    )
}
