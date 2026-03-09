interface SectionProps {
  title?: string
  subtitle?: string
  sep?: boolean
  children?: React.ReactNode
  className?: string
}

/**
 * Mirrors section() from components.py:
 *   ui.column().classes('gap-2 px-2 py-0 w-full items-center justify-start max-w-96')
 * Title uses section_title().classes('text-center') - always centered.
 * Subtitle uses section_subtitle() - also text-center.
 */
export default function Section({ title, subtitle, sep, children, className = '' }: SectionProps) {
  return (
    <div className={`flex flex-col items-center gap-2 px-2 py-0 w-full max-w-96 ${className}`}>
      {sep && <div className="w-full h-px bg-white/10" />}
      {title && (
        <div className="flex flex-col items-center gap-0 p-2">
          {/* section_title = text-2xl font-medium text-center */}
          <h2 className="text-xl font-medium text-center">{title}</h2>
          {/* section_subtitle = text-center text-sm */}
          {subtitle && <p className="text-sm text-center text-white/60">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  )
}
