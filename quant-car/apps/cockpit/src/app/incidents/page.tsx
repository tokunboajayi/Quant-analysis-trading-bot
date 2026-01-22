'use client'
/**
 * Incidents Page - Anomaly detection with real API data
 */
import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_BASE = 'http://localhost:8005'

interface Incident {
    id: string
    type: string
    severity: number
    opened_ts: string
    closed_ts?: string
    short_summary: string
    metric_name: string
    observed_value: number
    expected_value: number
    drivers?: string[]
}

const INCIDENT_TYPES: Record<string, { icon: string; color: string }> = {
    DRIFT_BREACH: { icon: '📈', color: 'text-yellow-400' },
    PNL_SHOCK: { icon: '📉', color: 'text-red-400' },
    VAR_BREACH: { icon: '⚡', color: 'text-red-400' },
    DRAWDOWN_SPIKE: { icon: '⚠️', color: 'text-red-400' },
    TURNOVER_SPIKE: { icon: '🔄', color: 'text-yellow-400' },
    DATA_GAP: { icon: '🔌', color: 'text-orange-400' },
}

export default function IncidentsPage() {
    const [incidents, setIncidents] = useState<Incident[]>([])
    const [selected, setSelected] = useState<Incident | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch(`${API_BASE}/incidents/index`)
            .then(r => r.json())
            .then(data => {
                setIncidents(data.incidents || [])
                if (data.incidents?.length > 0) {
                    setSelected(data.incidents[0])
                }
                setLoading(false)
            })
            .catch(() => setLoading(false))
    }, [])

    const formatTime = (ts: string) => {
        try {
            return new Date(ts).toLocaleString()
        } catch {
            return ts
        }
    }

    return (
        <div className="h-screen flex flex-col bg-[#0a0a0f] text-white">
            {/* Top Bar */}
            <div className="h-12 flex items-center px-4 border-b border-[#1f1f2e] bg-[#12121a]">
                <span className="font-bold text-lg">Incidents</span>
                <span className="ml-3 text-xs bg-red-900/50 text-red-300 px-2 py-0.5 rounded">
                    {incidents.filter(i => !i.closed_ts).length} Open
                </span>
                <div className="flex-1" />
                <nav className="flex gap-1">
                    <Link href="/quant" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Quant</Link>
                    <Link href="/research" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Research</Link>
                    <Link href="/compare" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Compare</Link>
                    <Link href="/incidents" className="text-xs px-3 py-1.5 bg-blue-600/40 rounded font-medium">Incidents</Link>
                    <Link href="/ops" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Ops</Link>
                </nav>
            </div>

            {loading ? (
                <div className="flex-1 flex items-center justify-center text-gray-500">Loading incidents...</div>
            ) : (
                <div className="flex-1 flex overflow-hidden">
                    {/* Incident List */}
                    <div className="w-80 border-r border-[#1f1f2e] overflow-auto bg-[#0c0c12]">
                        <div className="divide-y divide-[#1f1f2e]">
                            {incidents.map(inc => {
                                const typeInfo = INCIDENT_TYPES[inc.type] || { icon: '❓', color: 'text-gray-400' }
                                return (
                                    <div
                                        key={inc.id}
                                        className={`p-3 cursor-pointer transition-colors ${selected?.id === inc.id ? 'bg-[#1a1a24]' : 'hover:bg-[#12121a]'
                                            }`}
                                        onClick={() => setSelected(inc)}
                                    >
                                        <div className="flex items-center gap-2">
                                            <span className="text-lg">{typeInfo.icon}</span>
                                            <span className={`text-sm font-semibold ${typeInfo.color}`}>
                                                {inc.type.replace(/_/g, ' ')}
                                            </span>
                                            <span className={`ml-auto w-2 h-2 rounded-full ${inc.severity === 3 ? 'bg-red-500' :
                                                inc.severity === 2 ? 'bg-yellow-500' : 'bg-blue-500'
                                                }`} />
                                        </div>
                                        <div className="text-xs text-gray-500 mt-1 line-clamp-1">{inc.short_summary}</div>
                                        <div className="text-xs text-gray-600 mt-1 flex items-center gap-2">
                                            {formatTime(inc.opened_ts).split(',')[0]}
                                            {inc.closed_ts && <span className="text-green-500 text-[10px] font-medium">RESOLVED</span>}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>

                    {/* Incident Detail */}
                    <div className="flex-1 p-6 overflow-auto">
                        {selected ? (
                            <>
                                <div className="flex items-start gap-4 mb-6">
                                    <span className="text-4xl">{INCIDENT_TYPES[selected.type]?.icon || '❓'}</span>
                                    <div>
                                        <h2 className={`text-2xl font-bold ${INCIDENT_TYPES[selected.type]?.color || 'text-gray-400'}`}>
                                            {selected.type.replace(/_/g, ' ')}
                                        </h2>
                                        <p className="text-gray-400 mt-1">{selected.short_summary}</p>
                                        <p className="text-gray-600 text-sm mt-2">
                                            Opened: {formatTime(selected.opened_ts)}
                                            {selected.closed_ts && ` • Closed: ${formatTime(selected.closed_ts)}`}
                                        </p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-3 gap-4 mb-6">
                                    <div className="bg-[#12121a] p-4 rounded-lg border border-[#1f1f2e]">
                                        <div className="text-xs text-gray-500 mb-1">OBSERVED</div>
                                        <div className="text-3xl font-mono text-red-400">{selected.observed_value.toFixed(2)}</div>
                                    </div>
                                    <div className="bg-[#12121a] p-4 rounded-lg border border-[#1f1f2e]">
                                        <div className="text-xs text-gray-500 mb-1">EXPECTED</div>
                                        <div className="text-3xl font-mono text-green-400">{selected.expected_value.toFixed(2)}</div>
                                    </div>
                                    <div className="bg-[#12121a] p-4 rounded-lg border border-[#1f1f2e]">
                                        <div className="text-xs text-gray-500 mb-1">DEVIATION</div>
                                        <div className="text-3xl font-mono text-yellow-400">
                                            {((selected.observed_value / selected.expected_value - 1) * 100).toFixed(0)}%
                                        </div>
                                    </div>
                                </div>

                                <h3 className="text-sm font-semibold text-gray-400 mb-3">ROOT CAUSE ANALYSIS</h3>
                                <div className="bg-[#12121a] p-4 rounded-lg border border-[#1f1f2e] mb-6">
                                    <ul className="space-y-2">
                                        {(selected.drivers || []).map((driver, i) => (
                                            <li key={i} className="flex items-start gap-3 text-sm">
                                                <span className={`mt-1 w-2 h-2 rounded-full ${i === 0 ? 'bg-red-500' : i === 1 ? 'bg-yellow-500' : 'bg-blue-500'
                                                    }`} />
                                                <span className="text-gray-300">{driver}</span>
                                            </li>
                                        ))}
                                        {(!selected.drivers || selected.drivers.length === 0) && (
                                            <li className="text-gray-500 text-sm">No drivers identified</li>
                                        )}
                                    </ul>
                                </div>

                                <h3 className="text-sm font-semibold text-gray-400 mb-3">POSTMORTEM</h3>
                                <div className="bg-[#0c0c12] p-4 rounded-lg border border-[#1f1f2e] font-mono text-xs text-gray-300 whitespace-pre-wrap">
                                    {`# Incident: ${selected.type}

## Summary
${selected.short_summary}

## Timeline
- Opened: ${formatTime(selected.opened_ts)}
${selected.closed_ts ? `- Closed: ${formatTime(selected.closed_ts)}` : '- Status: OPEN'}

## Impact
- Metric: ${selected.metric_name}
- Observed: ${selected.observed_value}
- Expected: ${selected.expected_value}
- Deviation: ${((selected.observed_value / selected.expected_value - 1) * 100).toFixed(1)}%

## Remediation
- Review threshold configuration
- Investigate data quality
- Monitor for recurrence`}
                                </div>
                            </>
                        ) : (
                            <div className="h-full flex items-center justify-center text-gray-500">
                                Select an incident to view details
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
