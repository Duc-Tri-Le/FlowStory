import { useState, useEffect, useRef, useMemo } from 'react'
import {
  Play,
  Pause,
  RotateCcw,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  Type,
  Sparkles,
  Users,
} from 'lucide-react'
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
  location_id?: string
  action_type?: string // "dialogue" | "chase" | "fight" | "solo"
}

export interface StoryCharacter {
  id: string
  name: string
  gender?: string
  color: string
  description?: string
}

interface Props {
  scenes: StorytimeScene[]
  title?: string
  textConfig?: TextOverlayConfig
  characters?: StoryCharacter[]
  onSceneChange?: (sceneIndex: number) => void
}

export type CharacterType = 'detective' | 'suspect' | 'witness' | 'general'

interface ActorProps {
  id: string
  type: CharacterType
  name: string
  color?: string
  posX: number
  posY: number
  scale?: number
  facing: 1 | -1 // 1: facing right, -1: facing left
  isSpeaking: boolean
  mouthOpen: number // 0: closed, 1: mid, 2: wide
  expression: string // "serious" | "shocked" | "thinking" | "talking" | "fear"
  action: 'stand' | 'walk' | 'run' | 'shiver' | 'flee' | 'pursue'
  currentTime: number
  isPlaying: boolean
}

// ─────────────────────────────────────────────────────────────
// Reusable 2D Vector Character Component
// ─────────────────────────────────────────────────────────────
function CharacterActor({
  type,
  name,
  color,
  posX,
  posY,
  scale = 1,
  facing,
  isSpeaking,
  mouthOpen,
  expression,
  action,
  currentTime,
  isPlaying,
}: ActorProps) {
  const isMoving = action === 'walk' || action === 'run' || action === 'flee' || action === 'pursue'
  const isFast = action === 'run' || action === 'flee' || action === 'pursue'
  const freq = isFast ? 12 : 8

  // Legs walk-cycle calculation
  const walkStride = isMoving && isPlaying ? Math.sin(currentTime * freq) : 0
  const strideAmount = isFast ? 36 : 24
  const leftLegSwing = walkStride * strideAmount
  const rightLegSwing = -walkStride * strideAmount

  const liftHeight = isFast ? 16 : 10
  const leftFootLift =
    isMoving && isPlaying ? Math.max(0, Math.sin(currentTime * freq) * liftHeight) : 0
  const rightFootLift =
    isMoving && isPlaying ? Math.max(0, -Math.sin(currentTime * freq) * liftHeight) : 0

  const leftFootX = 135 + leftLegSwing
  const leftFootY = 455 - leftFootLift
  const rightFootX = 205 + rightLegSwing
  const rightFootY = 455 - rightFootLift

  // Dynamic Vertical Bobbing:
  // Step bobbing + speech bobbing (only for the speaker!) + natural breathing
  const walkBob = isMoving && isPlaying ? Math.abs(Math.sin(currentTime * freq)) * (isFast ? 12 : 8) : 0
  const speechBob = isSpeaking && isPlaying && mouthOpen > 0 ? Math.sin(currentTime * 12) * 4 : 0
  const breathBob = Math.sin(currentTime * 2 + posX * 0.05) * 1.6
  const shiverBob = action === 'shiver' && isPlaying ? Math.sin(currentTime * 30) * 2.5 : 0
  const totalBobY = walkBob + speechBob + breathBob + shiverBob + posY

  // Head tilt: responds to speech cadence if speaking, or walking cadence
  const headTilt =
    isSpeaking && isPlaying && mouthOpen > 0
      ? Math.sin(currentTime * 8) * 3
      : isMoving && isPlaying
      ? Math.sin(currentTime * (freq / 2)) * 2
      : Math.sin(currentTime * 1.2 + posX) * 1.2

  // Eye blinking (each character blinks slightly out of phase based on posX)
  const isBlinking = ((currentTime + (posX % 5)) % 3.4) < 0.15

  // Dynamic Arms & Hand Gestures
  const speechWave = isSpeaking && isPlaying && mouthOpen > 0 ? Math.sin(currentTime * 10) * 12 : 0
  const shockJitter =
    (expression === 'shocked' || expression === 'fear') && isPlaying
      ? Math.sin(currentTime * 26) * 3
      : 0
  const thinkTap = isSpeaking && isPlaying ? Math.sin(currentTime * 8) * 3.5 : 0

  // Left Arm Path
  let leftArmPath = ''
  if (action === 'flee') {
    // Both arms flailing forward in panic
    leftArmPath = `M 120,215 Q 60,170 ${70 + Math.sin(currentTime * 12) * 15},130`
  } else if (expression === 'shocked' || expression === 'fear') {
    leftArmPath = `M 120,215 Q 65,${150 + shockJitter} 110,105`
  } else if (expression === 'thinking') {
    leftArmPath = `M 120,215 Q 85,285 135,310`
  } else if (isSpeaking && expression === 'talking') {
    const elbowX = 85 - speechWave * 0.4
    const elbowY = 275 + speechWave * 0.4
    const handX = 95 - speechWave
    const handY = 320 + speechWave * 0.5
    leftArmPath = `M 120,215 Q ${elbowX},${elbowY} ${handX},${handY}`
  } else if (isMoving && isPlaying) {
    const swing = Math.sin(currentTime * freq) * (isFast ? 30 : 20)
    leftArmPath = `M 120,215 Q ${95 - swing * 0.5},${285} ${110 - swing},${345}`
  } else if (type === 'suspect') {
    // Suspect rubbing hands nervously
    leftArmPath = `M 120,215 Q 110,290 155,300`
  } else {
    // Default: relaxed or in coat pocket
    leftArmPath = `M 120,215 Q 90,290 120,340`
  }

  // Right Arm Path
  let rightArmPath = ''
  if (action === 'flee') {
    rightArmPath = `M 220,215 Q 280,170 ${290 - Math.sin(currentTime * 12) * 15},130`
  } else if (expression === 'shocked' || expression === 'fear') {
    rightArmPath = `M 220,215 Q 275,${150 + shockJitter} 230,105`
  } else if (expression === 'thinking') {
    const handX = 195 + thinkTap
    const handY = 160
    rightArmPath = `M 220,215 Q 270,230 ${handX},${handY}`
  } else if (isSpeaking && expression === 'talking') {
    const elbowX = 255 + speechWave * 0.4
    const elbowY = 255 - speechWave * 0.4
    const handX = 275 + speechWave
    const handY = 245 - speechWave * 0.5
    rightArmPath = `M 220,215 Q ${elbowX},${elbowY} ${handX},${handY}`
  } else if (isMoving && isPlaying) {
    const swing = Math.sin(currentTime * freq) * (isFast ? 30 : 20)
    rightArmPath = `M 220,215 Q ${245 + swing * 0.5},${285} ${230 + swing},${345}`
  } else if (type === 'detective') {
    // Detective holds cigarette up near mouth
    rightArmPath = `M 220,215 Q 260,255 208,165`
  } else if (type === 'suspect') {
    // Suspect rubbing hands nervously
    rightArmPath = `M 220,215 Q 230,290 185,300`
  } else {
    rightArmPath = `M 220,215 Q 250,290 220,340`
  }

  // Costume Palette based on Character Color or Type
  const coatFill =
    color ||
    (type === 'detective'
      ? '#1e242c' // Charcoal noir coat
      : type === 'suspect'
      ? '#1e293b' // Deep navy butler suit
      : type === 'witness'
      ? '#4c1d95' // Deep purple witness dress
      : '#334155')

  const collarFill =
    type === 'suspect'
      ? '#f8fafc' // White shirt under vest
      : type === 'witness'
      ? '#a855f7'
      : '#334155'

  return (
    <div
      className="absolute bottom-6 transition-transform duration-75 flex flex-col items-center"
      style={{
        transform: `translate(${posX}px, ${-totalBobY}px) scaleX(${facing}) scale(${scale})`,
        transformOrigin: 'bottom center',
      }}
    >
      {/* Name & Speaking Status Tag */}
      <div
        className={`mb-2 px-2.5 py-0.5 rounded-full text-[10px] font-mono tracking-wider transition-all backdrop-blur-md border ${
          isSpeaking
            ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-md shadow-amber-500/20 animate-pulse font-bold'
            : 'bg-black/60 text-slate-400 border-white/10'
        }`}
        style={{ transform: `scaleX(${facing})` }}
      >
        {isSpeaking ? `🎙️ ${name}` : name}
      </div>

      {/* Head Rotation Wrap */}
      <div
        style={{
          transform: `rotate(${headTilt * facing}deg)`,
          transformOrigin: '170px 180px',
        }}
      >
        <svg
          width="320"
          height="460"
          viewBox="0 0 340 480"
          className="drop-shadow-[0_15px_35px_rgba(0,0,0,0.85)]"
        >
          {/* ── Feet & Legs (Walk/Run Cycle) ── */}
          <path
            d={`M 135,405 L ${leftFootX},${leftFootY - 4}`}
            stroke="#090a0f"
            strokeWidth="7"
            strokeLinecap="round"
          />
          <ellipse
            cx={leftFootX + (facing > 0 ? 5 : -5)}
            cy={leftFootY}
            rx="14"
            ry="5.5"
            fill="#090a0f"
          />

          <path
            d={`M 205,405 L ${rightFootX},${rightFootY - 4}`}
            stroke="#090a0f"
            strokeWidth="7"
            strokeLinecap="round"
          />
          <ellipse
            cx={rightFootX + (facing > 0 ? 5 : -5)}
            cy={rightFootY}
            rx="14"
            ry="5.5"
            fill="#090a0f"
          />

          {/* ── Body Costume ── */}
          <path
            d="M 115,210 L 225,210 L 255,410 L 85,410 Z"
            fill={coatFill}
            stroke="#090a0f"
            strokeWidth="7"
            strokeLinejoin="round"
          />

          {/* Inner Shirt / Vest Details */}
          {type === 'suspect' ? (
            <>
              {/* White V-Shirt */}
              <polygon points="150,210 170,260 190,210" fill={collarFill} stroke="#090a0f" strokeWidth="4" />
              {/* Red Bowtie */}
              <polygon points="160,214 170,222 160,230" fill="#dc2626" stroke="#090a0f" strokeWidth="2.5" />
              <polygon points="180,214 170,222 180,230" fill="#dc2626" stroke="#090a0f" strokeWidth="2.5" />
              <circle cx="170" cy="222" r="3" fill="#b91c1c" />
              {/* Vest Buttons */}
              <circle cx="170" cy="285" r="3" fill="#e2e8f0" />
              <circle cx="170" cy="325" r="3" fill="#e2e8f0" />
              <circle cx="170" cy="365" r="3" fill="#e2e8f0" />
            </>
          ) : type === 'witness' ? (
            <>
              {/* Witness Scarf / Blouse */}
              <path d="M 140,210 Q 170,270 200,210" fill="none" stroke="#e879f9" strokeWidth="6" />
              <line x1="170" y1="260" x2="170" y2="410" stroke="#090a0f" strokeWidth="4" />
            </>
          ) : (
            <>
              {/* Detective Trench Coat Lapels */}
              <line x1="170" y1="210" x2="170" y2="410" stroke="#090a0f" strokeWidth="5" />
              <path d="M 130,210 L 170,270 L 210,210" fill="none" stroke="#090a0f" strokeWidth="6" />
            </>
          )}

          {/* ── Articulated Left Arm ── */}
          <path d={leftArmPath} fill="none" stroke="#090a0f" strokeWidth="7" strokeLinecap="round" />

          {/* ── Articulated Right Arm ── */}
          <path d={rightArmPath} fill="none" stroke="#090a0f" strokeWidth="7" strokeLinecap="round" />

          {/* ── White Circular Head ── */}
          <circle cx="170" cy="115" r="70" fill="#ffffff" stroke="#090a0f" strokeWidth="8" />

          {/* Witness Hairstyle (Bangs & Ponytail) */}
          {type === 'witness' && (
            <>
              {/* Ponytail behind */}
              <path d="M 115,110 C 70,120 70,180 100,195 C 90,160 110,140 120,130" fill="#1e1b4b" stroke="#090a0f" strokeWidth="5" />
              {/* Hair Bangs */}
              <path d="M 115,80 Q 150,55 220,75 Q 190,105 160,95 Z" fill="#1e1b4b" stroke="#090a0f" strokeWidth="4" />
            </>
          )}

          {/* Detective Eye Shadow / Noir Bags */}
          {type === 'detective' && (
            <>
              <path d="M 135,115 A 12,8 0 0,0 155,115" fill="none" stroke="#94a3b8" strokeWidth="3" opacity="0.6" />
              <path d="M 185,115 A 12,8 0 0,0 205,115" fill="none" stroke="#94a3b8" strokeWidth="3" opacity="0.6" />
            </>
          )}

          {/* Suspect Sweat Drop when Nervous */}
          {type === 'suspect' && (expression === 'shocked' || expression === 'fear' || action === 'shiver') && (
            <path
              d={`M 228,88 Q 235,100 231,106 Q 227,110 223,106 Q 220,100 228,88 Z`}
              fill="#38bdf8"
              stroke="#0284c7"
              strokeWidth="2"
            />
          )}

          {/* Eyes (Open Dots vs Blinking Lines) */}
          {isBlinking ? (
            <>
              <line x1="138" y1="108" x2="152" y2="108" stroke="#090a0f" strokeWidth="4" strokeLinecap="round" />
              <line x1="188" y1="108" x2="202" y2="108" stroke="#090a0f" strokeWidth="4" strokeLinecap="round" />
            </>
          ) : (
            <>
              <circle
                cx="145"
                cy="108"
                r={expression === 'shocked' || expression === 'fear' ? 8 : 5.2}
                fill="#090a0f"
              />
              <circle
                cx="195"
                cy="108"
                r={expression === 'shocked' || expression === 'fear' ? 8 : 5.2}
                fill="#090a0f"
              />
            </>
          )}

          {/* Eyebrows */}
          {expression === 'shocked' || expression === 'fear' ? (
            <>
              <path d="M 132,88 Q 145,76 158,88" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
              <path d="M 182,88 Q 195,76 208,88" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
            </>
          ) : expression === 'thinking' ? (
            <>
              <path d="M 134,94 L 158,98" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
              <path d="M 182,88 Q 195,78 208,88" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
            </>
          ) : type === 'suspect' ? (
            // Worried arched eyebrows
            <>
              <path d="M 134,88 Q 146,94 158,92" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
              <path d="M 182,92 Q 194,94 206,88" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
            </>
          ) : (
            // Serious straight slash
            <>
              <path d="M 134,92 L 158,98" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
              <path d="M 206,92 L 182,98" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
            </>
          )}

          {/* Mouth: ONLY moves if this actor is the speaker! */}
          {isSpeaking && mouthOpen === 2 ? (
            <path d="M 152,142 Q 170,166 188,142 Z" fill="#b91c1c" stroke="#090a0f" strokeWidth="4" />
          ) : isSpeaking && mouthOpen === 1 ? (
            <ellipse cx="170" cy="142" rx="10" ry="7" fill="#b91c1c" stroke="#090a0f" strokeWidth="3.5" />
          ) : (
            <path d="M 154,142 Q 170,140 186,142" fill="none" stroke="#090a0f" strokeWidth="5" strokeLinecap="round" />
          )}

          {/* Detective Cigarette & Live Smoke (Only for classic detective) */}
          {type === 'detective' && !color && (
            <>
              <line x1="184" y1="145" x2="216" y2="152" stroke="#e2e8f0" strokeWidth="4.5" strokeLinecap="round" />
              <line x1="214" y1="151.5" x2="220" y2="153" stroke="#ea580c" strokeWidth="4.5" strokeLinecap="round" />
              <path
                d={`M 220,152 Q ${225 + Math.sin(currentTime * 4) * 8},130 ${
                  230 + Math.cos(currentTime * 3) * 10
                },105 T ${228 + Math.sin(currentTime * 5) * 12},75`}
                fill="none"
                stroke="#94a3b8"
                strokeWidth="2.5"
                opacity={0.5 + Math.sin(currentTime * 3) * 0.25}
                strokeDasharray="4 3"
                strokeLinecap="round"
              />
            </>
          )}
        </svg>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Main StorytimePlayer with Multi-Character Stage Engine
// ─────────────────────────────────────────────────────────────
export default function StorytimePlayer({
  scenes,
  textConfig = DEFAULT_TEXT_CONFIG,
  characters = [],
}: Props) {
  const [currentSceneIdx, setCurrentSceneIdx] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [mouthOpen, setMouthOpen] = useState(0)
  const [isMuted, setIsMuted] = useState(false)

  // Stage Preset Mode: 'auto' | 'solo' | 'dialogue' | 'chase' | 'trio'
  const [stagePreset, setStagePreset] = useState<'auto' | 'solo' | 'dialogue' | 'chase' | 'trio'>('auto')
  // Active speaker override for testing: null (follow scene) | 'detective' | 'suspect' | 'witness'
  const [activeSpeakerOverride, setActiveSpeakerOverride] = useState<string | null>(null)

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
      const AudioCtx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
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

  // Animation Loop
  useEffect(() => {
    const dataArray = new Uint8Array(128)

    const loop = () => {
      if (audioRef.current && isPlaying) {
        setCurrentTime(audioRef.current.currentTime)

        if (analyserRef.current) {
          analyserRef.current.getByteFrequencyData(dataArray)
          let sum = 0
          for (let i = 2; i < 24; i++) sum += dataArray[i]
          const avg = sum / 22

          if (avg > 90) {
            setMouthOpen(2)
          } else if (avg > 35) {
            setMouthOpen(1)
          } else {
            setMouthOpen(0)
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

  // Scene Progression & Audio
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
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false))
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

  const sceneDuration = currentScene?.duration_seconds || 5
  const sceneProgress = Math.min(1, currentTime / (sceneDuration || 5))

  // Camera Zoom / Pan
  const cameraTransform = useMemo(() => {
    const mode = currentScene?.camera || 'zoom_in'
    if (mode === 'close') {
      return 'scale(1.35) translate(0%, 5%)'
    } else if (mode === 'zoom_in') {
      const scale = 1.0 + sceneProgress * 0.18
      return `scale(${scale}) translate(0%, 0%)`
    } else if (mode === 'pan_right') {
      const panX = -sceneProgress * 40
      return `scale(1.1) translate(${panX}px, 0%)`
    } else if (mode === 'pan_left') {
      const panX = sceneProgress * 40
      return `scale(1.1) translate(${panX}px, 0%)`
    }
    return 'scale(1.02) translate(0%, 0%)'
  }, [currentScene?.camera, sceneProgress])

  // Subtitles sequence
  const scriptWords = useMemo<SubtitleWord[]>(() => {
    if (!currentScene?.text) return []
    const words = currentScene.text.trim().split(/\s+/).filter(Boolean)
    if (words.length === 0) return []

    const dur = currentScene.duration_seconds || 5.0
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

  const visibleWords = useMemo<SubtitleWord[]>(() => {
    const sourceWords = scriptWords.length > 0 ? scriptWords : currentScene?.subtitles || []
    if (sourceWords.length === 0) return []

    const k = textConfig.wordsPerBatch ?? 3
    if (k <= 0 || k >= sourceWords.length) return sourceWords

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

  const fallbackVisibleText = useMemo(() => {
    return currentScene?.text || '...'
  }, [currentScene?.text])

  // ─────────────────────────────────────────────────────────────
  // Multi-Actor Stage Architecture Simulation (Universal & Dynamic)
  // ─────────────────────────────────────────────────────────────
  // Resolve characters (from props or default palette)
  const resolvedCharacters = useMemo(() => {
    if (characters && characters.length > 0) {
      return characters.map((c, i) => ({
        id: c.id,
        name: c.name,
        color: c.color,
        type: (c.gender === 'female' ? 'witness' : i === 0 ? 'detective' : 'suspect') as CharacterType,
      }))
    }
    // Fallback default cast if no characters passed
    return [
      { id: 'char_1', name: 'Nhân vật 1', color: '#1e242c', type: 'detective' as CharacterType },
      { id: 'char_2', name: 'Nhân vật 2', color: '#1e293b', type: 'suspect' as CharacterType },
      { id: 'char_3', name: 'Nhân vật 3', color: '#4c1d95', type: 'witness' as CharacterType },
    ]
  }, [characters])

  // Check if a specific actor is speaking in the current scene
  const isActorSpeaking = (actorId: string, actorName?: string) => {
    if (activeSpeakerOverride) return activeSpeakerOverride === actorId
    const sp = (currentScene?.speaker || '').toLowerCase().trim()
    if (!sp || sp === 'narrator') {
      // Narrator voice-over: no actor lip-syncs (they remain listeners/actors)
      return false
    }
    const aid = actorId.toLowerCase()
    const aname = (actorName || '').toLowerCase()
    return (
      sp === aid ||
      sp === aname ||
      (aid.length > 2 && sp.includes(aid)) ||
      (aname.length > 2 && sp.includes(aname)) ||
      (sp.length > 2 && aid.includes(sp)) ||
      (sp.length > 2 && aname.includes(sp))
    )
  }

  // Resolve effective stage preset (auto follows scene action_type)
  const effectivePreset =
    stagePreset === 'auto'
      ? (currentScene?.action_type as 'solo' | 'dialogue' | 'chase' | 'trio') || 'dialogue'
      : stagePreset

  // Build the list of active actors on the 2D stage based on effectivePreset and resolvedCharacters
  const stageActors = useMemo(() => {
    const char1 = resolvedCharacters[0] || { id: 'char_1', name: 'Nhân vật 1', color: '#1e242c', type: 'detective' as CharacterType }
    const char2 = resolvedCharacters[1] || { id: 'char_2', name: 'Nhân vật 2', color: '#1e293b', type: 'suspect' as CharacterType }
    const char3 = resolvedCharacters[2] || { id: 'char_3', name: 'Nhân vật 3', color: '#4c1d95', type: 'witness' as CharacterType }

    const isChar1Speaking = isActorSpeaking(char1.id, char1.name)
    const isChar2Speaking = isActorSpeaking(char2.id, char2.name)
    const isChar3Speaking = isActorSpeaking(char3.id, char3.name)

    if (effectivePreset === 'solo') {
      // 1 Solo Actor (Center)
      return [
        {
          id: char1.id,
          type: char1.type,
          name: char1.name,
          color: char1.color,
          posX: Math.sin(currentTime * 0.9) * 8,
          posY: 0,
          scale: 0.95,
          facing: 1 as const,
          isSpeaking: isChar1Speaking,
          expression: currentScene?.expression || 'serious',
          action: (currentScene?.camera === 'pan_right' || currentScene?.camera === 'pan_left' ? 'walk' : 'stand') as 'walk' | 'stand',
        },
      ]
    }

    if (effectivePreset === 'chase') {
      // 2 Actors in Pursuit / Running Away
      // Character 2 fleeing in front (Right)
      const fleeingX = 60 + sceneProgress * 200
      // Character 1 pursuing behind (Left)
      const chasingX = -180 + sceneProgress * 190

      return [
        {
          id: char2.id,
          type: char2.type,
          name: `${char2.name} (Bỏ chạy)`,
          color: char2.color,
          posX: fleeingX,
          posY: -5,
          scale: 0.9,
          facing: 1 as const, // facing right (direction of escape)
          isSpeaking: isChar2Speaking,
          expression: 'fear',
          action: 'flee' as const,
        },
        {
          id: char1.id,
          type: char1.type,
          name: `${char1.name} (Đuổi bắt)`,
          color: char1.color,
          posX: chasingX,
          posY: 0,
          scale: 0.95,
          facing: 1 as const, // chasing right
          isSpeaking: isChar1Speaking,
          expression: 'serious',
          action: 'pursue' as const,
        },
      ]
    }

    if (effectivePreset === 'trio') {
      // 3 Actors on Stage: Char 1 (Left), Char 3 (Center), Char 2 (Right)
      return [
        {
          id: char1.id,
          type: char1.type,
          name: char1.name,
          color: char1.color,
          posX: -220,
          posY: 0,
          scale: 0.88,
          facing: 1 as const,
          isSpeaking: isChar1Speaking,
          expression: isChar1Speaking ? 'talking' : 'serious',
          action: 'stand' as const,
        },
        {
          id: char3.id,
          type: char3.type,
          name: char3.name,
          color: char3.color,
          posX: -10,
          posY: -5,
          scale: 0.86,
          facing: (isChar1Speaking ? -1 : 1) as 1 | -1, // turns to face speaker
          isSpeaking: isChar3Speaking,
          expression: isChar3Speaking ? 'shocked' : 'thinking',
          action: 'stand' as const,
        },
        {
          id: char2.id,
          type: char2.type,
          name: char2.name,
          color: char2.color,
          posX: 210,
          posY: 0,
          scale: 0.88,
          facing: -1 as const, // facing left
          isSpeaking: isChar2Speaking,
          expression: isChar2Speaking ? 'fear' : 'shiver',
          action: (isChar2Speaking ? 'stand' : 'shiver') as 'stand' | 'shiver',
        },
      ]
    }

    // Default: 'dialogue' (2 Actors confronting each other)
    // Character 1 on Left (-180px), Character 2 on Right (+180px)
    const step1 = isChar1Speaking && isPlaying ? sceneProgress * 45 : 0
    const step2 = isChar2Speaking && isPlaying ? -sceneProgress * 30 : 0

    return [
      {
        id: char1.id,
        type: char1.type,
        name: char1.name,
        color: char1.color,
        posX: -180 + step1,
        posY: 0,
        scale: 0.92,
        facing: 1 as const, // facing right towards partner
        isSpeaking: isChar1Speaking,
        expression: isChar1Speaking ? 'talking' : (currentScene?.expression || 'serious'),
        action: (isChar1Speaking && isPlaying ? 'walk' : 'stand') as 'walk' | 'stand',
      },
      {
        id: char2.id,
        type: char2.type,
        name: char2.name,
        color: char2.color,
        posX: 180 + step2,
        posY: 0,
        scale: 0.92,
        facing: -1 as const, // facing left towards partner
        isSpeaking: isChar2Speaking,
        expression: isChar2Speaking ? 'talking' : 'shocked',
        action: (isChar2Speaking && isPlaying ? 'walk' : 'stand') as 'walk' | 'stand',
      },
    ]
  }, [
    effectivePreset,
    resolvedCharacters,
    currentTime,
    sceneProgress,
    currentScene?.expression,
    currentScene?.camera,
    currentScene?.speaker,
    activeSpeakerOverride,
    isPlaying,
  ])

  return (
    <div className="flex flex-col bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
      <audio ref={audioRef} onEnded={handleAudioEnded} muted={isMuted} />

      {/* 16:9 Cinema Viewport */}
      <div className="relative w-full aspect-video bg-black overflow-hidden flex items-center justify-center select-none">
        <div
          className="absolute inset-0 w-full h-full transition-transform duration-100 ease-out flex items-center justify-center"
          style={{ transform: cameraTransform }}
        >
          {/* Atmospheric Noir Background */}
          <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-black opacity-95" />
          <div className="absolute inset-0 opacity-25 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-500/35 via-slate-900/40 to-black" />
          <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-l from-amber-500/10 to-transparent blur-2xl" />
          <div className="absolute inset-0 opacity-15 pointer-events-none bg-[linear-gradient(115deg,transparent_45%,rgba(255,255,255,0.4)_50%,transparent_55%)] bg-[length:60px_100px]" />

          {/* Floor Shadow Line */}
          <div className="absolute bottom-6 inset-x-12 h-6 bg-black/60 blur-md rounded-full pointer-events-none" />

          {/* ── MULTI-CHARACTER STAGE ── */}
          {stageActors.map(actor => (
            <CharacterActor
              key={actor.id}
              id={actor.id}
              type={actor.type}
              name={actor.name}
              color={actor.color}
              posX={actor.posX}
              posY={actor.posY}
              scale={actor.scale}
              facing={actor.facing}
              isSpeaking={actor.isSpeaking}
              mouthOpen={actor.isSpeaking ? mouthOpen : 0}
              expression={actor.expression}
              action={actor.action}
              currentTime={currentTime}
              isPlaying={isPlaying}
            />
          ))}
        </div>

        {/* Karaoke Subtitles */}
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
                  className={`font-bold tracking-wide leading-relaxed ${
                    textConfig.uppercase ? 'uppercase' : ''
                  }`}
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
                        textShadow:
                          '0 2px 4px #000, 0 0 10px #000, 0 0 20px rgba(0,0,0,0.95)',
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

        {/* Live Badges */}
        <div className="absolute top-4 left-4 z-30 flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/70 backdrop-blur-md border border-white/10 text-xs text-slate-300 font-mono shadow-lg">
            <span
              className={`w-2 h-2 rounded-full ${
                isPlaying ? 'bg-amber-400 animate-pulse' : 'bg-slate-500'
              }`}
            />
            <span>SÂN KHẤU: {effectivePreset.toUpperCase()} ({stageActors.length} NHÂN VẬT)</span>
            <span className="text-slate-600">|</span>
            <span className="text-amber-400 font-bold">
              ĐANG NÓI:{' '}
              {(() => {
                const spk = stageActors.find(a => a.isSpeaking)
                if (spk) return spk.name.replace(/\s*\([^)]*\)/, '').toUpperCase()
                if (currentScene?.speaker === 'narrator') return 'NGƯỜI KỂ'
                return 'THUYẾT MINH'
              })()}
            </span>
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
                ? `TEXT: ${textConfig.fontSize}px • ${
                    textConfig.wordsPerBatch === 0
                      ? 'CẢ CÂU'
                      : `${textConfig.wordsPerBatch} TỪ`
                  }`
                : 'TEXT: TẮT'}
            </span>
          </div>
        </div>
      </div>

      {/* Control Bar & Multi-Actor Studio Controls */}
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
        <div className="flex items-center justify-between flex-wrap gap-2">
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
              {isPlaying ? (
                <Pause className="w-4 h-4 fill-current" />
              ) : (
                <Play className="w-4 h-4 fill-current" />
              )}
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
              {isMuted ? (
                <VolumeX className="w-4 h-4 text-red-400" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* ── Multi-Character Studio Controls ── */}
        <div className="pt-3 border-t border-slate-800/80 flex flex-col gap-2 text-xs">
          {/* Row 1: Stage Arrangement Presets */}
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-slate-400 font-medium flex items-center gap-1 mr-1">
                <Users className="w-3.5 h-3.5 text-blue-400" /> Sân khấu 2D:
              </span>
              {[
                { id: 'auto', label: '⚡ Tự Động Theo Cảnh' },
                { id: 'dialogue', label: '👥 2 Người (Đối chất)', desc: '2 nhân vật đối thoại' },
                { id: 'chase', label: '🏃‍♂️ 2 Người (Rượt đuổi)', desc: 'Chạy trốn & rượt đuổi' },
                { id: 'trio', label: '🎭 3 Người (Toàn cảnh)', desc: '3 nhân vật cùng xuất hiện' },
                { id: 'solo', label: '👤 1 Người (Đơn độc)', desc: '1 nhân vật độc thoại' },
              ].map(item => (
                <button
                  key={item.id}
                  onClick={() => setStagePreset(item.id as typeof stagePreset)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                    stagePreset === item.id
                      ? 'bg-blue-500/20 text-blue-300 border border-blue-500/50 font-bold shadow-sm'
                      : 'bg-slate-800/80 hover:bg-slate-800 text-slate-400'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* Row 2: Speaker Selector (Who moves mouth and gesticulates!) */}
          <div className="flex items-center justify-between flex-wrap gap-2 pt-1 border-t border-slate-800/50">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-slate-400 font-medium flex items-center gap-1 mr-1">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Chọn người NÓI (nhép miệng & vung tay):
              </span>
              {stageActors.map(actor => {
                const isSelected = activeSpeakerOverride ? activeSpeakerOverride === actor.id : actor.isSpeaking
                const cleanName = actor.name.replace(/\s*\([^)]*\)/, '')
                return (
                  <button
                    key={actor.id}
                    onClick={() => setActiveSpeakerOverride(actor.id)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 font-bold shadow-sm'
                        : 'bg-slate-800/80 hover:bg-slate-800 text-slate-400'
                    }`}
                  >
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: actor.color || '#f59e0b' }} />
                    <span>🗣️ {cleanName}</span>
                  </button>
                )
              })}

              {activeSpeakerOverride && (
                <button
                  onClick={() => setActiveSpeakerOverride(null)}
                  className="px-2 py-0.5 rounded text-[10px] text-slate-500 hover:text-slate-300 underline ml-1"
                >
                  Theo kịch bản
                </button>
              )}
            </div>

            <div className="text-[11px] text-slate-500 italic">
              * Người không được chọn sẽ giữ vai trò người nghe (ngậm miệng, đứng quan sát hoặc run sợ).
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
