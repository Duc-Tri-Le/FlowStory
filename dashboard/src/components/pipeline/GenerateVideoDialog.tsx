import { useState, useMemo } from 'react'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '../ui/dialog'
import { Button } from '../ui/button'
import { getProxyDownloadUrl } from '../../api/client'
import type { Scene, StatusType } from '../../types'

interface Props {
  open: boolean
  onOpenChange: (v: boolean) => void
  scenes: Scene[]
  projectId: string
  videoId: string
  onSubmit: (sceneIds: string[]) => Promise<void>
  submitting: boolean
}

const STATUS_COLOR: Record<StatusType, string> = {
  COMPLETED: 'var(--green)',
  PROCESSING: 'var(--yellow)',
  PENDING: 'var(--muted)',
  FAILED: 'var(--red)',
}

const STATUS_LABEL: Record<StatusType, string> = {
  COMPLETED: 'Đã có video',
  PROCESSING: 'Đang tạo',
  PENDING: 'Chưa tạo',
  FAILED: 'Thất bại',
}

function getVideoStatus(scene: Scene): StatusType {
  if (scene.vertical_video_status !== 'PENDING') return scene.vertical_video_status
  return scene.horizontal_video_status
}

function getVideoUrl(scene: Scene): string | null {
  return scene.vertical_video_url || scene.horizontal_video_url
}

function getThumbUrl(scene: Scene): string | null {
  return scene.vertical_image_url || scene.horizontal_image_url
}

export default function GenerateVideoDialog({
  open, onOpenChange, scenes, onSubmit, submitting,
}: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [filter, setFilter] = useState<'all' | 'pending' | 'failed'>('all')

  const filteredScenes = useMemo(() => {
    return scenes.filter(s => {
      const st = getVideoStatus(s)
      if (filter === 'pending') return st === 'PENDING'
      if (filter === 'failed') return st === 'FAILED'
      return true
    })
  }, [scenes, filter])

  const allSelected = filteredScenes.length > 0 && filteredScenes.every(s => selected.has(s.id))
  const someSelected = selected.size > 0 && !allSelected

  function toggleAll() {
    if (allSelected) {
      const next = new Set(selected)
      filteredScenes.forEach(s => next.delete(s.id))
      setSelected(next)
    } else {
      const next = new Set(selected)
      filteredScenes.forEach(s => next.add(s.id))
      setSelected(next)
    }
  }

  function toggle(id: string) {
    const next = new Set(selected)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelected(next)
  }

  async function handleSubmit() {
    if (selected.size === 0) return
    await onSubmit([...selected])
    setSelected(new Set())
    onOpenChange(false)
  }

  const pendingCount = scenes.filter(s => getVideoStatus(s) === 'PENDING').length
  const failedCount = scenes.filter(s => getVideoStatus(s) === 'FAILED').length
  const completedCount = scenes.filter(s => getVideoStatus(s) === 'COMPLETED').length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        style={{
          width: 'min(860px, 95vw)',
          maxWidth: 'none',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          padding: 0,
          gap: 0,
          background: 'var(--card)',
          border: '1px solid var(--border)',
        }}
      >
        {/* Header */}
        <DialogHeader className="px-6 pt-5 pb-4" style={{ borderBottom: '1px solid var(--border)' }}>
          <DialogTitle className="text-base font-semibold" style={{ color: 'var(--text)' }}>
            ▶ Tạo Video
          </DialogTitle>
          <DialogDescription style={{ color: 'var(--muted)', fontSize: '12px' }}>
            Chọn cảnh muốn tạo video. Cảnh đã có video có thể tải về ngay.
          </DialogDescription>

          {/* Stats + filter row */}
          <div className="flex items-center gap-2 mt-3 flex-wrap">
            {[
              { label: 'Tổng', count: scenes.length, color: 'var(--text)' },
              { label: 'Chưa tạo', count: pendingCount, color: 'var(--muted)' },
              { label: 'Thất bại', count: failedCount, color: 'var(--red)' },
              { label: 'Hoàn thành', count: completedCount, color: 'var(--green)' },
            ].map(({ label, count, color }) => (
              <div
                key={label}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
              >
                <span className="text-[10px] tracking-wide" style={{ color: 'var(--muted)' }}>{label}</span>
                <span className="text-xs font-semibold" style={{ color }}>{count}</span>
              </div>
            ))}

            <div className="flex items-center gap-1 ml-auto">
              {(['all', 'pending', 'failed'] as const).map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className="px-2.5 py-1 rounded text-[10px] tracking-widest uppercase transition-all"
                  style={{
                    background: filter === f ? 'var(--accent)' : 'var(--surface)',
                    color: filter === f ? '#fff' : 'var(--muted)',
                    border: '1px solid var(--border)',
                    cursor: 'pointer',
                  }}
                >
                  {f === 'all' ? 'Tất cả' : f === 'pending' ? 'Chưa tạo' : 'Thất bại'}
                </button>
              ))}
            </div>
          </div>
        </DialogHeader>

        {/* Scene list */}
        <div className="flex-1 overflow-y-auto px-4 py-3">
          {/* Select all row */}
          <div
            className="flex items-center gap-3 px-3 py-2 rounded-md mb-2 cursor-pointer select-none"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
            onClick={toggleAll}
          >
            <CheckBox checked={allSelected} indeterminate={someSelected} />
            <span className="text-xs font-semibold" style={{ color: 'var(--text)' }}>
              Chọn tất cả ({filteredScenes.length} cảnh)
            </span>
            {selected.size > 0 && (
              <span
                className="ml-auto text-[10px] px-2 py-0.5 rounded font-semibold"
                style={{ background: 'var(--accent)', color: '#fff' }}
              >
                {selected.size} đã chọn
              </span>
            )}
          </div>

          {/* Scene rows */}
          <div className="flex flex-col gap-1.5">
            {filteredScenes.map(scene => {
              const st = getVideoStatus(scene)
              const videoUrl = getVideoUrl(scene)
              const thumbUrl = getThumbUrl(scene)
              const isSelected = selected.has(scene.id)
              const isProcessing = st === 'PROCESSING'

              return (
                <div
                  key={scene.id}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-md cursor-pointer transition-colors"
                  style={{
                    background: isSelected ? 'rgba(59,130,246,0.06)' : 'var(--surface)',
                    border: `1px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}`,
                    opacity: isProcessing ? 0.7 : 1,
                    cursor: isProcessing ? 'default' : 'pointer',
                  }}
                  onClick={() => !isProcessing && toggle(scene.id)}
                >
                  <CheckBox checked={isSelected} disabled={isProcessing} />

                  {/* Thumbnail */}
                  <div
                    className="flex-shrink-0 rounded overflow-hidden"
                    style={{ width: 64, height: 36, background: 'var(--bg)', border: '1px solid var(--border)' }}
                  >
                    {videoUrl ? (
                      <video src={videoUrl} className="w-full h-full object-cover" muted playsInline />
                    ) : thumbUrl ? (
                      <img src={thumbUrl} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span style={{ fontSize: 9, color: 'var(--muted)' }}>—</span>
                      </div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold" style={{ color: 'var(--text)' }}>
                        Cảnh #{scene.display_order + 1}
                      </span>
                      <span
                        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] tracking-widest"
                        style={{ color: STATUS_COLOR[st], border: `1px solid ${STATUS_COLOR[st]}` }}
                      >
                        <span className="w-1 h-1 rounded-full" style={{ background: STATUS_COLOR[st] }} />
                        {STATUS_LABEL[st]}
                      </span>
                    </div>
                    {scene.video_prompt && (
                      <p
                        className="mt-0.5 text-[10px] leading-snug overflow-hidden"
                        style={{
                          color: 'var(--muted)',
                          display: '-webkit-box',
                          WebkitLineClamp: 1,
                          WebkitBoxOrient: 'vertical',
                          margin: 0,
                        }}
                      >
                        {scene.video_prompt}
                      </p>
                    )}
                  </div>

                  {/* Download button if video done */}
                  {videoUrl && (
                    <a
                      href={getProxyDownloadUrl(videoUrl, `scene_${scene.display_order + 1}_video.mp4`)}
                      download={`scene_${scene.display_order + 1}_video.mp4`}
                      onClick={e => e.stopPropagation()}
                      className="flex-shrink-0 inline-flex items-center gap-1 px-2.5 py-1.5 rounded text-[10px] font-medium transition-opacity hover:opacity-80"
                      style={{
                        background: 'transparent',
                        color: 'var(--green)',
                        border: '1px solid var(--green)',
                        textDecoration: 'none',
                      }}
                      title="Tải video về máy"
                    >
                      ⬇ Tải
                    </a>
                  )}
                </div>
              )
            })}
          </div>

          {filteredScenes.length === 0 && (
            <div
              className="flex items-center justify-center py-12 rounded-md text-xs"
              style={{ border: '1px dashed var(--border)', color: 'var(--muted)' }}
            >
              Không có cảnh nào phù hợp bộ lọc
            </div>
          )}
        </div>

        {/* Footer */}
        <DialogFooter
          className="flex-row items-center gap-3 px-6 py-4"
          style={{ borderTop: '1px solid var(--border)' }}
        >
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <span className="flex-1" />
          {selected.size > 0 && (
            <span className="text-[11px]" style={{ color: 'var(--muted)' }}>
              {selected.size} cảnh được chọn
            </span>
          )}
          <Button
            size="sm"
            disabled={selected.size === 0 || submitting}
            onClick={handleSubmit}
            style={{ background: 'var(--accent)', color: '#fff', minWidth: 130 }}
          >
            {submitting
              ? 'Đang gửi...'
              : selected.size > 0
              ? `▶ Tạo ${selected.size} video`
              : '▶ Chọn cảnh để tạo'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/* Inline checkbox */
function CheckBox({
  checked, indeterminate = false, disabled = false,
}: { checked: boolean; indeterminate?: boolean; disabled?: boolean }) {
  return (
    <div
      className="flex-shrink-0 w-4 h-4 rounded flex items-center justify-center transition-colors"
      style={{
        background: checked || indeterminate ? 'var(--accent)' : 'transparent',
        border: `1.5px solid ${checked || indeterminate ? 'var(--accent)' : 'var(--border)'}`,
        opacity: disabled ? 0.45 : 1,
      }}
    >
      {indeterminate ? (
        <span style={{ width: 8, height: 2, background: '#fff', display: 'block', borderRadius: 1 }} />
      ) : checked ? (
        <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
          <path d="M1 4l3 3 5-6" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : null}
    </div>
  )
}
