/**
 * Quant Theme - Design tokens for professional quant desk
 */

export const theme = {
    // Background
    bg: {
        primary: 0x0a0a0f,
        elevated: 0x12121a,
        panel: 0x1a1a24,
    },

    // Borders
    border: {
        subtle: 0x1f1f2e,
        normal: 0x2a2a3a,
        strong: 0x3a3a4a,
    },

    // Text
    text: {
        primary: 0xe5e5e5,
        secondary: 0xa0a0a0,
        dim: 0x6b7280,
        muted: 0x4b5563,
    },

    // Semantic colors
    semantic: {
        positive: 0x22c55e,   // Green
        negative: 0xef4444,   // Red
        warning: 0xeab308,    // Yellow
        info: 0x3b82f6,       // Blue
        neutral: 0x6b7280,    // Gray
    },

    // Sector colors (for SankeyFlow)
    sectors: {
        Technology: 0x3b82f6,
        Healthcare: 0x22c55e,
        Financials: 0xf59e0b,
        Consumer: 0x8b5cf6,
        Energy: 0xef4444,
        Industrials: 0x6366f1,
        Materials: 0x14b8a6,
        Utilities: 0x06b6d4,
        RealEstate: 0xec4899,
        Other: 0x6b7280,
    },

    // Pipeline stages
    pipeline: {
        ok: 0x22c55e,
        running: 0x3b82f6,
        failed: 0xef4444,
        skipped: 0x6b7280,
    },

    // Regime colors
    regime: {
        clear: 0x22c55e,
        rain: 0xeab308,
        storm: 0xef4444,
    },

    // Chart colors
    chart: {
        equity: 0x3b82f6,
        drawdown: 0xef4444,
        alpha: 0x22c55e,
        risk: 0xf59e0b,
    },

    // Glow
    glow: {
        info: 'rgba(59, 130, 246, 0.4)',
        warning: 'rgba(234, 179, 8, 0.4)',
        danger: 'rgba(239, 68, 68, 0.4)',
    },
}

// Get sector color
export function getSectorColor(sector: string): number {
    const key = sector.replace('sector:', '') as keyof typeof theme.sectors
    return theme.sectors[key] || theme.sectors.Other
}

// Get status color
export function getStatusColor(status: string): number {
    if (status === 'ok' || status === 'up') return theme.semantic.positive
    if (status === 'degraded' || status === 'warning') return theme.semantic.warning
    if (status === 'failed' || status === 'down') return theme.semantic.negative
    return theme.semantic.neutral
}

// Convert hex to CSS color
export function hexToCSS(hex: number): string {
    return `#${hex.toString(16).padStart(6, '0')}`
}
