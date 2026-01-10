'use client'
/**
 * Super QuantDash - Bloomberg-grade quant console
 * Refactored with 12-column grid system
 */
import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { useTelemetry } from '@/data/store'

// Shell & Components
import DashboardShell from '@/components/Shell'
import Panel from '@/components/Panel'
import PortfolioList from '@/components/PortfolioList'
import KeyMetrics from '@/components/KeyMetrics'
import PipelineStatus from '@/components/PipelineStatus'
import WarningsPanel from '@/components/WarningsPanel'
import WeightChangesTable from '@/components/WeightChangesTable'
import ModelHealth from '@/components/ModelHealth'
import ProvidersHealth from '@/components/ProvidersHealth'
import TopBar from '@/quant/react_panels/TopBar'
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Pixi Stage (SSR disabled)
const QuantStage = dynamic(() => import('@/quant/engine/QuantStage'), { ssr: false })

export default function QuantPage() {
    const { frame, prevFrame, connected, wsRate, connect, error } = useTelemetry()
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
        connect()
    }, [connect])

    if (!mounted) {
        return (
            <div className="h-screen flex items-center justify-center bg-[var(--color-bg)]">
                <div className="text-[var(--color-text-muted)] animate-pulse">Initializing QuantDash...</div>
            </div>
        )
    }

    return (
        <DashboardShell
            topBar={
                <TopBar
                    connected={connected}
                    wsRate={wsRate}
                    runId={frame?.run_id}
                    tradingDate={frame?.trading_date}
                    mode={frame?.execution_mode || 'PAPER'}
                    regime={frame?.regime_state || 'clear'}
                />
            }
            leftRail={
                <>
                    {/* Portfolio Allocation */}
                    <PortfolioList nodes={frame?.portfolio_flow?.nodes || []} />

                    {/* Key Metrics - anchored bottom */}
                    <div className="mt-auto">
                        <KeyMetrics
                            alpha={frame?.speed_alpha?.value}
                            equity={frame?.pnl?.equity}
                            drawdown={frame?.pnl?.drawdown}
                            return1d={frame?.pnl?.return_1d}
                            turnover={frame?.rpm_turnover?.raw}
                            regime={frame?.regime_state}
                        />
                    </div>
                </>
            }
            center={
                <>
                    {/* Pipeline Status */}
                    <PipelineStatus
                        stages={frame?.pipeline_stage_status || {}}
                        latency={frame?.pipeline_latency_ms || undefined}
                    />

                    {/* Pixi Canvas */}
                    <Panel title="LIVE VISUALIZATION" subtitle="60fps animated charts" noPadding className="flex-1">
                        <div className="relative h-full min-h-[400px]">
                            <ErrorBoundary>
                                <QuantStage frame={frame} prevFrame={prevFrame} wsRate={wsRate} />
                            </ErrorBoundary>

                            {/* Connection overlay */}
                            {!connected && (
                                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                                    <div className="bg-[var(--color-negative)]/80 px-4 py-2 rounded-lg border border-[var(--color-negative)]/50">
                                        <span className="text-white text-sm">{error || 'Connecting...'}</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </Panel>
                </>
            }
            rightRail={
                <>
                    {/* Warnings */}
                    <WarningsPanel warnings={frame?.warnings || []} />

                    {/* Weight Changes */}
                    <WeightChangesTable changes={frame?.top_weight_changes || []} />

                    {/* Model Health */}
                    <ModelHealth models={frame?.models || []} />

                    {/* Providers */}
                    <ProvidersHealth providers={frame?.providers || []} />

                    {/* Legend */}
                    <Panel title="LEGEND">
                        <div className="grid grid-cols-3 gap-2 text-[9px]">
                            <div className="flex items-center gap-1">
                                <div className="w-2 h-2 rounded-full bg-[var(--color-positive)]" />
                                <span className="text-[var(--color-text-dim)]">Healthy</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-2 h-2 rounded-full bg-[var(--color-warning)]" />
                                <span className="text-[var(--color-text-dim)]">Warning</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-2 h-2 rounded-full bg-[var(--color-negative)]" />
                                <span className="text-[var(--color-text-dim)]">Critical</span>
                            </div>
                        </div>
                    </Panel>
                </>
            }
        />
    )
}
