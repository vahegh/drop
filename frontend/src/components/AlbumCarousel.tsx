import { useState, useRef } from 'react'

export default function AlbumCarousel({ photos }: { photos: string[] }) {
  const [active, setActive] = useState(0)
  const [animKey, setAnimKey] = useState(0)
  const [dir, setDir] = useState<'left' | 'right'>('left')
  const touchStartX = useRef<number | null>(null)

  function go(next: number, direction: 'left' | 'right') {
    setDir(direction)
    setActive(next)
    setAnimKey(k => k + 1)
  }

  function prev() { go((active - 1 + photos.length) % photos.length, 'right') }
  function next() { go((active + 1) % photos.length, 'left') }

  function handleTouchStart(e: React.TouchEvent) {
    touchStartX.current = e.touches[0].clientX
  }

  function handleTouchEnd(e: React.TouchEvent) {
    if (touchStartX.current === null) return
    const dx = e.changedTouches[0].clientX - touchStartX.current
    touchStartX.current = null
    if (Math.abs(dx) < 30) return
    dx < 0 ? next() : prev()
  }

  const slideIn = dir === 'left'
    ? 'animate-in slide-in-from-right-4 fade-in duration-200'
    : 'animate-in slide-in-from-left-4 fade-in duration-200'

  return (
    <div className="w-full max-w-96 md:max-w-full space-y-2">
      {/* Preload all images for instant switching */}
      <div className="hidden">
        {photos.map((url, i) => <img key={i} src={`${url}=w800`} />)}
      </div>

      {/* Main image */}
      <div
        className="relative w-full rounded-sm overflow-hidden bg-black/30 select-none"
        style={{ aspectRatio: '3/2' }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <img
          key={animKey}
          src={`${photos[active]}=w800`}
          alt={`Photo ${active + 1}`}
          className={`w-full h-full object-contain ${slideIn}`}
          draggable={false}
        />
        {photos.length > 1 && (
          <>
            <button
              onClick={prev}
              className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 flex items-center justify-center text-white text-sm"
              aria-label="Previous"
            >‹</button>
            <button
              onClick={next}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 flex items-center justify-center text-white text-sm"
              aria-label="Next"
            >›</button>
            <span className="absolute bottom-2 right-3 text-xs text-white/60 tabular-nums">
              {active + 1} / {photos.length}
            </span>
          </>
        )}
      </div>

      {/* Thumbnails */}
      {photos.length > 1 && (
        <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          {photos.map((url, i) => (
            <button
              key={i}
              onClick={() => go(i, i > active ? 'left' : 'right')}
              className="flex-none w-14 h-14 rounded-xs overflow-hidden transition-opacity"
              style={{ opacity: i === active ? 1 : 0.45 }}
            >
              <img src={`${url}=w120`} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
