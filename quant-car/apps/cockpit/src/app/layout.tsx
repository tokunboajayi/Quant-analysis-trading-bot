import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'Super QuantDash',
    description: 'Professional quant console with animated visualizations',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" className="dark">
            <body className="bg-[#0a0a0f] text-white antialiased">
                {children}
            </body>
        </html>
    )
}
