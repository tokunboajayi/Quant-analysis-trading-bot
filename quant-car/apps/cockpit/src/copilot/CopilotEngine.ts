/**
 * Copilot Engine - Natural language to command compiler
 */

interface CommandPlan {
    id: string
    confidence: number
    steps: { commandId: string; args: Record<string, any>; label: string }[]
    trace: { tokens: string[]; matchedRules: string[]; entities: { type: string; value: string }[] }
}

interface Intent {
    pattern: RegExp
    intent: string
    extract: (match: RegExpMatchArray) => Record<string, any>
}

const INTENTS: Intent[] = [
    // Navigation
    { pattern: /go\s+(?:to\s+)?(\w+)/i, intent: 'NAVIGATE', extract: m => ({ route: m[1] }) },
    { pattern: /open\s+(\w+)/i, intent: 'NAVIGATE', extract: m => ({ route: m[1] }) },

    // Focus entity
    { pattern: /focus\s+(\w+)/i, intent: 'FOCUS_ENTITY', extract: m => ({ ticker: m[1].toUpperCase() }) },
    { pattern: /show\s+(\w+)/i, intent: 'FOCUS_ENTITY', extract: m => ({ ticker: m[1].toUpperCase() }) },
    { pattern: /ticker\s+(\w+)/i, intent: 'FOCUS_ENTITY', extract: m => ({ ticker: m[1].toUpperCase() }) },

    // Filter
    { pattern: /filter\s+sector\s+(\w+)/i, intent: 'FILTER_SECTOR', extract: m => ({ sector: m[1] }) },
    { pattern: /hazards?\s*>\s*([\d.]+)/i, intent: 'SET_THRESHOLD', extract: m => ({ threshold: parseFloat(m[1]) }) },
    { pattern: /clear\s+filters?/i, intent: 'CLEAR_FILTERS', extract: () => ({}) },

    // Explain
    { pattern: /why\s+(?:did\s+)?drawdown/i, intent: 'EXPLAIN_EVENT', extract: () => ({ type: 'DRAWDOWN_SPIKE' }) },
    { pattern: /why\s+(?:did\s+)?pnl/i, intent: 'EXPLAIN_EVENT', extract: () => ({ type: 'PNL_SHOCK' }) },
    { pattern: /what\s+caused/i, intent: 'EXPLAIN_EVENT', extract: () => ({ type: 'general' }) },

    // Compare
    { pattern: /compare\s+(?:latest\s+)?(?:with\s+)?baseline/i, intent: 'COMPARE', extract: () => ({ runA: 'baseline', runB: 'latest' }) },
    { pattern: /compare\s+runs?/i, intent: 'COMPARE', extract: () => ({}) },

    // Replay
    { pattern: /replay\s+(?:run\s+)?(\d{4}-\d{2}-\d{2})/i, intent: 'REPLAY', extract: m => ({ date: m[1] }) },
    { pattern: /freeze/i, intent: 'CONTROL', extract: () => ({ action: 'freeze' }) },
    { pattern: /resume|play/i, intent: 'CONTROL', extract: () => ({ action: 'resume' }) },
]

// Route mapping
const ROUTE_MAP: Record<string, string> = {
    quant: '/quant',
    dashboard: '/quant',
    research: '/research',
    compare: '/compare',
    incidents: '/incidents',
    ops: '/ops',
    replay: '/replay',
}

export function compile(input: string): CommandPlan {
    const tokens = input.toLowerCase().split(/\s+/)
    const matchedRules: string[] = []
    const entities: { type: string; value: string }[] = []
    const steps: CommandPlan['steps'] = []

    for (const intent of INTENTS) {
        const match = input.match(intent.pattern)
        if (match) {
            matchedRules.push(intent.intent)
            const args = intent.extract(match)

            switch (intent.intent) {
                case 'NAVIGATE':
                    const route = ROUTE_MAP[args.route] || `/quant`
                    steps.push({ commandId: 'nav:open', args: { route }, label: `Open ${route}` })
                    break
                case 'FOCUS_ENTITY':
                    entities.push({ type: 'ticker', value: args.ticker })
                    steps.push({ commandId: 'filter:setTicker', args, label: `Focus ${args.ticker}` })
                    break
                case 'FILTER_SECTOR':
                    entities.push({ type: 'sector', value: args.sector })
                    steps.push({ commandId: 'filter:setSector', args, label: `Filter sector: ${args.sector}` })
                    break
                case 'SET_THRESHOLD':
                    steps.push({ commandId: 'filter:setHazardThreshold', args, label: `Set hazard > ${args.threshold}` })
                    break
                case 'CLEAR_FILTERS':
                    steps.push({ commandId: 'filter:clear', args: {}, label: 'Clear all filters' })
                    break
                case 'EXPLAIN_EVENT':
                    steps.push({ commandId: 'incidents:open', args, label: 'Open incidents' })
                    steps.push({ commandId: 'incidents:filter', args: { type: args.type }, label: `Show ${args.type} incidents` })
                    break
                case 'COMPARE':
                    steps.push({ commandId: 'nav:open', args: { route: '/compare' }, label: 'Open compare' })
                    if (args.runA && args.runB) {
                        steps.push({ commandId: 'compare:setRuns', args, label: `Compare ${args.runA} vs ${args.runB}` })
                    }
                    break
                case 'REPLAY':
                    steps.push({ commandId: 'replay:setDate', args, label: `Replay ${args.date}` })
                    break
                case 'CONTROL':
                    steps.push({ commandId: `control:${args.action}`, args: {}, label: args.action === 'freeze' ? 'Freeze animation' : 'Resume animation' })
                    break
            }
            break  // Use first match
        }
    }

    // If no match, try fuzzy ticker match
    if (steps.length === 0) {
        const tickerMatch = input.match(/\b([A-Z]{2,5})\b/)
        if (tickerMatch) {
            entities.push({ type: 'ticker', value: tickerMatch[1] })
            steps.push({ commandId: 'filter:setTicker', args: { ticker: tickerMatch[1] }, label: `Focus ${tickerMatch[1]}` })
            matchedRules.push('FUZZY_TICKER')
        }
    }

    const confidence = matchedRules.length > 0 ? 0.8 : 0.2

    return {
        id: `plan_${Date.now()}`,
        confidence,
        steps,
        trace: { tokens, matchedRules, entities },
    }
}

// Safety check - refuse trading commands
export function isSafe(input: string): boolean {
    const unsafePatterns = [
        /\b(buy|sell|order|trade|execute|place)\b/i,
        /\b(leverage|margin)\b/i,
    ]
    return !unsafePatterns.some(p => p.test(input))
}
