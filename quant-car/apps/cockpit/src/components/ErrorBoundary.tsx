'use client'
import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
    children?: ReactNode
    fallback?: ReactNode
}

interface State {
    hasError: boolean
    error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    }

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error }
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo)
    }

    public render() {
        if (this.state.hasError) {
            return (
                this.props.fallback || (
                    <div className="flex flex-col items-center justify-center h-full p-4 bg-gray-900 border border-red-900/50 rounded-lg text-center">
                        <div className="text-red-500 text-3xl mb-2">⚠️</div>
                        <h3 className="text-lg font-bold text-red-200 mb-1">Visual Error</h3>
                        <p className="text-sm text-gray-400 mb-4 max-w-sm">
                            The visualization crashed. This usually happens due to WebGL context loss or a resize glitch.
                        </p>
                        <button
                            className="px-4 py-2 bg-red-800/20 hover:bg-red-800/40 text-red-200 rounded text-sm transition"
                            onClick={() => this.setState({ hasError: false })}
                        >
                            Reload Visuals
                        </button>
                    </div>
                )
            )
        }

        return this.props.children
    }
}
