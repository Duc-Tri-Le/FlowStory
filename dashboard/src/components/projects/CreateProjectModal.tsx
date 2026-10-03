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

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated?: (project: Project) => void
}

const MATERIAL_OPTIONS = [
  { id: 'realistic', label: 'Photorealistic (Điện ảnh chân thực)' },
  { id: '3d_pixar', label: '3D Pixar (Hoạt hình 3D Pixar)' },
  { id: 'anime', label: 'Anime (Anime Nhật Bản)' },
  { id: 'anime_comedy', label: 'Anime Comedy (Hài hước)' },
  { id: 'ghibli', label: 'Studio Ghibli (Phong cách Ghibli)' },
  { id: 'cyberpunk', label: 'Cyberpunk (Tương lai viễn tưởng)' },
  { id: 'oil_painting', label: 'Oil Painting (Sơn dầu)' },
  { id: 'comic_book', label: 'Comic Book (Truyện tranh)' },
]

export default function CreateProjectModal({ open, onOpenChange, onCreated }: Props) {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [flowUuid, setFlowUuid] = useState('')
  const [material, setMaterial] = useState('realistic')
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function reset() {
    setName('')
    setFlowUuid('')
    setMaterial('realistic')
    setPrompt('')
    setError(null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) {
      setError('Vui lòng nhập tên dự án')
      return
    }
    if (!prompt.trim()) {
      setError('Vui lòng nhập kịch bản hoặc mô tả phân cảnh ban đầu')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // 1. Unified full-pipeline creation
      const res = await fetchAPI<{
        project?: Project
        project_id?: string
        video_id: string
        scenes_created: number
        characters_created?: number
        pipeline_started?: boolean
      }>('/api/projects/create-with-script', {
        method: 'POST',
        body: JSON.stringify({
          name: name.trim(),
          story: prompt.trim(),
          flow_project_id: flowUuid.trim() || undefined,
          material,
        }),
      })

      const projId = res.project?.id || res.project_id
      reset()
      onOpenChange(false)
      if (res.project) onCreated?.(res.project)
      if (projId) navigate(`/projects/${projId}`)
      return

      // 2. Sequential creation:
      // Step A: Create project with name, story, material and Google Flow UUID
      const project = await fetchAPI<Project>('/api/projects', {
        method: 'POST',
        body: JSON.stringify({
          name: name.trim(),
          story: prompt.trim(),
          flow_project_id: flowUuid.trim() || undefined,
          material,
        }),
      })

      // Step B: Create default video
      const video = await fetchAPI<{ id: string }>('/api/videos', {
        method: 'POST',
        body: JSON.stringify({
          project_id: project.id,
          title: name.trim(),
          display_order: 0,
        }),
      })

      // Step C: Generate scenes from script (server auto-detects count)
      await fetchAPI(`/api/projects/${project.id}/generate-scenes`, {
        method: 'POST',
        body: JSON.stringify({
          video_id: video.id,
          prompt: prompt.trim(),
        }),
      }).catch((e: any) => console.warn('Scene generation note:', e))

      reset()
      onOpenChange(false)
      onCreated?.(project)
      navigate(`/projects/${project.id}`)
    } catch (err: any) {
      setError(err?.message || 'Có lỗi xảy ra khi tạo dự án')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={o => { if (!loading) { onOpenChange(o); if (!o) reset(); } }}>
      <DialogContent className="max-w-[580px] p-6 gap-4" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
        <DialogHeader className="gap-1.5">
          <DialogTitle className="text-base font-semibold tracking-wide flex items-center gap-2">
            <span>✨</span> Tạo Dự Án Mới từ Kịch Bản
          </DialogTitle>
          <DialogDescription className="text-xs" style={{ color: 'var(--muted)' }}>
            Khởi tạo dự án, gắn Google Flow UUID và tự động phân tách kịch bản thành các cảnh quay (scene).
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5 pt-1">
          {/* Tên dự án */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[11px] font-medium tracking-wide uppercase" style={{ color: 'var(--text)' }}>
              Tên Dự Án <span style={{ color: 'var(--red)' }}>*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Ví dụ: Cuộc Chiến Trên Bầu Trời..."
              disabled={loading}
              className="w-full px-3 py-2 rounded-md text-xs outline-none transition-all"
              style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
            />
          </div>

          {/* Gắn Google Flow UUID */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-medium tracking-wide uppercase" style={{ color: 'var(--text)' }}>
                Google Flow UUID <span className="text-[10px] lowercase text-muted-foreground font-normal">(tùy chọn)</span>
              </label>
              {flowUuid && (
                <span className="text-[10px] font-mono" style={{ color: 'var(--accent)' }}>
                  UUID đã nhập
                </span>
              )}
            </div>
            <input
              type="text"
              value={flowUuid}
              onChange={e => setFlowUuid(e.target.value)}
              placeholder="Dán UUID dự án Google Flow (ví dụ: f0ee1600-5085-47c8-8226-ed62673e2363)..."
              disabled={loading}
              className="w-full px-3 py-2 rounded-md text-xs font-mono outline-none transition-all"
              style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
            />
            <span className="text-[10px] leading-tight" style={{ color: 'var(--muted)' }}>
              💡 Dán UUID nếu bạn đã tạo dự án trên Google Flow Studio, hoặc để trống để FlowKit tự khởi tạo.
            </span>
          </div>

          {/* Chất liệu & Phân cảnh tự động */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-medium tracking-wide uppercase" style={{ color: 'var(--text)' }}>
                Chất Liệu / Phong Cách
              </label>
              <select
                value={material}
                onChange={e => setMaterial(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2 rounded-md text-xs outline-none"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
              >
                {MATERIAL_OPTIONS.map(m => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-medium tracking-wide uppercase" style={{ color: 'var(--text)' }}>
                Số Lượng Scene
              </label>
              <div
                className="w-full px-3 py-2 rounded-md text-xs flex items-center gap-1.5 h-[34px]"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--accent)' }}
              >
                <span>⚡</span>
                <span className="font-medium text-[11px]">Tự động đọc từ kịch bản</span>
              </div>
            </div>
          </div>

          {/* Kịch bản ban đầu */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-medium tracking-wide uppercase" style={{ color: 'var(--text)' }}>
                Kịch Bản / Phân Cảnh Ban Đầu <span style={{ color: 'var(--red)' }}>*</span>
              </label>
              <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
                Bối cảnh thuần: không người
              </span>
            </div>
            <textarea
              rows={6}
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder="Nhập mô tả diễn biến câu chuyện, hoặc danh sách các cảnh bạn muốn tạo...&#10;Ví dụ:&#10;Cảnh 1: Sa mạc cát vàng mênh mông dưới ánh hoàng hôn rực đỏ (chỉ bối cảnh, không người).&#10;Cảnh 2: Một chiến binh áo choàng đen đứng trên cồn cát cao nhìn về phía thành phố cổ.&#10;Cảnh 3: Đôi mắt của chiến binh lóe sáng dưới ánh trăng đêm."
              disabled={loading}
              className="w-full p-3 rounded-md text-xs leading-relaxed outline-none resize-y font-mono"
              style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
            />
            <span className="text-[10px] leading-relaxed" style={{ color: 'var(--muted)' }}>
              💡 <strong>Quy trình từng bước</strong>: Khi tạo dự án, hệ thống <strong>chỉ tạo ảnh tham chiếu</strong> để bạn duyệt trước. Sau khi thấy ảnh tham chiếu ổn định, bạn vào mục <em>Hình ảnh</em> bấm <strong>▶ Tạo tất cả ảnh</strong>, rồi tiếp tục kiểm tra và bấm <strong>▶ Tạo Video</strong>. Hệ thống không tự ý sinh ảnh cảnh hay video khi chưa có sự xác nhận của bạn.
            </span>
          </div>

          {error && (
            <div className="p-2.5 rounded text-xs" style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--red)', border: '1px solid var(--red)' }}>
              ⚠️ {error}
            </div>
          )}

          <DialogFooter className="pt-2 flex items-center justify-end gap-2">
            <Button type="button" variant="outline" size="sm" disabled={loading} onClick={() => onOpenChange(false)}>
              Hủy
            </Button>
            <Button type="submit" variant="default" size="sm" disabled={loading} className="gap-1.5">
              {loading ? (
                <>⏳ Đang tạo dự án & kịch bản...</>
              ) : (
                <>🚀 Tạo Dự Án & Kịch Bản</>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
