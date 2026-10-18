import { useState, useEffect } from 'react'
import { Sparkles, Wand2, RefreshCw, Download, FileText, Mic, Film, CheckCircle2 } from 'lucide-react'
import StorytimePlayer, { type StorytimeScene } from '../components/storytime/StorytimePlayer'
import TextOverlayCustomizer, { type TextOverlayConfig, DEFAULT_TEXT_CONFIG } from '../components/storytime/TextOverlayCustomizer'
import { fetchAPI, postAPI } from '../api/client'

const SAMPLE_DETECTIVE_STORY = `Đêm hôm đó, một vụ án mạng kỳ lạ đã xảy ra ngay tại căn phòng số bảy.
Cửa phòng bị khóa trái từ bên trong, không có bất kỳ dấu vết cạy phá nào.
Nạn nhân là một triệu phú già, nằm gục bên bàn làm việc với chiếc đồng hồ vỡ nát.
Kỳ lạ thay, kim đồng hồ đã dừng lại chính xác ở thời điểm mười một giờ mười lăm phút.
Mọi người trong ngôi nhà đều có chứng cứ ngoại phạm, ngoại trừ người quản gia vừa biến mất bí ẩn.`

interface VoiceOption {
  id: string
  name: string
  engine: string
  status: string
  description?: string
}

interface VoiceGroup {
  label: string
  engine: string
  online?: boolean
  voices: VoiceOption[]
}

const DEFAULT_VOICE_GROUPS: VoiceGroup[] = [
  {
    label: '⚡ Edge-TTS (Cloud Sẵn Sàng)',
    engine: 'edge',
    voices: [
      { id: 'vi-VN-NamMinhNeural', name: '🎙️ Nam Minh (Trầm ấm Noir)', engine: 'edge', status: 'ready' },
      { id: 'vi-VN-HoaiMyNeural', name: '🎙️ Hoài My (Cảm xúc Drama)', engine: 'edge', status: 'ready' },
    ],
  },
  {
    label: '🎭 GPT-SoVITS (Voice Clone Cục Bộ)',
    engine: 'gpt_sovits',
    voices: [
      { id: 'gpt:thanh_tra_minh', name: '🎭 Thanh Tra Minh (Mẫu)', engine: 'gpt_sovits', status: 'offline' },
      { id: 'gpt:sat_nhan_giau_mat', name: '🎭 Kẻ Giấu Mặt (Mẫu)', engine: 'gpt_sovits', status: 'offline' },
    ],
  },
]

export default function StorytimePage() {
  const [storyText, setStoryText] = useState(SAMPLE_DETECTIVE_STORY)
  const [voice, setVoice] = useState('vi-VN-NamMinhNeural')
  const [voiceGroups, setVoiceGroups] = useState<VoiceGroup[]>(DEFAULT_VOICE_GROUPS)
  const [scenes, setScenes] = useState<StorytimeScene[]>([])
  const [textConfig, setTextConfig] = useState<TextOverlayConfig>(DEFAULT_TEXT_CONFIG)
  const [isBreakingDown, setIsBreakingDown] = useState(false)
  const [isGeneratingTTS, setIsGeneratingTTS] = useState(false)
  const [activePackageId, setActivePackageId] = useState<string | null>(null)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const [regeneratingIdx, setRegeneratingIdx] = useState<number | null>(null)

  // Load sample package and available voices on mount
  useEffect(() => {
    fetchAPI<{ ok: boolean; package: { scenes: StorytimeScene[] } }>('/api/storytime/sample-package')
      .then(res => {
        if (res.ok && res.package?.scenes?.length) {
          setScenes(res.package.scenes)
        }
      })
      .catch(() => {})

    fetchAPI<{ ok: boolean; groups?: VoiceGroup[] }>('/api/storytime/voices')
      .then(res => {
        if (res.ok && res.groups?.length) {
          setVoiceGroups(res.groups)
        }
      })
      .catch(() => {})
  }, [])

  // 1. AI Script Breakdown
  const handleBreakdown = async () => {
    if (!storyText.trim()) return
    setIsBreakingDown(true)
    setStatusMsg('Đang bóc tách kịch bản thành từng cảnh 10-25 từ...')
    try {
      const res = await postAPI<{ ok: boolean; spec: { scenes: StorytimeScene[] } }>('/api/storytime/breakdown', {
        story_text: storyText,
        genre: 'trinh_tham',
      })
      if (res.ok && res.spec?.scenes) {
        setScenes(res.spec.scenes)
        setStatusMsg(`Đã chia kịch bản thành ${res.spec.scenes.length} cảnh. Hãy bấm "Tạo Giọng & Phụ Đề"!`)
      }
    } catch (e) {
      setStatusMsg(`Lỗi bóc tách: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setIsBreakingDown(false)
    }
  }

  // 2. Batch TTS with Per-Scene Voice Support
  const handleBuildPackage = async () => {
    if (!scenes.length) return
    setIsGeneratingTTS(true)
    setStatusMsg('Đang sinh giọng đọc Edge-TTS cho từng phân cảnh và đồng bộ kịch bản...')
    try {
      const res = await postAPI<{ ok: boolean; package: { package_id: string; scenes: StorytimeScene[] } }>(
        '/api/storytime/build-package',
        {
          title: 'Vụ Án Mới',
          genre: 'trinh_tham',
          voice: voice,
          scenes: scenes.map((s, idx) => ({
            display_order: idx,
            speaker: s.speaker || 'thanh_tra',
            text: s.text,
            camera: s.camera || 'zoom_in',
            expression: s.expression || 'serious',
            background_prompt: s.background_prompt,
            voice: s.voice || voice,
          })),
        }
      )
      if (res.ok && res.package) {
        setScenes(res.package.scenes)
        setActivePackageId(res.package.package_id)
        setStatusMsg('Đã tạo xong Giọng đọc theo từng phân cảnh! Bấm "Phát Thử" bên phải để xem.')
      }
    } catch (e) {
      setStatusMsg(`Lỗi xử lý: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setIsGeneratingTTS(false)
    }
  }

  // 3. Single Scene Voice Generation
  const handleRegenSingleScene = async (idx: number) => {
    const sc = scenes[idx]
    if (!sc || !sc.text.trim()) return
    setRegeneratingIdx(idx)
    setStatusMsg(`Đang sinh giọng cho phân cảnh ${idx + 1}...`)
    try {
      const targetVoice = sc.voice || voice
      const res = await postAPI<{ ok: boolean; audio_url: string; duration: number }>('/api/storytime/tts', {
        text: sc.text,
        voice: targetVoice,
      })
      if (res.ok && res.audio_url) {
        updateScene(idx, {
          audio_url: res.audio_url,
          duration_seconds: res.duration + 0.35,
          voice: targetVoice,
        })
        setStatusMsg(`Đã tạo xong giọng đọc cho phân cảnh ${idx + 1}!`)
      }
    } catch (e) {
      setStatusMsg(`Lỗi tạo giọng cảnh ${idx + 1}: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setRegeneratingIdx(null)
    }
  }

  const updateScene = (idx: number, updates: Partial<StorytimeScene>) => {
    setScenes(prev => {
      const next = [...prev]
      next[idx] = { ...next[idx], ...updates }
      return next
    })
  }

  return (
    <div className="p-6 max-w-7xl mx-auto flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
              <Film className="w-6 h-6 text-amber-500" />
              Noir Storytime Studio
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Limited 2D Animatic
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Sản xuất video hoạt hình trinh thám/drama tối giản: Giọng đọc Edge-TTS, Nhép miệng FFT và Phụ đề Whisper từng từ.
          </p>
        </div>

        {statusMsg && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-amber-300">
            <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{statusMsg}</span>
          </div>
        )}
      </div>

      {/* Main Studio Workspace: Scene Editor (1/3: 4 cols) + Cinema Player (2/3: 8 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Script & Scene Editor (4 cols = 1/3) */}
        <div className="lg:col-span-4 flex flex-col gap-5">
          {/* 1. Raw Story Input Card */}
          <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-xl backdrop-blur-sm">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <FileText className="w-4 h-4 text-amber-400" />
                Kịch Bản Truyện Thô
              </label>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Giọng đọc:</span>
                <select
                  value={voice}
                  onChange={e => setVoice(e.target.value)}
                  className="bg-slate-950 text-slate-200 text-xs px-2.5 py-1 rounded-lg border border-slate-700 outline-none max-w-[200px] truncate"
                >
                  {voiceGroups.map(group => (
                    <optgroup key={group.label} label={group.label} className="bg-slate-900 text-slate-400 font-semibold">
                      {group.voices.map(v => (
                        <option key={v.id} value={v.id} className="bg-slate-950 text-slate-200">
                          {v.name} {v.status === 'offline' ? '(Chưa bật server)' : ''}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>
            </div>

            <textarea
              rows={4}
              value={storyText}
              onChange={e => setStoryText(e.target.value)}
              placeholder="Dán nội dung truyện trinh thám hoặc câu chuyện cần làm video vào đây..."
              className="w-full bg-slate-950 text-slate-200 text-sm p-3.5 rounded-xl border border-slate-800 focus:border-amber-500/50 outline-none resize-none leading-relaxed"
            />

            <div className="flex items-center justify-between mt-3 pt-2">
              <button
                onClick={() => setStoryText(SAMPLE_DETECTIVE_STORY)}
                className="text-xs text-slate-400 hover:text-slate-200 underline"
              >
                Tải kịch bản mẫu trinh thám
              </button>

              <button
                onClick={handleBreakdown}
                disabled={isBreakingDown || !storyText.trim()}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs flex items-center gap-2 transition-all disabled:opacity-40"
              >
                {isBreakingDown ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Wand2 className="w-3.5 h-3.5 text-amber-400" />}
                <span>{isBreakingDown ? 'Đang phân tích...' : 'AI Bóc Tách Cảnh (10-25 từ)'}</span>
              </button>
            </div>
          </div>

          {/* 2. Scene List Editor */}
          <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-200">
                  Danh Sách Phân Cảnh ({scenes.length} cảnh)
                </h3>
                <p className="text-xs text-slate-500">Mỗi cảnh được tối ưu 10-25 từ để khớp nhịp đọc</p>
              </div>

              <button
                onClick={handleBuildPackage}
                disabled={isGeneratingTTS || !scenes.length}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs flex items-center gap-2 shadow-lg shadow-amber-500/20 disabled:opacity-40"
              >
                {isGeneratingTTS ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Mic className="w-3.5 h-3.5" />}
                <span>{isGeneratingTTS ? 'Đang sinh audio...' : '🎙️ Tạo Giọng & Phụ Đề Tất Cả'}</span>
              </button>
            </div>

            <div className="flex flex-col gap-3 max-h-[480px] overflow-y-auto pr-1">
              {scenes.map((scene, idx) => {
                const words = (scene.text || '').trim().split(/\s+/).filter(Boolean).length
                const isOptimal = words >= 10 && words <= 25

                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col gap-2.5"
                  >
                    <div className="flex flex-col gap-2">
                      {/* Card Header Row 1: Index, Speaker, Status & Single-TTS Button */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="w-5 h-5 rounded-md bg-slate-800 text-slate-300 font-mono text-[11px] flex items-center justify-center font-bold shrink-0">
                            {idx + 1}
                          </span>
                          <span className="text-xs font-semibold text-slate-300 truncate">
                            {scene.speaker === 'thanh_tra' ? 'Thanh tra Minh' : 'Người kể'}
                          </span>
                          {scene.audio_url && (
                            <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium shrink-0">
                              <CheckCircle2 className="w-3 h-3" />
                              {scene.duration_seconds?.toFixed(1)}s
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-1.5 shrink-0">
                          <span
                            className={`text-[10px] font-mono px-1.5 py-0.5 rounded-md ${
                              isOptimal ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                            }`}
                          >
                            {words} từ
                          </span>

                          <button
                            onClick={() => handleRegenSingleScene(idx)}
                            disabled={regeneratingIdx === idx || !scene.text.trim()}
                            className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 hover:bg-slate-700 text-amber-300 hover:text-white flex items-center gap-1 border border-slate-700 transition-all disabled:opacity-40"
                            title="Tạo lại giọng đọc riêng cho phân cảnh này"
                          >
                            {regeneratingIdx === idx ? (
                              <RefreshCw className="w-2.5 h-2.5 animate-spin" />
                            ) : (
                              <Mic className="w-2.5 h-2.5" />
                            )}
                            <span>Sinh giọng</span>
                          </button>
                        </div>
                      </div>

                      {/* Card Controls Row 2: Voice, Camera, Expression */}
                      <div className="grid grid-cols-3 gap-1.5 pt-0.5">
                        {/* Per-scene Voice Selector */}
                        <select
                          value={scene.voice || voice}
                          onChange={e => updateScene(idx, { voice: e.target.value })}
                          className="bg-slate-900 text-slate-200 text-[11px] px-1.5 py-1 rounded border border-slate-700 outline-none truncate font-medium"
                          title="Chọn giọng đọc riêng cho phân cảnh này"
                        >
                          {voiceGroups.map(group => (
                            <optgroup key={group.label} label={group.label} className="bg-slate-950 text-slate-400 text-[10px]">
                              {group.voices.map(v => (
                                <option key={v.id} value={v.id} className="bg-slate-900 text-slate-200 text-[11px]">
                                  {v.name} {v.status === 'offline' ? '(Chưa bật server)' : ''}
                                </option>
                              ))}
                            </optgroup>
                          ))}
                        </select>

                        {/* Camera Selector */}
                        <select
                          value={scene.camera || 'zoom_in'}
                          onChange={e => updateScene(idx, { camera: e.target.value })}
                          className="bg-slate-900 text-slate-300 text-[11px] px-1.5 py-1 rounded border border-slate-700 outline-none truncate"
                        >
                          <option value="zoom_in">CAM: Zoom In</option>
                          <option value="close">CAM: Cận mặt</option>
                          <option value="pan_right">CAM: Pan Phải</option>
                          <option value="static">CAM: Tĩnh</option>
                        </select>

                        {/* Expression Selector */}
                        <select
                          value={scene.expression || 'serious'}
                          onChange={e => updateScene(idx, { expression: e.target.value })}
                          className="bg-slate-900 text-slate-300 text-[11px] px-1.5 py-1 rounded border border-slate-700 outline-none truncate"
                        >
                          <option value="serious">EXP: Nghiêm</option>
                          <option value="shocked">EXP: Sốc</option>
                          <option value="thinking">EXP: Suy tư</option>
                        </select>
                      </div>
                    </div>

                    <textarea
                      rows={2}
                      value={scene.text}
                      onChange={e => updateScene(idx, { text: e.target.value })}
                      className="w-full bg-slate-900/60 text-slate-200 text-xs p-2.5 rounded-lg border border-slate-800/60 focus:border-slate-600 outline-none resize-none"
                    />
                  </div>
                )
              })}

              {!scenes.length && (
                <div className="p-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
                  Chưa có cảnh nào. Hãy bấm "AI Bóc Tách Cảnh" ở trên để tự động chia kịch bản.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Cinema Player (8 cols = 2/3, Sticky) */}
        <div className="lg:col-span-8 flex flex-col gap-4 sticky top-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              Xem Trước Video Trực Tiếp
            </h2>

            {activePackageId && (
              <span className="text-[11px] font-mono text-slate-500">ID: {activePackageId}</span>
            )}
          </div>

          {/* Interactive Player with FFT Lip-Sync */}
          <StorytimePlayer scenes={scenes} textConfig={textConfig} />

          {/* Post-Production Step: Subtitle & Text Overlay Customizer */}
          <TextOverlayCustomizer
            config={textConfig}
            onChange={setTextConfig}
            videoReady={scenes.some(s => !!s.audio_url) || scenes.length > 0}
          />

          {/* Export & Actions Card */}
          <div className="bg-slate-900/80 rounded-2xl p-4 border border-slate-800 flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Độ phân giải: 1920x1080 (16:9)</span>
              <span>Khung hình: 30 FPS</span>
            </div>

            <button
              onClick={() => {
                const exportPayload = {
                  package_id: activePackageId || 'custom_storytime',
                  exported_at: new Date().toISOString(),
                  text_overlay_config: textConfig,
                  scenes: scenes,
                }
                const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = 'storytime_package.json'
                a.click()
              }}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs flex items-center justify-center gap-2 border border-slate-700 transition-all"
            >
              <Download className="w-4 h-4 text-amber-400" />
              <span>Tải JSON Cấu Trúc Khung Hình & Cấu Hình Text</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
