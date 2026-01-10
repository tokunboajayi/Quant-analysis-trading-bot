/**
 * DashboardShell - 12-column grid layout system
 */
import { ReactNode, useState } from 'react'

interface DashboardShellProps {
    topBar: ReactNode
    leftRail: ReactNode
    center: ReactNode
    rightRail: ReactNode
}

export default function DashboardShell({ topBar, leftRail, center, rightRail }: DashboardShellProps) {
    const [showGrid, setShowGrid] = useState(false)

    return (
        <div className="h-screen flex flex-col bg-[var(--color-bg)] text-white overflow-hidden">
            {/* Top Bar */}
            {topBar}

            {/* Main Grid */}
            <div className="flex-1 overflow-hidden px-[var(--grid-gutter)] py-4">
                <div className="h-full grid grid-cols-12 gap-[var(--grid-gap)]">
                    {/* Left Rail - 3 cols */}
                    <div className="col-span-3 flex flex-col gap-[var(--grid-gap)] overflow-auto">
                        {leftRail}
                    </div>

                    {/* Center - 6 cols */}
                    <div className="col-span-6 flex flex-col gap-[var(--grid-gap)] overflow-hidden">
                        {center}
                    </div>

                    {/* Right Rail - 3 cols */}
                    <div className="col-span-3 flex flex-col gap-[var(--grid-gap)] overflow-auto">
                        {rightRail}
                    </div>
                </div>
            </div>

            {/* Grid Overlay (Dev Mode) */}
            {showGrid && (
                <div className="grid-overlay">
                    {Array.from({ length: 12 }).map((_, i) => (
                        <div key={i} />
                    ))}
                </div>
            )}

            {/* Dev Toggle */}
            {process.env.NODE_ENV === 'development' && (
                <button
                    onClick={() => setShowGrid(!showGrid)}
                    className="fixed bottom-2 right-2 z-50 text-[9px] px-2 py-1 bg-blue-900/50 text-blue-300 rounded opacity-50 hover:opacity-100"
                >
                    {showGrid ? 'GRID ON' : 'GRID OFF'}
                </button>
            )}
        </div>
    )
}
