'use client'
/**
 * CommandPalette - Global ⌘K command interface
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'

interface Command {
    id: string
    title: string
    category: string
    keywords: string[]
    action: () => void
    shortcut?: string
}

interface CommandPaletteProps {
    isOpen: boolean
    onClose: () => void
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
    const [query, setQuery] = useState('')
    const [selectedIndex, setSelectedIndex] = useState(0)
    const inputRef = useRef<HTMLInputElement>(null)
    const router = useRouter()

    const commands: Command[] = [
        // Navigation
        { id: 'nav-quant', title: 'Go to Quant Dashboard', category: 'Navigation', keywords: ['quant', 'dashboard', 'main'], action: () => router.push('/quant') },
        { id: 'nav-research', title: 'Go to Research', category: 'Navigation', keywords: ['research', 'walkforward', 'drift'], action: () => router.push('/research') },
        { id: 'nav-compare', title: 'Go to Compare', category: 'Navigation', keywords: ['compare', 'a/b', 'strategies'], action: () => router.push('/compare') },
        { id: 'nav-incidents', title: 'Go to Incidents', category: 'Navigation', keywords: ['incidents', 'alerts', 'anomaly'], action: () => router.push('/incidents') },
        { id: 'nav-replay', title: 'Go to Replay', category: 'Navigation', keywords: ['replay', 'history'], action: () => router.push('/replay') },

        // Tickers
        { id: 'focus-nvda', title: 'Focus NVDA', category: 'Ticker', keywords: ['nvda', 'nvidia'], action: () => console.log('Focus NVDA') },
        { id: 'focus-aapl', title: 'Focus AAPL', category: 'Ticker', keywords: ['aapl', 'apple'], action: () => console.log('Focus AAPL') },
        { id: 'focus-tsla', title: 'Focus TSLA', category: 'Ticker', keywords: ['tsla', 'tesla'], action: () => console.log('Focus TSLA') },

        // Filters
        { id: 'filter-tech', title: 'Filter: Technology Sector', category: 'Filter', keywords: ['tech', 'technology', 'sector'], action: () => console.log('Filter tech') },
        { id: 'filter-hazards', title: 'Show High-Risk Hazards (>0.7)', category: 'Filter', keywords: ['hazard', 'risk', 'high'], action: () => console.log('Hazard filter') },
        { id: 'clear-filters', title: 'Clear All Filters', category: 'Filter', keywords: ['clear', 'reset'], action: () => console.log('Clear filters') },

        // Actions
        { id: 'toggle-perf', title: 'Toggle Performance Overlay', category: 'Dev', keywords: ['perf', 'fps', 'performance'], action: () => console.log('Toggle perf') },
        { id: 'freeze', title: 'Freeze Animation', category: 'Control', keywords: ['freeze', 'pause', 'stop'], action: () => console.log('Freeze') },
        { id: 'resume', title: 'Resume Animation', category: 'Control', keywords: ['resume', 'play', 'start'], action: () => console.log('Resume') },
    ]

    // Fuzzy search
    const filteredCommands = query
        ? commands.filter(cmd => {
            const q = query.toLowerCase()
            return cmd.title.toLowerCase().includes(q) ||
                cmd.keywords.some(k => k.includes(q))
        })
        : commands

    // Group by category
    const grouped = filteredCommands.reduce((acc, cmd) => {
        if (!acc[cmd.category]) acc[cmd.category] = []
        acc[cmd.category].push(cmd)
        return acc
    }, {} as Record<string, Command[]>)

    useEffect(() => {
        if (isOpen) {
            inputRef.current?.focus()
            setQuery('')
            setSelectedIndex(0)
        }
    }, [isOpen])

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault()
            setSelectedIndex(i => Math.min(i + 1, filteredCommands.length - 1))
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setSelectedIndex(i => Math.max(i - 1, 0))
        } else if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
            filteredCommands[selectedIndex].action()
            onClose()
        } else if (e.key === 'Escape') {
            onClose()
        }
    }, [filteredCommands, selectedIndex, onClose])

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20" onClick={onClose}>
            <div className="absolute inset-0 bg-black/50" />
            <div
                className="relative bg-[#12121a] border border-[#2a2a3a] rounded-lg w-[600px] max-h-[60vh] overflow-hidden shadow-2xl"
                onClick={e => e.stopPropagation()}
            >
                {/* Search Input */}
                <div className="flex items-center border-b border-[#2a2a3a] px-4 py-3">
                    <span className="text-gray-500 mr-3">⌘</span>
                    <input
                        ref={inputRef}
                        type="text"
                        placeholder="Type a command..."
                        className="flex-1 bg-transparent outline-none text-white"
                        value={query}
                        onChange={e => { setQuery(e.target.value); setSelectedIndex(0) }}
                        onKeyDown={handleKeyDown}
                    />
                </div>

                {/* Command List */}
                <div className="overflow-auto max-h-[50vh] p-2">
                    {Object.entries(grouped).map(([category, cmds]) => (
                        <div key={category} className="mb-3">
                            <div className="text-xs text-gray-500 px-2 py-1">{category}</div>
                            {cmds.map((cmd, i) => {
                                const globalIndex = filteredCommands.indexOf(cmd)
                                return (
                                    <div
                                        key={cmd.id}
                                        className={`px-3 py-2 rounded cursor-pointer text-sm ${globalIndex === selectedIndex ? 'bg-blue-600/30 text-white' : 'text-gray-300 hover:bg-[#1a1a24]'
                                            }`}
                                        onClick={() => { cmd.action(); onClose() }}
                                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                                    >
                                        {cmd.title}
                                        {cmd.shortcut && <span className="float-right text-gray-500">{cmd.shortcut}</span>}
                                    </div>
                                )
                            })}
                        </div>
                    ))}
                    {filteredCommands.length === 0 && (
                        <div className="text-center text-gray-500 py-8">No commands found</div>
                    )}
                </div>
            </div>
        </div>
    )
}

// Hook to manage command palette state
export function useCommandPalette() {
    const [isOpen, setIsOpen] = useState(false)

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault()
                setIsOpen(prev => !prev)
            }
        }
        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [])

    return { isOpen, setIsOpen, close: () => setIsOpen(false) }
}
