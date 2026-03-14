import { useState, useRef, useEffect } from 'react'

export default function AlbumCarousel({ photos }: { photos: string[] }) {
  const [active, setActive] = useState(0)
  const [animKey, setAnimKey] = useState(0)
  const [dir, setDir] = useState<'left' | 'right'>('left')
  const [fsOpen, setFsOpen] = useState(false)
  const [fsClosing, setFsClosing] = useState(false)
  const dialogRef = useRef<HTMLDialogElement>(null)
  const touchStartX = useRef<number | null>(null)
  const touchStartY = useRef<number | null>(null)

  function go(n: number, direction: 'left' | 'right') {
    setDir(direction)
    setActive(n)
    setAnimKey(k => k + 1)
  }

  function prev() { go((active - 1 + photos.length) % photos.length, 'right') }
  function next() { go((active + 1) % photos.length, 'left') }

  function openFs() { dialogRef.current?.showModal(); setFsOpen(true) }
  function closeFs() {
    setFsClosing(true)
    setTimeout(() => { dialogRef.current?.close(); setFsOpen(false); setFsClosing(false) }, 200)
  }

  // Intercept native Escape to play closing animation first
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    function onCancel(e: Event) { e.preventDefault(); closeFs() }
    dialog.addEventListener('cancel', onCancel)
    return () => dialog.removeEventListener('cancel', onCancel)
  }, [])

  // Arrow keys while open
  useEffect(() => {
    if (!fsOpen) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'ArrowLeft') prev()
      if (e.key === 'ArrowRight') next()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [fsOpen, active])

  function handleTouchStart(e: React.TouchEvent) {
    touchStartX.current = e.touches[0].clientX
    touchStartY.current = e.touches[0].clientY
  }

  function handleTouchEnd(e: React.TouchEvent) {
    if (touchStartX.current === null) return
    const dx = e.changedTouches[0].clientX - touchStartX.current
    const dy = e.changedTouches[0].clientY - (touchStartY.current ?? 0)
    touchStartX.current = null
    touchStartY.current = null
    if (fsOpen && Math.abs(dy) > Math.abs(dx) && Math.abs(dy) > 40) { closeFs(); return }
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
        className="relative w-full overflow-hidden bg-black/30 select-none"
        style={{ aspectRatio: '3/2' }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <img
          key={animKey}
          src={`${photos[active]}=w800`}
          alt={`Photo ${active + 1}`}
          className={`w-full h-full object-contain cursor-zoom-in ${slideIn}`}
          draggable={false}
          onClick={openFs}
        />
        {photos.length > 1 && (
          <>
            <button onClick={prev} className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 flex items-center justify-center text-white text-sm" aria-label="Previous">‹</button>
            <button onClick={next} className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 flex items-center justify-center text-white text-sm" aria-label="Next">›</button>
            <span className="absolute bottom-2 right-3 text-xs text-white/60 tabular-nums">{active + 1} / {photos.length}</span>
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
              className="flex-none size-10 rounded-xs overflow-hidden transition-opacity"
              style={{ opacity: i === active ? 1 : 0.45 }}
            >
              <img src={`${url}=w120`} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}

      {/* Fullscreen lightbox — showModal() puts this in browser top layer, no layout impact */}
      <dialog
        ref={dialogRef}
        className={`m-0 p-0 w-screen h-screen max-w-none max-h-none bg-black border-none outline-none touch-none duration-200 ${fsClosing ? 'animate-out fade-out' : fsOpen ? 'animate-in fade-in' : ''}`}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onClick={closeFs}
      >
        <div className="relative w-full h-full flex items-center justify-center" tabIndex={-1} autoFocus>
        <img
          key={animKey}
          src={`${photos[active]}=w800`}
          alt={`Photo ${active + 1}`}
          className={`max-w-full max-h-full object-contain duration-200 ${fsClosing ? 'animate-out zoom-out-95 fade-out' : fsOpen ? `animate-in zoom-in-95 ${slideIn}` : ''}`}
          draggable={false}
          onClick={e => e.stopPropagation()}
        />
        {photos.length > 1 && (
          <>
            <button onClick={e => { e.stopPropagation(); prev() }} className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 flex items-center justify-center text-white text-lg" aria-label="Previous">‹</button>
            <button onClick={e => { e.stopPropagation(); next() }} className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 flex items-center justify-center text-white text-lg" aria-label="Next">›</button>
            <span className="absolute bottom-4 right-4 text-sm text-white/60 tabular-nums">{active + 1} / {photos.length}</span>
          </>
        )}
        <button onClick={closeFs} className="absolute top-3 right-3 w-9 h-9 rounded-full bg-black/60 flex items-center justify-center text-white text-lg" aria-label="Close">✕</button>
        </div>
      </dialog>
    </div>
  )
}
