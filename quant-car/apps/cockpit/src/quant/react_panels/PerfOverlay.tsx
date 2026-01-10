'use client'
/**
 * PerfOverlay - FPS and performance metrics
 */
import { useEffect, useState } from 'react'
import { perfMonitor } from '../engine/perf'

export default function PerfOverlay() {
    const [stats, setStats] = useState({ fps: 60, particleCount: 0, wsRate: 0 })

    useEffect(() => {
        const interval = setInterval(() => {
            setStats(perfMonitor.getStats())
        }, 500)
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="absolute top-2 left-2 bg-black/80 text-xs font-mono p-2 rounded space-y-1">
            <div className={stats.fps < 55 ? 'text-red-400' : 'text-green-400'}>
                FPS: {stats.fps}
            </div>
            <div className="text-gray-400">Particles: {stats.particleCount}</div>
            <div className="text-gray-400">WS: {stats.wsRate} msg/s</div>
        </div>
    )
}
