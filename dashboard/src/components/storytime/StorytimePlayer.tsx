import { useState, useEffect, useRef, useMemo } from 'react'
import { Play, Pause, RotateCcw, SkipBack, SkipForward, Volume2, VolumeX, Type } from 'lucide-react'
import { type TextOverlayConfig, DEFAULT_TEXT_CONFIG } from './TextOverlayCustomizer'

export interface SubtitleWord {
  word: string
  start: number
  end: number
}

export interface StorytimeScene {
  id: number
  speaker?: string
  text: string
  camera?: string // "close" | "zoom_in" | "pan_right" | "pan_left" | "static"
  expression?: string // "serious" | "shocked" | "thinking" | "talking" | "fear"
  audio_url?: string
  duration_seconds: number
  duration_frames: number
  subtitles?: SubtitleWord[]
  background_prompt?: string
  voice?: string
  location_id?: string // Reference to a shared location for background reuse
}

interface Props {
  scenes: StorytimeScene[]
  title?: string
  textConfig?: TextOverlayConfig
  onSceneChange?: (sceneIndex: number) => void
}

export default function StorytimePlayer({ scenes, textConfig = DEFAULT_TEXT_CONFIG }: Props) {
  const [currentSceneIdx, setCurrentSceneIdx] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0) // Seconds in current scene
  const [mouthOpen, setMouthOpen] = useState(0) // 0: closed, 1: mid, 2: wide open
  const [isMuted, setIsMuted] = useState(false)

  const audioRef = useRef<HTMLAudioElement | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceNodeRef = useRef<MediaElementAudioSourceNode | null>(null)
  const animFrameRef = useRef<number | null>(null)

  const currentScene = scenes[currentSceneIdx] || null

  // Setup Web Audio API FFT Analyser for Real-time Lip Sync
  const setupAudioContext = () => {
    if (!audioRef.current) return
    if (!audioContextRef.current) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      const ctx = new AudioCtx()
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.65

      const source = ctx.createMediaElementSource(audioRef.current)
      source.connect(analyser)
      analyser.connect(ctx.destination)

      audioContextRef.current = ctx
      analyserRef.current = analyser
      sourceNodeRef.current = source
    }
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume()
    }
  }

  // Animation Loop: Updates time, camera zoom, and FFT mouth sync
  useEffect(() => {
    const dataArray = new Uint8Array(128)

    const loop = () => {
      if (audioRef.current && isPlaying) {
        setCurrentTime(audioRef.current.currentTime)

        // FFT Volume measurement for mouth shapes
        if (analyserRef.current) {
          analyserRef.current.getByteFrequencyData(dataArray)
          // Average low-mid speech frequencies (bins 2 to 24, approx 150Hz - 2000Hz)
          let sum = 0
          for (let i = 2; i < 24; i++) sum += dataArray[i]
          const avg = sum / 22

          if (avg > 90) {
            setMouthOpen(2) // Wide open
          } else if (avg > 35) {
            setMouthOpen(1) // Half open
          } else {
            setMouthOpen(0) // Closed
          }
        }
      }
      animFrameRef.current = requestAnimationFrame(loop)
    }

    animFrameRef.current = requestAnimationFrame(loop)
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    }
  }, [isPlaying])

  // Scene Progression & Audio Handling
  useEffect(() => {
    if (!currentScene) return
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setCurrentTime(0)
      if (currentScene.audio_url) {
        audioRef.current.src = currentScene.audio_url
        if (isPlaying) {
          setupAudioContext()
          audioRef.current.play().catch(() => setIsPlaying(false))
        }
      }
    }
  }, [currentSceneIdx, currentScene?.audio_url])

  const togglePlay = () => {
    if (!audioRef.current) return
    setupAudioContext()
    if (isPlaying) {
      audioRef.current.pause()
      setIsPlaying(false)
    } else {
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false))
    }
  }

  const handleAudioEnded = () => {
    if (currentSceneIdx < scenes.length - 1) {
      setCurrentSceneIdx(prev => prev + 1)
    } else {
      setIsPlaying(false)
      setCurrentTime(0)
    }
  }

  // Calculate Camera Zoom / Pan Transform based on camera mode and progress
  const sceneProgress = currentScene ? Math.min(1, currentTime / (currentScene.duration_seconds || 5)) : 0
  const cameraTransform = useMemo(() => {
    if (!currentScene) return 'scale(1) translate(0px, 0px)'
    const mode = currentScene.camera || 'zoom_in'

    if (mode === 'close') {
      // Punch-in tight close-up on head
      return 'scale(1.45) translate(0%, 8%)'
    } else if (mode === 'zoom_in') {
      // Slow dramatic Ken Burns zoom in
      const scale = 1.0 + sceneProgress * 0.22
      return `scale(${scale}) translate(0%, 0%)`
    } else if (mode === 'pan_right') {
      const panX = -sceneProgress * 40
      return `scale(1.15) translate(${panX}px, 0%)`
    } else if (mode === 'pan_left') {
      const panX = sceneProgress * 40
      return `scale(1.15) translate(${panX}px, 0%)`
    }
    return 'scale(1.05) translate(0%, 0%)'
  }, [currentScene, sceneProgress])

  // Body bobbing (sin wave) when speaking
  const bodyBobY = isPlaying && mouthOpen > 0 ? Math.sin(currentTime * 12) * 5 : 0
  const headTilt = isPlaying && mouthOpen > 0 ? Math.sin(currentTime * 8) * 2.5 : 0

  // Generate word sequence directly from the script text (kịch bản gốc) without needing Speech-To-Text
  const scriptWords = useMemo<SubtitleWord[]>(() => {
    if (!currentScene?.text) return []
    const words = currentScene.text.trim().split(/\s+/).filter(Boolean)
    if (words.length === 0) return []

    const dur = currentScene.duration_seconds || 5.0
    // Proportional timing based on word character length
    const totalChars = words.reduce((acc, w) => acc + Math.max(1, w.length), 0)
    let cursor = 0.12
    const usableTime = Math.max(0.5, dur - 0.28)

    return words.map(w => {
      const weight = Math.max(1, w.length) / totalChars
      const wDur = Math.max(0.12, weight * usableTime)
      const start = cursor
      const end = cursor + wDur
      cursor = end
      return { word: w, start, end }
    })
  }, [currentScene?.text, currentScene?.duration_seconds])

  // Chunk subtitles into groups of N words according to textConfig.wordsPerBatch directly from the script!
  const visibleWords = useMemo<SubtitleWord[]>(() => {
    const sourceWords = scriptWords.length > 0 ? scriptWords : (currentScene?.subtitles || [])
    if (sourceWords.length === 0) return []

    const k = textConfig.wordsPerBatch ?? 3
    if (k <= 0 || k >= sourceWords.length) {
      return sourceWords
    }

    const chunks: SubtitleWord[][] = []
    for (let i = 0; i < sourceWords.length; i += k) {
      chunks.push(sourceWords.slice(i, i + k))
    }

    const activeIdx = chunks.findIndex((_, idx) => {
      const nextChunk = chunks[idx + 1]
      if (!nextChunk) return true
      return currentTime < nextChunk[0].start
    })

    return chunks[Math.max(0, activeIdx)] || chunks[0]
  }, [scriptWords, currentScene?.subtitles, currentTime, textConfig.wordsPerBatch])

  // Fallback string if needed
  const fallbackVisibleText = useMemo(() => {
    return currentScene?.text || '...'
  }, [currentScene?.text])

  return (
    <div className="flex flex-col bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        onEnded={handleAudioEnded}
        muted={isMuted}
      />

      {/* 16:9 Cinema Viewport */}
      <div className="relative w-full aspect-video bg-black overflow-hidden flex items-center justify-center select-none">
        {/* World Layer with Camera Transform */}
        <div
          className="absolute inset-0 w-full h-full transition-transform duration-100 ease-out flex items-center justify-center"
          style={{ transform: cameraTransform }}
        >
          {/* 1. Atmospheric Noir Background */}
          <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-black opacity-95" />
          
          {/* Subtle Noir Window / Shadow blinds */}
          <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-500/30 via-slate-900/40 to-black" />
          <div className="absolute top-0 right-0 w-72 h-full bg-gradient-to-l from-amber-500/10 to-transparent blur-2xl" />

          {/* Rain streak lines */}
          <div className="absolute inset-0 opacity-15 pointer-events-none bg-[linear-gradient(115deg,transparent_45%,rgba(255,255,255,0.4)_50%,transparent_55%)] bg-[length:60px_100px]" />

          {/* 2. 2D Minimalist Doodle Stickman Character (SVG) */}
          <div
            className="relative z-10 transition-transform duration-75"
            style={{ transform: `translateY(${bodyBobY}px) rotate(${headTilt}deg)` }}
          >
            <svg width="340" height="460" viewBox="0 0 340 460" className="drop-shadow-[0_15px_35px_rgba(0,0,0,0.85)]">
              {/* Charcoal Trench Coat / Body */}
              <path
                d="M 115,210 L 225,210 L 255,410 L 85,410 Z"
                fill="#1e242c"
                stroke="#090a0f"
                strokeWidth="7"
                strokeLinejoin="round"
              />
              {/* Coat Lapel Lines */}
              <line x1="170" y1="210" x2="170" y2="410" stroke="#090a0f" strokeWidth="5" />
              <path d="M 130,210 L 170,270 L 210,210" fill="none" stroke="#090a0f" strokeWidth="6" />

              {/* Stick Arms */}
              <path d="M 120,230 Q 80,300 110,350" fill="none" stroke="#090a0f" strokeWidth="7" strokeLinecap="round" />
              <path d="M 220,230 Q 260,300 230,350" fill="none" stroke="#090a0f" strokeWidth="7" strokeLinecap="round" />

              {/* Pure White Circular Head */}
              <circle
                cx="170"
                cy="115"
                r="70"
                fill="#ffffff"
                stroke="#090a0f"
                strokeWidth="8"
              />

              {/* Detective Dark Eye Circles (Noir Mood) */}
              <path d="M 135,115 A 12,8 0 0,0 155,115" fill="none" stroke="#94a3b8" strokeWidth="3" opacity="0.6" />
              <path d="M 185,115 A 12,8 0 0,0 205,115" fill="none" stroke="#94a3b8" strokeWidth="3" opacity="0.6" />

              {/* Dot Eyes */}
              <circle cx="145" cy="108" r={currentScene?.expression === 'shocked' ? 7.5 : 5} fill="#090a0f" />
              <circle cx="195" cy="108" r={currentScene?.expression === 'shocked' ? 7.5 : 5} fill="#090a0f" />

              {/* Eyebrows based on Expression */}
              {currentScene?.expression === 'shocked' ? (
                // Raised arched eyebrows
                <>
                  <path d="M 132,90 Q 145,80 158,90" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
                  <path d="M 182,90 Q 195,80 208,90" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
                </>
              ) : currentScene?.expression === 'thinking' ? (
                // One raised, one furrowed
                <>
                  <path d="M 134,94 L 158,98" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
                  <path d="M 182,88 Q 195,80 208,90" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
                </>
              ) : (
                // Serious straight slash eyebrows
                <>
                  <path d="M 134,92 L 158,98" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
                  <path d="M 206,92 L 182,98" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
                </>
              )}

              {/* Dynamic Lip-Sync Mouth */}
              {mouthOpen === 2 ? (
                // Wide Open Mouth (high energy)
                <path d="M 152,142 Q 170,165 188,142 Z" fill="#b91c1c" stroke="#090a0f" strokeWidth="4" />
              ) : mouthOpen === 1 ? (
                // Medium Oval Mouth
                <ellipse cx="170" cy="142" rx="10" ry="7" fill="#b91c1c" stroke="#090a0f" strokeWidth="3.5" />
              ) : (
                // Closed Flat Serious Line Mouth
                <path d="M 154,142 Q 170,140 186,142" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
              )}

              {/* Detective Cigarette */}
              <line x1="184" y1="145" x2="216" y2="152" stroke="#e2e8f0" strokeWidth="4.5" strokeLinecap="round" />
              <line x1="214" y1="151.5" x2="220" y2="153" stroke="#ea580c" strokeWidth="4.5" strokeLinecap="round" />
              {/* Cigarette smoke wisps */}
              <path d="M 222,152 Q 228,135 222,120 T 235,95" fill="none" stroke="#94a3b8" strokeWidth="2.5" opacity="0.45" strokeDasharray="3 3" />
            </svg>
          </div>
        </div>

        {/* 3. Optional Karaoke Subtitle Overlay Bar */}
        {textConfig.enabled && (
          <div
            className={`absolute inset-x-8 z-30 flex justify-center pointer-events-none transition-all duration-200 ${
              textConfig.position === 'top'
                ? 'top-8'
                : textConfig.position === 'center'
                ? 'top-1/2 -translate-y-1/2'
                : 'bottom-6'
            }`}
          >
            <div className="max-w-3xl text-center px-4 py-1.5 transition-all">
              {visibleWords && visibleWords.length > 0 ? (
                <p
                  className={`font-bold tracking-wide leading-relaxed ${textConfig.uppercase ? 'uppercase' : ''}`}
                  style={{
                    fontSize: `${textConfig.fontSize}px`,
                    fontFamily:
                      textConfig.fontFamily === 'impact'
                        ? "'Impact', 'Arial Black', sans-serif"
                        : textConfig.fontFamily === 'serif'
                        ? "'Georgia', 'Times New Roman', serif"
                        : textConfig.fontFamily === 'comic'
                        ? "'Comic Sans MS', cursive, sans-serif"
                        : textConfig.fontFamily === 'mono'
                        ? "'Courier New', monospace"
                        : "'Geist', system-ui, sans-serif",
                    color: textConfig.textColor,
                    textShadow: '0 2px 4px #000, 0 0 10px #000, 0 0 20px rgba(0,0,0,0.95)',
                  }}
                >
                  {visibleWords.map((wordObj, i) => (
                    <span
                      key={i}
                      className="inline-block mr-2"
                      style={{
                        color: textConfig.textColor,
                        fontWeight: 700,
                        textShadow: '0 2px 4px #000, 0 0 10px #000, 0 0 20px rgba(0,0,0,0.95)',
                      }}
                    >
                      {wordObj.word}
                    </span>
                  ))}
                </p>
              ) : (
                <p
                  className={`font-medium ${textConfig.uppercase ? 'uppercase' : ''}`}
                  style={{
                    fontSize: `${textConfig.fontSize}px`,
                    color: textConfig.textColor,
                    textShadow: '0 2px 4px #000, 0 0 10px #000, 0 0 20px rgba(0,0,0,0.95)',
                  }}
                >
                  {fallbackVisibleText}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Camera & Text Overlay Indicator Badges */}
        <div className="absolute top-4 left-4 z-30 flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-md border border-white/10 text-xs text-slate-300 font-mono">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span>CAM: {(currentScene?.camera || 'ZOOM_IN').toUpperCase()}</span>
            <span className="text-slate-600">|</span>
            <span>EXP: {(currentScene?.expression || 'SERIOUS').toUpperCase()}</span>
          </div>

          <div
            className={`px-2.5 py-1.5 rounded-lg backdrop-blur-md border text-xs font-mono flex items-center gap-1.5 ${
              textConfig.enabled
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                : 'bg-black/60 border-white/10 text-slate-500'
            }`}
          >
            <Type className="w-3 h-3" />
            <span>
              {textConfig.enabled
                ? `TEXT: ${textConfig.fontSize}px • ${textConfig.wordsPerBatch === 0 ? 'CẢ CÂU' : `${textConfig.wordsPerBatch} TỪ`}`
                : 'TEXT: TẮT'}
            </span>
          </div>
        </div>
      </div>

      {/* Control Bar */}
      <div className="p-4 bg-slate-900 border-t border-slate-800 flex flex-col gap-3">
        {/* Timeline Slider */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400 w-12 text-right">
            {currentTime.toFixed(1)}s
          </span>
          <input
            type="range"
            min={0}
            max={currentScene?.duration_seconds || 5}
            step={0.05}
            value={currentTime}
            onChange={e => {
              const t = parseFloat(e.target.value)
              setCurrentTime(t)
              if (audioRef.current) audioRef.current.currentTime = t
            }}
            className="flex-1 accent-amber-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
          />
          <span className="text-xs font-mono text-slate-500 w-12">
            {(currentScene?.duration_seconds || 0).toFixed(1)}s
          </span>
        </div>

        {/* Playback Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentSceneIdx(prev => Math.max(0, prev - 1))}
              disabled={currentSceneIdx === 0}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-40"
              title="Cảnh trước"
            >
              <SkipBack className="w-4 h-4" />
            </button>

            <button
              onClick={togglePlay}
              className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold flex items-center gap-2 shadow-lg shadow-amber-500/20 active:scale-95 transition-all"
            >
              {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
              <span>{isPlaying ? 'Tạm Dừng' : 'Phát Thử'}</span>
            </button>

            <button
              onClick={() => {
                if (audioRef.current) audioRef.current.currentTime = 0
                setCurrentTime(0)
              }}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              title="Phát lại cảnh này"
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            <button
              onClick={() => setCurrentSceneIdx(prev => Math.min(scenes.length - 1, prev + 1))}
              disabled={currentSceneIdx === scenes.length - 1}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-40"
              title="Cảnh tiếp theo"
            >
              <SkipForward className="w-4 h-4" />
            </button>

            <span className="text-xs text-slate-400 font-medium ml-3">
              Cảnh {currentSceneIdx + 1} / {scenes.length}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsMuted(prev => !prev)}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              title={isMuted ? 'Bật tiếng' : 'Tắt tiếng'}
            >
              {isMuted ? <VolumeX className="w-4 h-4 text-red-400" /> : <Volume2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
