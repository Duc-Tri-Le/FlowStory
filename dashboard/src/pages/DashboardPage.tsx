import { useState, useEffect, useCallback } from 'react'
import {
  Layers,
  Film,
  Plus,
  Trash2,
  Download,
  CheckCircle2,
  Clock,
  Play,
  Zap,
  Mic,
  Sparkles,
  RefreshCw,
} from 'lucide-react'
import RealVideoPlayer from '../components/storytime/RealVideoPlayer'
import { type StorytimeScene } from '../components/storytime/StorytimePlayer'
import TextOverlayCustomizer, { type TextOverlayConfig, DEFAULT_TEXT_CONFIG } from '../components/storytime/TextOverlayCustomizer'
import { fetchAPI } from '../api/client'
import CreateProjectModal from '../components/projects/CreateProjectModal'

interface PackageItem {
  package_id: string
  title: string
  genre: string
  scenes_count: number
  total_duration: number
  status: string
  is_sample?: boolean
}

export default function DashboardPage() {
  const [packages, setPackages] = useState<PackageItem[]>([])
  const [selectedPackageId, setSelectedPackageId] = useState<string>('sample')
  const [currentScenes, setCurrentScenes] = useState<StorytimeScene[]>([])
  const [textConfig, setTextConfig] = useState<TextOverlayConfig>(DEFAULT_TEXT_CONFIG)
  const [loading, setLoading] = useState(true)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  // Modal state
  const [showBatchModal, setShowBatchModal] = useState(false)

  // Load packages list from backend
  const loadPackages = useCallback(async () => {
    try {
      const res = await fetchAPI<{ ok: boolean; packages: PackageItem[] }>('/api/storytime/packages')
      if (res.ok && res.packages) {
        setPackages(res.packages)
        return res.packages
      }
      setPackages([])
      return []
    } catch {
      setPackages([])
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  // Load specific package details into the Live Player
  const loadPackageScenes = useCallback(async (pkgId: string) => {
    if (!pkgId) {
      setCurrentScenes([])
      setSelectedPackageId('')
      return
    }
    try {
      const res = await fetchAPI<{ ok: boolean; package: { scenes: StorytimeScene[] } }>(
        `/api/storytime/packages/${pkgId}`
      )
      if (res.ok && res.package?.scenes) {
        setCurrentScenes(res.package.scenes)
        setSelectedPackageId(pkgId)
      }
    } catch {
      // Ignore fallback errors
    }
  }, [])

  useEffect(() => {
    loadPackages().then((pkgs) => {
      if (pkgs && pkgs.length > 0) {
        loadPackageScenes(pkgs[0].package_id)
      } else {
        setSelectedPackageId('')
        setCurrentScenes([])
      }
    })
  }, [loadPackages, loadPackageScenes])

  // Delete Package & synchronize completely with database
  const handleDelete = async (pkgId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!window.confirm('Bạn có chắc chắn muốn xóa dự án này? Toàn bộ phân cảnh, video và âm thanh liên quan sẽ bị xóa vĩnh viễn khỏi cơ sở dữ liệu.')) {
      return
    }
    try {
      await fetchAPI(`/api/storytime/packages/${pkgId}`, { method: 'DELETE' })
      setPackages(prev => {
        const next = prev.filter(p => p.package_id !== pkgId)
        if (selectedPackageId === pkgId) {
          if (next.length > 0) {
            loadPackageScenes(next[0].package_id)
          } else {
            setSelectedPackageId('')
            setCurrentScenes([])
          }
        }
        return next
      })
      setStatusMessage('Đã xóa dự án thành công khỏi hệ thống!')
    } catch (err: any) {
      alert('Xóa dự án thất bại: ' + (err?.message || err))
    }
  }

  // Calculate Aggregated Metrics
  const totalVideos = packages.length
  const totalScenes = packages.reduce((acc, p) => acc + (p.scenes_count || 0), 0)
  const totalSeconds = packages.reduce((acc, p) => acc + (p.total_duration || 0), 0)
  const totalMinutes = (totalSeconds / 60).toFixed(1)

  return (
    <div className="p-6 max-w-7xl mx-auto flex flex-col gap-6">
      {/* 1. Header & Live Indicator */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
              <Zap className="w-6 h-6 text-amber-500 fill-amber-500/20" />
              Batch Video Production Hub
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Hàng Loạt Tự Động
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Trung tâm sản xuất video hoạt hình 2D OverSimplified & Kinh Dị Dân Gian tự động qua Google Flow (Imagen 3 & Veo 3).
          </p>
        </div>

        {/* Action Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowBatchModal(true)}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black text-xs flex items-center gap-2 shadow-lg shadow-amber-500/25 active:scale-95 transition-all"
          >
            <Plus className="w-4 h-4 stroke-[3]" />
            <span>Thêm Kịch Bản Hàng Loạt</span>
          </button>
        </div>
      </div>

      {/* 2. Top Summary Metrics (4 Quick Cards) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg flex flex-col gap-1">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Tập Video Đã Tạo</span>
            <Film className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-white tracking-tight mt-1">
            {totalVideos} <span className="text-xs text-slate-500 font-normal">tập</span>
          </div>
          <span className="text-[11px] text-emerald-400 font-medium flex items-center gap-1 mt-0.5">
            <CheckCircle2 className="w-3 h-3" /> Sẵn sàng render
          </span>
        </div>

        {/* Metric 2 */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg flex flex-col gap-1">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Tổng Số Phân Cảnh</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white tracking-tight mt-1">
            {totalScenes} <span className="text-xs text-slate-500 font-normal">cảnh</span>
          </div>
          <span className="text-[11px] text-slate-400">10-25 từ / cảnh (~6s)</span>
        </div>

        {/* Metric 3 */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg flex flex-col gap-1">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Thời Lượng Sản Xuất</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-white tracking-tight mt-1">
            {totalMinutes} <span className="text-xs text-slate-500 font-normal">phút</span>
          </div>
          <span className="text-[11px] text-slate-400">Tương đương {totalSeconds.toFixed(0)} giây</span>
        </div>

        {/* Metric 4 */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg flex flex-col gap-1">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Engine Giọng & Phụ Đề</span>
            <Mic className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-sm font-bold text-slate-200 mt-2 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Edge-TTS + Kịch Bản Gốc
          </div>
          <span className="text-[11px] text-slate-500">Trực tiếp từ kịch bản • Không cần Voice-to-Text</span>
        </div>
      </div>

      {/* Status Alert Banner */}
      {statusMessage && (
        <div className="px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage(null)} className="text-slate-400 hover:text-white text-xs">
            ✕
          </button>
        </div>
      )}

      {/* 3. Main Workspace: Queue Table (1/3: 4 cols) + Live Player (2/3: 8 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Batch Queue Table (4 cols = 1/3) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-xl backdrop-blur-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Film className="w-4 h-4 text-amber-400" />
                  Hàng Đợi Video Hàng Loạt ({packages.length} tập)
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Bấm vào tập bất kỳ để phát thử ngay trên khung xem trước bên phải
                </p>
              </div>

              <button
                onClick={loadPackages}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all text-xs flex items-center gap-1.5"
                title="Làm mới danh sách"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Làm mới</span>
              </button>
            </div>

            {/* Table of Batches */}
            <div className="flex flex-col gap-2.5 overflow-hidden">
              {packages.length === 0 ? (
                <div className="p-8 rounded-xl border border-dashed border-slate-800 flex flex-col items-center justify-center text-center gap-2">
                  <Film className="w-8 h-8 text-slate-600 mb-1" />
                  <span className="text-sm font-semibold text-slate-300">Chưa có dự án nào</span>
                  <span className="text-xs text-slate-500 max-w-xs">
                    Hãy bấm nút "Thêm Kịch Bản Hàng Loạt" phía trên để nạp kịch bản và bắt đầu sản xuất.
                  </span>
                </div>
              ) : (
                packages.map((pkg, idx) => {
                const isSelected = selectedPackageId === pkg.package_id

                return (
                  <div
                    key={pkg.package_id}
                    onClick={() => loadPackageScenes(pkg.package_id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between group ${
                      isSelected
                        ? 'bg-amber-500/10 border-amber-500/50 shadow-md shadow-amber-500/5'
                        : 'bg-slate-950/70 border-slate-800/80 hover:border-slate-700 hover:bg-slate-950'
                    }`}
                  >
                    <div className="flex items-center gap-3.5">
                      <div
                        className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs transition-all ${
                          isSelected
                            ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                            : 'bg-slate-800 text-slate-400 group-hover:bg-slate-700 group-hover:text-white'
                        }`}
                      >
                        {isSelected ? <Play className="w-4 h-4 fill-current ml-0.5" /> : idx + 1}
                      </div>

                      <div className="flex flex-col">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-white group-hover:text-amber-400 transition-colors">
                            {pkg.title}
                          </span>
                          {pkg.is_sample && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300">
                              Mẫu
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                          <span>{pkg.scenes_count} phân cảnh</span>
                          <span>•</span>
                          <span>{pkg.total_duration?.toFixed(1)} giây</span>
                          <span>•</span>
                          <span className="text-emerald-400 font-medium flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Sẵn sàng
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={e => {
                          e.stopPropagation()
                          loadPackageScenes(pkg.package_id)
                        }}
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 hover:text-white font-medium flex items-center gap-1.5 transition-all"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>Phát</span>
                      </button>

                      {!pkg.is_sample && (
                        <button
                          onClick={e => handleDelete(pkg.package_id, e)}
                          className="p-2 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
                          title="Xóa tập này"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                )
              }))}
            </div>
          </div>
        </div>

        {/* Right Column: Live Player Preview (8 cols = 2/3, Sticky) */}
        <div className="lg:col-span-8 flex flex-col gap-4 sticky top-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              Khung Xem Trước Trực Tiếp (16:9)
            </h2>

            <span className="text-xs text-slate-400 font-mono">
              Tập đang chọn: <strong className="text-amber-400">{packages.find(p => p.package_id === selectedPackageId)?.title || 'Chưa chọn'}</strong>
            </span>
          </div>

          {/* Real Google Flow Video Player */}
          <RealVideoPlayer
            initialUuid="8a3fdd42-25a5-40d9-9827-6cd3afaadb24"
            title={`Xem trước: ${packages.find(p => p.package_id === selectedPackageId)?.title || 'Bóng Đen Gian Chuồng Cũ'}`}
          />

          {/* Post-Production Step: Subtitle & Text Overlay Customizer */}
          <TextOverlayCustomizer
            config={textConfig}
            onChange={setTextConfig}
            videoReady={currentScenes.length > 0}
          />

          {/* Export / Quick Info Card */}
          <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Độ phân giải: 1920x1080 (16:9)</span>
              <span>Tốc độ: 30 FPS</span>
            </div>

            <button
              onClick={() => {
                const exportPayload = {
                  package_id: selectedPackageId,
                  exported_at: new Date().toISOString(),
                  text_overlay_config: textConfig,
                  scenes: currentScenes,
                }
                const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `storytime_${selectedPackageId}.json`
                a.click()
              }}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs flex items-center justify-center gap-2 border border-slate-700 transition-all shadow-sm"
            >
              <Download className="w-4 h-4 text-amber-400" />
              <span>Tải Gói Remotion JSON (Kèm Cấu Hình Text)</span>
            </button>
          </div>
        </div>
      </div>

      {/* 4. Unified Batch & Project Creator Modal */}
      <CreateProjectModal
        open={showBatchModal}
        onOpenChange={setShowBatchModal}
        onCreated={() => {
          loadPackages()
        }}
      />
    </div>
  )
}
