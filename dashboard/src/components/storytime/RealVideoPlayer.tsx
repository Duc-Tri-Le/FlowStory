import React, { useState, useRef } from 'react'
import {
  Film,
  Download,
  Upload,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  ExternalLink,
  Sparkles,
} from 'lucide-react'
import { postAPI } from '../../api/client'

interface Props {
  initialUuid?: string
  initialVideoUrl?: string
  title?: string
}

export default function RealVideoPlayer({
  initialUuid = '8a3fdd42-25a5-40d9-9827-6cd3afaadb24',
  initialVideoUrl = '/api/storytime/preview-video/sample.mp4',
  title = 'Video Xem Trước (Google Flow 16:9)',
}: Props) {
  const [uuid, setUuid] = useState(initialUuid)
  const [videoUrl, setVideoUrl] = useState(initialVideoUrl)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'warning' | 'error'; message: string } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)

  React.useEffect(() => {
    if (initialVideoUrl) {
      setVideoUrl(initialVideoUrl)
    }
  }, [initialVideoUrl])

  React.useEffect(() => {
    if (initialUuid) {
      setUuid(initialUuid)
    }
  }, [initialUuid])

  // Fetch video from Google Flow via backend
  const handleFetchFromFlow = async () => {
    if (!uuid.trim()) return
    setLoading(true)
    setStatus(null)

    try {
      const res = await postAPI<{
        ok: boolean
        video_url?: string
        error?: string
        message?: string
      }>('/api/storytime/fetch-flow-video', { uuid: uuid.trim() })

      if (res.ok && res.video_url) {
        setVideoUrl(res.video_url)
        setStatus({
          type: 'success',
          message: `Đã tải thành công video Google Flow (${uuid.slice(0, 8)}...)!`,
        })
        if (videoRef.current) {
          videoRef.current.load()
          videoRef.current.play().catch(() => {})
        }
      } else {
        setStatus({
          type: 'warning',
          message:
            res.message ||
            'Tiện ích Chrome Extension chưa kết nối. Hãy tải video từ flow.google.com rồi bấm nút "Tải lên tệp .mp4" bên dưới để xem ngay.',
        })
      }
    } catch {
      setStatus({
        type: 'warning',
        message:
          'Chưa thể kết nối tới Google Flow Extension. Bạn có thể tải video về máy từ Google Flow và dùng nút "Tải lên tệp .mp4" bên dưới.',
      })
    } finally {
      setLoading(false)
    }
  }

  // Handle local MP4 file upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const localBlobUrl = URL.createObjectURL(file)
    setVideoUrl(localBlobUrl)
    setStatus({
      type: 'success',
      message: `Đang phát tệp video: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`,
    })

    // Upload to backend in background
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch('http://127.0.0.1:8100/api/storytime/upload-preview-video', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (data.ok && data.video_url) {
        setVideoUrl(data.video_url)
      }
    } catch {
      // Keep blob url
    }
  }

  return (
    <div className="flex flex-col gap-4 bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-2xl backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-2.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-sm shadow-emerald-500/50" />
          <h2 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
            <Film className="w-4 h-4 text-amber-400" />
            {title}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-amber-400" />
            Google Flow Veo 3 Video
          </span>
        </div>
      </div>

      {/* Real HTML5 Video Player */}
      <div className="relative w-full aspect-video rounded-xl overflow-hidden bg-black border border-slate-800 shadow-inner group">
        <video
          ref={videoRef}
          controls
          playsInline
          className="w-full h-full object-contain"
          src={videoUrl}
        >
          Trình duyệt của bạn không hỗ trợ thẻ video HTML5.
        </video>
      </div>

      {/* UUID Fetch & Upload Bar */}
      <div className="flex flex-col gap-3 pt-1">
        <div className="flex flex-col sm:flex-row items-center gap-2">
          <div className="relative flex-1 w-full">
            <input
              type="text"
              value={uuid}
              onChange={e => setUuid(e.target.value)}
              placeholder="Nhập UUID video / dự án từ Google Flow..."
              className="w-full bg-slate-950 text-slate-200 text-xs px-3.5 py-2.5 rounded-xl border border-slate-800 focus:border-amber-500/60 outline-none font-mono tracking-tight"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={handleFetchFromFlow}
              disabled={loading || !uuid.trim()}
              className="flex-1 sm:flex-initial px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 shadow-md shadow-amber-500/20 active:scale-95 transition-all disabled:opacity-50"
            >
              {loading ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5 stroke-[2.5]" />
              )}
              <span>Tải từ Google Flow</span>
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs flex items-center justify-center gap-1.5 border border-slate-700 active:scale-95 transition-all"
              title="Tải lên tệp video MP4"
            >
              <Upload className="w-3.5 h-3.5 text-slate-400" />
              <span className="hidden sm:inline">Tải tệp .mp4</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/mp4,video/webm"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
        </div>

        {/* Status / Helper Notification */}
        {status && (
          <div
            className={`p-3 rounded-xl text-xs flex items-start gap-2.5 border leading-relaxed ${
              status.type === 'success'
                ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
                : status.type === 'warning'
                ? 'bg-amber-950/40 text-amber-200 border-amber-800/60'
                : 'bg-rose-950/40 text-rose-300 border-rose-800/60'
            }`}
          >
            {status.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <span>{status.message}</span>
              {status.type === 'warning' && (
                <div className="mt-1 text-[11px] text-slate-400 flex items-center gap-2">
                  <span>Mẹo: Bạn có thể mở</span>
                  <a
                    href="https://flow.google.com/"
                    target="_blank"
                    rel="noreferrer"
                    className="text-amber-400 underline hover:text-amber-300 flex items-center gap-1 font-medium"
                  >
                    Google Flow <ExternalLink className="w-3 h-3" />
                  </a>
                  <span>tải video về và dùng nút "Tải tệp .mp4" để xem trực tiếp ngay lập tức!</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
