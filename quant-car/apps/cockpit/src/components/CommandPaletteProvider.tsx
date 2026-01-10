'use client'
/**
 * Command Palette Provider - Global ⌘K handler
 */
import { ReactNode } from 'react'
import CommandPalette, { useCommandPalette } from '@/command/CommandPalette'

export default function CommandPaletteProvider({ children }: { children: ReactNode }) {
    const { isOpen, close } = useCommandPalette()

    return (
        <>
            {children}
            <CommandPalette isOpen={isOpen} onClose={close} />
        </>
    )
}
