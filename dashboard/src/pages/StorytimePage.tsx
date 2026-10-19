import { useState, useEffect } from 'react'
import { Sparkles, Wand2, RefreshCw, Download, FileText, Mic, Film, CheckCircle2, MapPin, Plus, Trash2, Users } from 'lucide-react'
import StorytimePlayer, { type StorytimeScene, type StoryCharacter } from '../components/storytime/StorytimePlayer'
import TextOverlayCustomizer, { type TextOverlayConfig, DEFAULT_TEXT_CONFIG } from '../components/storytime/TextOverlayCustomizer'
import { fetchAPI, postAPI } from '../api/client'

const SAMPLE_DETECTIVE_STORY = `Đêm hôm đó, một vụ án mạng kỳ lạ đã xảy ra ngay tại căn phòng số bảy.
Thanh tra Minh bước lại gần và chất vấn: "Quản gia Lâm, lúc mười một giờ đêm đó ông ở đâu?"
Quản gia Lâm sợ hãi xua tay: "Oan cho tôi quá, lúc đó tôi đang ở dưới tầng hầm kiểm tra kho rượu!"
Bất ngờ, quản gia vùng chạy trốn thục mạng ra phía hành lang tối, thám tử Minh liền lao theo truy bắt!
Nhân chứng Mai bàng hoàng chỉ tay: "Hắn ta chính là kẻ vừa giấu chiếc đồng hồ vỡ nát của nạn nhân!"`

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

export interface StoryLocation {
  id: string
  name: string
  background_prompt: string
  color: string
}

const LOCATION_COLOR_PALETTE = [
  '#f59e0b', '#3b82f6', '#8b5cf6', '#ef4444', '#10b981',
  '#ec4899', '#06b6d4', '#f97316', '#6366f1', '#14b8a6',
]

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
  const [storyTitle, setStoryTitle] = useState('Vụ Án Mới')
  const [voice, setVoice] = useState('vi-VN-NamMinhNeural')
  const [voiceGroups, setVoiceGroups] = useState<VoiceGroup[]>(DEFAULT_VOICE_GROUPS)
  const [scenes, setScenes] = useState<StorytimeScene[]>([])
  const [characters, setCharacters] = useState<StoryCharacter[]>([])
  const [locations, setLocations] = useState<StoryLocation[]>([])
  const [textConfig, setTextConfig] = useState<TextOverlayConfig>(DEFAULT_TEXT_CONFIG)
  const [isBreakingDown, setIsBreakingDown] = useState(false)
  const [isGeneratingTTS, setIsGeneratingTTS] = useState(false)
  const [activePackageId, setActivePackageId] = useState<string | null>(null)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const [regeneratingIdx, setRegeneratingIdx] = useState<number | null>(null)

  // Load sample package and available voices on mount
  useEffect(() => {
    fetchAPI<{ ok: boolean; package: { scenes: StorytimeScene[]; characters?: StoryCharacter[]; locations?: StoryLocation[] } }>('/api/storytime/sample-package')
      .then(res => {
        if (res.ok && res.package?.scenes?.length) {
          setScenes(res.package.scenes)
          if (res.package.characters?.length) {
            setCharacters(res.package.characters)
          }
          if (res.package.locations?.length) {
            setLocations(res.package.locations)
          }
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
      const res = await postAPI<{
        ok: boolean
        spec: {
          title?: string
          scenes: StorytimeScene[]
          locations?: StoryLocation[]
          characters?: StoryCharacter[]
        }
      }>('/api/storytime/breakdown', {
        story_text: storyText,
        genre: 'general',
      })
      if (res.ok && res.spec?.scenes) {
        if (res.spec.title) {
          setStoryTitle(res.spec.title)
        }
        setScenes(res.spec.scenes)
        if (res.spec.characters?.length) {
          setCharacters(res.spec.characters)
        }
        if (res.spec.locations?.length) {
          setLocations(res.spec.locations)
        }
        const charCount = res.spec.characters?.length || 0
        const locCount = res.spec.locations?.length || 0
        setStatusMsg(`Đã bóc tách thành ${res.spec.scenes.length} cảnh, ${charCount} nhân vật, ${locCount} bối cảnh. Hãy bấm "Tạo Giọng & Phụ Đề"!`)
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
      const res = await postAPI<{ ok: boolean; package: { package_id: string; project_id?: string; scenes: StorytimeScene[]; characters?: StoryCharacter[]; locations?: StoryLocation[] } }>(
        '/api/storytime/build-package',
        {
          title: storyTitle || 'Vụ Án Mới',
          genre: 'general',
          voice: voice,
          story_text: storyText,
          characters: characters.length > 0 ? characters : undefined,
          locations: locations.length > 0 ? locations : undefined,
          scenes: scenes.map((s, idx) => ({
            display_order: idx,
            speaker: s.speaker || 'char_1',
            text: s.text,
            camera: s.camera || 'zoom_in',
            expression: s.expression || 'serious',
            background_prompt: s.background_prompt,
            voice: s.voice || voice,
            location_id: s.location_id,
            action_type: s.action_type || 'dialogue',
          })),
        }
      )
      if (res.ok && res.package) {
        setScenes(res.package.scenes)
        if (res.package.characters?.length) {
          setCharacters(res.package.characters)
        }
        if (res.package.locations?.length) {
          setLocations(res.package.locations)
        }
        setActivePackageId(res.package.package_id)
        setStatusMsg('Đã tạo xong Giọng đọc và lưu thành công vào Dự án! Bấm "Phát Thử" bên phải để xem.')
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

  // Location management helpers
  const addLocation = () => {
    const idx = locations.length
    const color = LOCATION_COLOR_PALETTE[idx % LOCATION_COLOR_PALETTE.length]
    const newLoc: StoryLocation = {
      id: `loc_${Date.now().toString(36)}`,
      name: `Bối cảnh ${idx + 1}`,
      background_prompt: 'Dark moody scene. Pure scenery illustration, dark noir moody background, strictly NO people, NO characters.',
      color,
    }
    setLocations(prev => [...prev, newLoc])
  }

  const updateLocation = (locId: string, updates: Partial<StoryLocation>) => {
    setLocations(prev => prev.map(l => l.id === locId ? { ...l, ...updates } : l))
  }

  const deleteLocation = (locId: string) => {
    setLocations(prev => prev.filter(l => l.id !== locId))
    // Clear location_id from scenes referencing this location
    setScenes(prev => prev.map(s => s.location_id === locId ? { ...s, location_id: undefined } : s))
  }

  // Character management helper
  const updateCharacter = (charId: string, updates: Partial<StoryCharacter>) => {
    setCharacters(prev => prev.map(c => c.id === charId ? { ...c, ...updates } : c))
  }

  // Count scenes per location for badge display
  const scenesPerLocation = (locId: string) => scenes.filter(s => s.location_id === locId).length

  return (
    <div className="p-6 max-w-7xl mx-auto flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
              <Film className="w-6 h-6 text-amber-500" />
              Storytime Animation Studio
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Multi-Character 2D Engine
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Sản xuất video hoạt hình đa nhân vật tự động: Hỗ trợ mọi kịch bản, hành động di chuyển, đối thoại & rượt đuổi với FFT Lip-Sync.
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

          {/* 2. Character Manager */}
          {characters.length > 0 && (
            <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    <Users className="w-4 h-4 text-blue-400" />
                    Nhân Vật Hoạt Hình ({characters.length})
                  </h3>
                  <p className="text-xs text-slate-500">Màu trang phục & nhân vật bóc tách từ kịch bản</p>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                {characters.map(char => (
                  <div
                    key={char.id}
                    className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span
                        className="w-3.5 h-3.5 rounded-full shrink-0 ring-2 ring-slate-800"
                        style={{ backgroundColor: char.color }}
                      />
                      <input
                        type="text"
                        value={char.name}
                        onChange={e => updateCharacter(char.id, { name: e.target.value })}
                        className="bg-transparent text-slate-200 text-xs font-semibold outline-none border-b border-transparent hover:border-slate-700 focus:border-blue-500/50 min-w-0"
                      />
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                        {char.gender === 'female' ? 'Nữ' : char.gender === 'male' ? 'Nam' : 'Khác'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <input
                        type="color"
                        value={char.color}
                        onChange={e => updateCharacter(char.id, { color: e.target.value })}
                        className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent p-0"
                        title="Đổi màu trang phục 2D"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Location Manager */}
          <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-amber-400" />
                  Bối Cảnh / Locations ({locations.length})
                </h3>
                <p className="text-xs text-slate-500">Các cảnh cùng bối cảnh sẽ dùng chung ảnh nền</p>
              </div>
              <button
                onClick={addLocation}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs flex items-center gap-1.5 border border-slate-700 transition-all"
              >
                <Plus className="w-3 h-3" />
                Thêm Bối Cảnh
              </button>
            </div>

            {locations.length > 0 ? (
              <div className="flex flex-col gap-2 max-h-[240px] overflow-y-auto pr-1">
                {locations.map(loc => {
                  const count = scenesPerLocation(loc.id)
                  return (
                    <div
                      key={loc.id}
                      className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col gap-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          <span
                            className="w-3 h-3 rounded-full shrink-0 ring-2 ring-slate-800"
                            style={{ backgroundColor: loc.color }}
                          />
                          <input
                            type="text"
                            value={loc.name}
                            onChange={e => updateLocation(loc.id, { name: e.target.value })}
                            className="bg-transparent text-slate-200 text-xs font-semibold outline-none border-b border-transparent hover:border-slate-700 focus:border-amber-500/50 min-w-0 flex-1"
                          />
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-md bg-slate-800 text-slate-400">
                            {count} cảnh
                          </span>
                          <input
                            type="color"
                            value={loc.color}
                            onChange={e => updateLocation(loc.id, { color: e.target.value })}
                            className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent p-0"
                            title="Đổi màu badge"
                          />
                          <button
                            onClick={() => deleteLocation(loc.id)}
                            className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-all"
                            title="Xoá bối cảnh"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      <textarea
                        rows={2}
                        value={loc.background_prompt}
                        onChange={e => updateLocation(loc.id, { background_prompt: e.target.value })}
                        placeholder="Background prompt cho bối cảnh này..."
                        className="w-full bg-slate-900/60 text-slate-300 text-[11px] p-2 rounded-lg border border-slate-800/60 focus:border-slate-600 outline-none resize-none leading-relaxed"
                      />
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="p-4 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
                Chưa có bối cảnh. AI sẽ tự tạo khi bóc tách kịch bản, hoặc bấm "Thêm Bối Cảnh" để tạo thủ công.
              </div>
            )}
          </div>

          {/* 3. Scene List Editor */}
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
                    style={(() => {
                      const sceneLoc = locations.find(l => l.id === scene.location_id)
                      return sceneLoc ? { borderLeftWidth: '3px', borderLeftColor: sceneLoc.color } : undefined
                    })()}
                  >
                    <div className="flex flex-col gap-2">
                      {/* Card Header Row 1: Index, Speaker, Location Badge, Status & Single-TTS Button */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="w-5 h-5 rounded-md bg-slate-800 text-slate-300 font-mono text-[11px] flex items-center justify-center font-bold shrink-0">
                            {idx + 1}
                          </span>
                          <span className="text-xs font-semibold text-slate-200 truncate">
                            {(() => {
                              const foundChar = characters.find(c => c.id === scene.speaker || c.name === scene.speaker)
                              if (foundChar) return `👤 ${foundChar.name}`
                              if (scene.speaker === 'narrator') return '🎙️ Người kể'
                              return scene.speaker ? `👤 ${scene.speaker}` : '🎙️ Người kể'
                            })()}
                          </span>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 shrink-0">
                            {scene.action_type === 'chase'
                              ? '🏃‍♂️ Rượt đuổi'
                              : scene.action_type === 'trio'
                              ? '🎭 Đa nhân vật'
                              : scene.action_type === 'solo'
                              ? '👤 Đơn độc'
                              : '👥 Đối thoại'}
                          </span>
                          {(() => {
                            const sceneLoc = locations.find(l => l.id === scene.location_id)
                            return sceneLoc ? (
                              <span
                                className="text-[10px] font-medium px-1.5 py-0.5 rounded-full truncate max-w-[100px]"
                                style={{ backgroundColor: sceneLoc.color + '20', color: sceneLoc.color, border: `1px solid ${sceneLoc.color}40` }}
                                title={sceneLoc.name}
                              >
                                📍 {sceneLoc.name}
                              </span>
                            ) : null
                          })()}
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

                      {/* Card Controls Row 2: Speaker, Action Type, Voice, Location, Camera, Expression */}
                      <div className="grid grid-cols-6 gap-1.5 pt-0.5">
                        {/* Speaker Selector */}
                        <select
                          value={scene.speaker || (characters[0]?.id || 'char_1')}
                          onChange={e => updateScene(idx, { speaker: e.target.value })}
                          className="bg-slate-900 text-amber-300 text-[11px] px-1.5 py-1 rounded border border-amber-500/30 outline-none truncate font-medium"
                          title="Ai là người nói câu này?"
                        >
                          {characters.length > 0 ? (
                            <>
                              {characters.map(c => (
                                <option key={c.id} value={c.id}>
                                  👤 {c.name}
                                </option>
                              ))}
                              <option value="narrator">🎙️ Người kể</option>
                            </>
                          ) : (
                            <>
                              <option value="char_1">👤 Nhân vật 1</option>
                              <option value="char_2">👤 Nhân vật 2</option>
                              <option value="narrator">🎙️ Người kể</option>
                            </>
                          )}
                        </select>

                        {/* Action Type / Sân khấu */}
                        <select
                          value={scene.action_type || 'dialogue'}
                          onChange={e => updateScene(idx, { action_type: e.target.value })}
                          className="bg-slate-900 text-blue-300 text-[11px] px-1.5 py-1 rounded border border-blue-500/30 outline-none truncate font-medium"
                          title="Hành động sân khấu"
                        >
                          <option value="dialogue">👥 Đối chất</option>
                          <option value="chase">🏃‍♂️ Rượt đuổi</option>
                          <option value="trio">🎭 3 Người</option>
                          <option value="solo">👤 Đơn độc</option>
                        </select>

                        {/* Per-scene Location Selector */}
                        <select
                          value={scene.location_id || ''}
                          onChange={e => {
                            const locId = e.target.value || undefined
                            const loc = locations.find(l => l.id === locId)
                            updateScene(idx, {
                              location_id: locId,
                              background_prompt: loc?.background_prompt || scene.background_prompt,
                            })
                          }}
                          className="bg-slate-900 text-slate-200 text-[11px] px-1.5 py-1 rounded border border-slate-700 outline-none truncate font-medium"
                          title="Chọn bối cảnh cho phân cảnh này"
                        >
                          <option value="">📍 Không gán</option>
                          {locations.map(loc => (
                            <option key={loc.id} value={loc.id}>
                              📍 {loc.name}
                            </option>
                          ))}
                        </select>

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
                          <option value="zoom_in">CAM: Zoom</option>
                          <option value="close">CAM: Cận</option>
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
          <StorytimePlayer scenes={scenes} textConfig={textConfig} characters={characters} />

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
                  locations: locations,
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
