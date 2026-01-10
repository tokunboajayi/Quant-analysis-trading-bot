/**
 * Panel - Standardized container component
 */
import { ReactNode } from 'react'

interface PanelProps {
    title?: string
    subtitle?: string
    action?: ReactNode
    children: ReactNode
    className?: string
    noPadding?: boolean
}

export default function Panel({
    title,
    subtitle,
    action,
    children,
    className = '',
    noPadding = false
}: PanelProps) {
    return (
        <div className={`
            bg-[var(--panel-bg)] 
            border border-[var(--panel-border)] 
            rounded-lg 
            overflow-hidden
            ${className}
        `}>
            {/* Header */}
            {title && (
                <div className="flex items-center justify-between px-3 py-2.5 border-b border-[var(--panel-border)]">
                    <div>
                        <h3 className="section-title">{title}</h3>
                        {subtitle && (
                            <p className="text-[9px] text-[var(--color-text-dim)] mt-0.5">{subtitle}</p>
                        )}
                    </div>
                    {action && <div className="flex items-center gap-2">{action}</div>}
                </div>
            )}

            {/* Body */}
            <div className={noPadding ? '' : 'p-3'}>
                {children}
            </div>
        </div>
    )
}
