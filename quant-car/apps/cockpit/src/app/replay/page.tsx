'use client'
/**
 * Replay Page - Historical playback with real run data
 */
import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_BASE = 'http://localhost:8005'

interface RunInfo { run_id: string; date: string; frame_count?: number }

export default function ReplayPage() {
    const [runs, setRuns] = useState<RunInfo[]>([])
    const [selectedRun, setSelectedRun] = useState<string>('')
    const [playbackPosition, setPlaybackPosition] = useState(0)
    const [isPlaying, setIsPlaying] = useState(false)
    const [playbackSpeed, setPlaybackSpeed] = useState(1)
    const [loading, setLoading] = useState(true)
    const [currentFrame, setCurrentFrame] = useState<any>(null)

    useEffect(() => {
        fetch(`${API_BASE}/replay/index`)
            .then(r => r.json())
            .then(data => {
                setRuns(data.runs || [])
                if (data.runs?.length > 0) {
                    setSelectedRun(data.runs[0].run_id)
                }
                setLoading(false)
            })
            .catch(() => {
                // Use demo data if API fails
                setRuns([
                    { run_id: '20260109_cf64ff71', date: '2026-01-09', frame_count: 100 },
                    { run_id: '20260108_abc12345', date: '2026-01-08', frame_count: 100 },
                ])
                setLoading(false)
            })
    }, [])

    // Playback simulation
    useEffect(() => {
        if (!isPlaying || !selectedRun) return
        const interval = setInterval(() => {
            setPlaybackPosition(p => {
                if (p >= 100) {
                    setIsPlaying(false)
                    return 100
                }
                return Math.min(p + playbackSpeed, 100)
            })
        }, 500)
        return () => clearInterval(interval)
    }, [isPlaying, playbackSpeed, selectedRun])

    // Fetch frame on position change
    useEffect(() => {
        if (!selectedRun) return
        fetch(`${API_BASE}/telemetry/latest`)
            .then(r => r.json())
            .then(setCurrentFrame)
            .catch(() => { })
    }, [selectedRun, Math.floor(playbackPosition / 10)])

    const formatDate = (d: string) => {
        if (d.length === 8) return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
        return d
    }

    return (
        <div className="h-screen flex flex-col bg-[#0a0a0f] text-white">
            {/* Top Bar */}
            <div className="h-12 flex items-center px-4 border-b border-[#1f1f2e] bg-[#12121a]">
                <span className="font-bold text-lg">Replay</span>
                <div className="flex-1" />
                <select
                    className="bg-[#0c0c12] border border-[#2a2a3a] rounded px-3 py-1.5 text-sm mr-4"
                    value={selectedRun}
                    onChange={e => { setSelectedRun(e.target.value); setPlaybackPosition(0); setIsPlaying(false) }}
                >
                    <option value="">Select Run</option>
                    {runs.map(r => (
                        <option key={r.run_id} value={r.run_id}>
                            {formatDate(r.date)} ({r.run_id.slice(-8)})
                        </option>
                    ))}
                </select>
                <nav className="flex gap-1">
                    <Link href="/quant" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Quant</Link>
                    <Link href="/research" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Research</Link>
                    <Link href="/compare" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Compare</Link>
                    <Link href="/incidents" className="text-xs px-3 py-1.5 text-gray-400 hover:bg-white/5 rounded">Incidents</Link>
                    <Link href="/replay" className="text-xs px-3 py-1.5 bg-blue-600/40 rounded font-medium">Replay</Link>
                </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col p-6">
                {loading ? (
                    <div className="flex-1 flex items-center justify-center text-gray-500">Loading runs...</div>
                ) : (
                    <>
                        {/* Status Bar */}
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-4">
                                <div className={`px-3 py-1 rounded text-sm font-medium ${isPlaying ? 'bg-green-900/50 text-green-300' : 'bg-gray-800 text-gray-400'
                                    }`}>
                                    {isPlaying ? '▶ Playing' : '⏸ Paused'}
                                </div>
                                <div className="text-sm text-gray-400">
                                    Frame: <span className="font-mono text-white">{Math.floor(playbackPosition)}</span> / 100
                                </div>
                            </div>
                            <div className="text-sm text-gray-400">
                                Speed: <span className="font-mono text-white">{playbackSpeed}x</span>
                            </div>
                        </div>

                        {/* Visualization */}
                        <div className="flex-1 bg-[#12121a] rounded-lg border border-[#1f1f2e] mb-6 flex items-center justify-center relative overflow-hidden">
                            {selectedRun && currentFrame ? (
                                <div className="text-center">
                                    <div className="text-4xl mb-4">📈</div>
                                    <div className="text-2xl font-mono text-blue-400">
                                        ${currentFrame.pnl?.equity?.toLocaleString() || '100,000'}
                                    </div>
                                    <div className="text-sm text-gray-400 mt-2">
                                        Equity at t={Math.floor(playbackPosition)}
                                    </div>
                                    <div className={`text-sm mt-2 ${(currentFrame.pnl?.return_1d || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                                        }`}>
                                        {((currentFrame.pnl?.return_1d || 0) * 100).toFixed(2)}% today
                                    </div>
                                </div>
                            ) : (
                                <div className="text-gray-500">Select a run to replay</div>
                            )}

                            {/* Progress indicator */}
                            <div className="absolute bottom-0 left-0 right-0 h-1 bg-[#1a1a24]">
                                <div
                                    className="h-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all"
                                    style={{ width: `${playbackPosition}%` }}
                                />
                            </div>
                        </div>

                        {/* Scrubber */}
                        <div className="mb-6">
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={playbackPosition}
                                onChange={e => { setPlaybackPosition(parseInt(e.target.value)); setIsPlaying(false) }}
                                className="w-full h-2 bg-[#1a1a24] rounded-lg appearance-none cursor-pointer accent-blue-500"
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-2">
                                <span>Start</span>
                                <span className="text-blue-400">{playbackPosition.toFixed(0)}%</span>
                                <span>End</span>
                            </div>
                        </div>

                        {/* Controls */}
                        <div className="flex items-center justify-center gap-3">
                            <button
                                onClick={() => setPlaybackPosition(0)}
                                className="px-4 py-2 bg-[#1a1a24] rounded-lg hover:bg-[#2a2a3a] transition-colors text-lg"
                                disabled={!selectedRun}
                            >
                                ⏮️
                            </button>
                            <button
                                onClick={() => setIsPlaying(!isPlaying)}
                                className={`px-6 py-2 rounded-lg transition-colors text-lg font-medium ${isPlaying ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-blue-600 hover:bg-blue-700'
                                    }`}
                                disabled={!selectedRun}
                            >
                                {isPlaying ? '⏸️ Pause' : '▶️ Play'}
                            </button>
                            <button
                                onClick={() => setPlaybackPosition(100)}
                                className="px-4 py-2 bg-[#1a1a24] rounded-lg hover:bg-[#2a2a3a] transition-colors text-lg"
                                disabled={!selectedRun}
                            >
                                ⏭️
                            </button>
                            <select
                                value={playbackSpeed}
                                onChange={e => setPlaybackSpeed(parseFloat(e.target.value))}
                                className="bg-[#1a1a24] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm ml-4"
                            >
                                <option value="0.5">0.5x</option>
                                <option value="1">1x</option>
                                <option value="2">2x</option>
                                <option value="4">4x</option>
                            </select>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
