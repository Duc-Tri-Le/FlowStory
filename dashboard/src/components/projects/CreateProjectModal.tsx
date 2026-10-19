import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../ui/dialog'
import { Button } from '../ui/button'
import { fetchAPI } from '../../api/client'
import type { Project } from '../../types'
import { Zap, FileText, ChevronDown, ChevronUp } from 'lucide-react'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated?: (project?: Project) => void
}

const MATERIAL_OPTIONS = [
  { id: 'oversimplified_2d', label: '⭐ Hoạt Hình 2D Người Que Tối Giản (OverSimplified & Dark Folklore)' },
  { id: 'realistic', label: 'Photorealistic (Điện ảnh chân thực)' },
  { id: 'cinematic_drama', label: 'Cinematic Drama (Phim truyền hình 35mm)' },
  { id: '3d_pixar', label: '3D Pixar (Hoạt hình 3D Pixar)' },
  { id: 'anime', label: 'Anime (Anime Nhật Bản)' },
  { id: 'anime_comedy', label: 'Anime Comedy (Hoạt hình hài hước)' },
  { id: 'ghibli', label: 'Studio Ghibli (Phong cách Ghibli)' },
  { id: 'comic_book', label: 'Comic Book (Truyện tranh)' },
  { id: 'watercolor', label: 'Watercolor (Tranh màu nước)' },
  { id: 'oil_painting', label: 'Oil Painting (Sơn dầu cổ điển)' },
  { id: 'claymation', label: 'Claymation (Đất sét hoạt hình)' },
  { id: 'stop_motion', label: 'Stop Motion (Thủ công nỉ & gỗ)' },
  { id: 'minecraft', label: 'Minecraft (Voxel khối vuông)' },
  { id: 'lego', label: 'LEGO (Xếp hình Lego)' },
  { id: 'cyberpunk', label: 'Cyberpunk (Tương lai viễn tưởng)' },
  { id: 'retro_vhs', label: 'Retro VHS (Băng từ thập niên 80)' },
]

const VOICE_OPTIONS = [
  { id: 'vi-VN-NamMinhNeural', label: '🎙️ Nam Minh (Trầm ấm Noir / Trinh thám)' },
  { id: 'vi-VN-HoaiMyNeural', label: '🎙️ Hoài My (Cảm xúc Drama gia đình)' },
]

const DEFAULT_BATCH_INPUT = `=== Tập 1: Bóng Đen Gian Chuồng Cũ ===
Đêm hôm đó, giữa cơn mưa bão xối xả, Lão Tam nghe thấy tiếng cào xé kỳ lạ phát ra sau gian chuồng cũ.
Cầm ngọn đèn dầu rọi vào bóng tối, ông bàng hoàng nhận ra đôi mắt đỏ quỷ dị của con quái thú đang nhìn mình trừng trừng.
Tiếng gầm rùng rợn xé toạc màn mưa khiến người nông dân kinh hồn bạt vía.
Lão Tam ngã quỵ xuống đất, run rẩy tìm đường tháo chạy trong bóng đêm mịt mùng.

=== Tập 2: Dấu Chân Kỳ Dị Ven Rừng ===
Sáng hôm sau, khi cơn bão vừa dứt, dân làng kéo nhau ra gian chuồng củi hoang tàn.
Trên nền đất bùn nhão nhoét xuất hiện những vệt móng vuốt cào xé sâu hoắm dọc theo vách gỗ mục nát.
Lão Tam hớt hải chỉ tay về phía cánh rừng rậm u ám phủ đầy sương lạnh.
Mọi người đều nín lặng khi nhận ra vết chân quái thú đang dẫn thẳng vào sâu trong hang tối.`

const SAMPLE_SINGLE_STORY = `Bóng Đen Gian Chuồng Cũ (Hoạt Hình 2D Dân Gian)
Đêm hôm đó, giữa cơn mưa bão xối xả, Lão Tam nghe thấy tiếng cào xé kỳ lạ sau gian chuồng cũ.
Cầm ngọn đèn dầu rọi vào bóng tối, ông bàng hoàng nhận ra đôi mắt đỏ quỷ dị của con quái thú đang nhìn mình trừng trừng.
Con quái thú nhe hàm nanh sắc nhọn gầm lên một tiếng rùng rợn xé toạc màn đêm.
Lão Tam hốt hoảng vứt cả chiếc đèn dầu, cuống cuồng tháo chạy trong nỗi kinh hoàng tột độ.`

export default function CreateProjectModal({ open, onOpenChange, onCreated }: Props) {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [flowUuid, setFlowUuid] = useState('')
  const [material, setMaterial] = useState('oversimplified_2d')
  const [orientation, setOrientation] = useState<'HORIZONTAL' | 'VERTICAL'>('HORIZONTAL')
  const [voice, setVoice] = useState('vi-VN-NamMinhNeural')
  const [prompt, setPrompt] = useState(DEFAULT_BATCH_INPUT)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function reset() {
    setName('')
    setFlowUuid('')
    setMaterial('oversimplified_2d')
    setOrientation('HORIZONTAL')
    setVoice('vi-VN-NamMinhNeural')
    setPrompt(DEFAULT_BATCH_INPUT)
    setShowAdvanced(false)
    setError(null)
  }

  // Count detect episodes
  const episodeCount = (prompt.match(/===\s*(.*?)\s*===/g) || []).length

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!prompt.trim()) {
      setError('Vui lòng nhập nội dung kịch bản.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const res = await fetchAPI<{
        project?: Project
        project_id?: string
        video_id: string
        scenes_created: number
        characters_created?: number
        pipeline_started?: boolean
        created_count?: number
        projects?: Project[]
      }>('/api/projects/create-with-script', {
        method: 'POST',
        body: JSON.stringify({
          name: name.trim() || (episodeCount > 1 ? 'Loạt Video Mới' : 'Dự Án Mới'),
          story: prompt.trim(),
          flow_project_id: flowUuid.trim() || undefined,
          material,
          orientation,
        }),
      })

      reset()
      onOpenChange(false)
      if (res.project) onCreated?.(res.project)
      else onCreated?.()

      if (res.created_count && res.created_count > 1) {
        navigate('/projects')
      } else if (res.project_id || res.project?.id) {
        const pid = res.project_id || res.project?.id
        navigate(`/projects/${pid}?tab=pipeline`)
      } else {
        navigate('/projects')
      }
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi tạo dự án.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={o => { if (!loading) { onOpenChange(o); if (!o) reset(); } }}>
      <DialogContent className="max-w-[680px] p-6 gap-4" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
        <DialogHeader className="gap-1.5 pb-2 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
              <Zap className="w-4 h-4 fill-current" />
            </div>
            <div>
              <DialogTitle className="text-base font-bold tracking-tight text-white flex items-center gap-2">
                <span>Nạp Kịch Bản & Tạo Dự Án</span>
                {episodeCount > 1 && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Phát hiện {episodeCount} tập
                  </span>
                )}
              </DialogTitle>
              <DialogDescription className="text-xs" style={{ color: 'var(--muted)' }}>
                Nhập 1 tập kịch bản hoặc phân tách nhiều tập bằng dòng <code className="text-amber-300 font-mono">=== Tập X: Tên Tập ===</code>.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5 pt-1">
          {/* Controls Row: Material, Orientation & Voice */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-medium tracking-wide uppercase" style={{ color: 'var(--text)' }}>
                Phong Cách (Material)
              </label>
              <select
                value={material}
                onChange={e => setMaterial(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2 rounded-lg text-xs outline-none"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
              >
                {MATERIAL_OPTIONS.map(m => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-medium tracking-wide uppercase" style={{ color: 'var(--text)' }}>
                Tỷ Lệ Khung Hình
              </label>
              <select
                value={orientation}
                onChange={e => setOrientation(e.target.value as 'HORIZONTAL' | 'VERTICAL')}
                disabled={loading}
                className="w-full px-3 py-2 rounded-lg text-xs font-medium outline-none"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
              >
                <option value="HORIZONTAL">🖥️ 16:9 Ngang (Chuẩn Phim)</option>
                <option value="VERTICAL">📱 9:16 Dọc (Shorts/TikTok)</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-medium tracking-wide uppercase" style={{ color: 'var(--text)' }}>
                Giọng Đọc (TTS)
              </label>
              <select
                value={voice}
                onChange={e => setVoice(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2 rounded-lg text-xs outline-none"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
              >
                {VOICE_OPTIONS.map(v => (
                  <option key={v.id} value={v.id}>{v.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Kịch bản Textarea */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-medium tracking-wide uppercase flex items-center gap-1.5" style={{ color: 'var(--text)' }}>
                <FileText className="w-3.5 h-3.5 text-amber-400" />
                <span>Nội Dung Kịch Bản <span style={{ color: 'var(--red)' }}>*</span></span>
              </label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPrompt(DEFAULT_BATCH_INPUT)}
                  className="text-[10px] text-amber-400 hover:text-amber-300 underline"
                >
                  Nạp mẫu 2 tập
                </button>
                <span className="text-slate-600">·</span>
                <button
                  type="button"
                  onClick={() => setPrompt(SAMPLE_SINGLE_STORY)}
                  className="text-[10px] text-slate-400 hover:text-slate-200 underline"
                >
                  Nạp mẫu 1 tập
                </button>
              </div>
            </div>

            <textarea
              rows={9}
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder="Dán kịch bản vào đây...&#10;&#10;=== Tập 1: Tên Tập ===&#10;Nội dung diễn biến tập 1...&#10;&#10;=== Tập 2: Tên Tập ===&#10;Nội dung diễn biến tập 2..."
              disabled={loading}
              className="w-full p-3.5 rounded-xl text-xs leading-relaxed outline-none resize-y font-mono focus:border-amber-500/50 transition-all"
              style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
            />
          </div>

          {/* Advanced Collapsible: Custom Name & Google Flow ID */}
          <div className="border rounded-lg px-3 py-2" style={{ borderColor: 'var(--border)', background: 'rgba(15, 23, 42, 0.4)' }}>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center justify-between w-full text-left text-[11px] font-medium"
              style={{ color: 'var(--muted)' }}
            >
              <span>⚙️ Tùy chọn nâng cao (Tên dự án riêng, Google Flow UUID)</span>
              {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showAdvanced && (
              <div className="flex flex-col gap-3 pt-3 mt-2 border-t" style={{ borderColor: 'var(--border)' }}>
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--text)' }}>
                    Tên dự án tùy chỉnh (nếu muốn đặt riêng)
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="Mặc định tự nhận diện từ tiêu đề kịch bản..."
                    disabled={loading}
                    className="w-full px-3 py-1.5 rounded-md text-xs outline-none"
                    style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--text)' }}>
                    Google Flow UUID (tùy chọn)
                  </label>
                  <input
                    type="text"
                    value={flowUuid}
                    onChange={e => setFlowUuid(e.target.value)}
                    placeholder="Dán UUID dự án Google Flow nếu đã tạo trên Flow Studio..."
                    disabled={loading}
                    className="w-full px-3 py-1.5 rounded-md text-xs font-mono outline-none"
                    style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
                  />
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="p-2.5 rounded text-xs" style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--red)', border: '1px solid var(--red)' }}>
              ⚠️ {error}
            </div>
          )}

          <DialogFooter className="pt-2 flex items-center justify-end gap-2 border-t" style={{ borderColor: 'var(--border)' }}>
            <Button type="button" variant="outline" size="sm" disabled={loading} onClick={() => onOpenChange(false)}>
              Hủy
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={loading}
              className="gap-1.5 font-bold shadow-md"
              style={{ background: 'var(--accent)', color: '#fff' }}
            >
              {loading ? (
                <>⏳ Đang phân tích & tạo dự án...</>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5 fill-current" />
                  <span>{episodeCount > 1 ? `Tạo ${episodeCount} Dự Án Hàng Loạt` : 'Tạo Dự Án & Phân Cảnh'}</span>
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
