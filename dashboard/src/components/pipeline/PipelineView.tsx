import { useState, useEffect, useCallback } from 'react'
import { fetchAPI, postAPI } from '../../api/client'
import { useWebSocketContext } from '../../api/useWebSocketContext'
import { useTranslation } from '../../i18n/useTranslation'
import type { TranslationKey } from '../../i18n/translations'
import { statusLabel, stateLabel } from '../../i18n/labels'
import type { Project, Video, Character, Scene, Request, SceneReview, StatusType } from '../../types'
import { count, sceneStageStatus, charStatus, latestRequest, type SceneStage } from '../../lib/stageStats'
import { Button } from '../ui/button'
import { Avatar, AvatarFallback, AvatarGroup } from '../ui/avatar'
import { Tooltip, TooltipContent, TooltipTrigger } from '../ui/tooltip'
import StageNode from './StageNode'
import SceneCard from './SceneCard'
import SceneDetailSheet from './SceneDetailSheet'
import GenerateVideoDialog from './GenerateVideoDialog'
import { useNavigate } from 'react-router-dom'
import { CheckCircle2, ArrowRight, Clapperboard, Film, RefreshCw } from 'lucide-react'

type StageKey = 'refs' | 'image' | 'video' | 'upscale'

interface PipelineViewProps {
  projectId: string
  videoId: string
}

const STAGE_META: { key: StageKey; idx: string; nameKey: TranslationKey; subtitleKey: TranslationKey }[] = [
  { key: 'refs', idx: '01', nameKey: 'pipeline.railName.refs', subtitleKey: 'pipeline.railSubtitle.refs' },
  { key: 'image', idx: '02', nameKey: 'pipeline.railName.image', subtitleKey: 'pipeline.railSubtitle.image' },
  { key: 'video', idx: '03', nameKey: 'pipeline.railName.video', subtitleKey: 'pipeline.railSubtitle.video' },
  { key: 'upscale', idx: '04', nameKey: 'pipeline.railName.upscale', subtitleKey: 'pipeline.railSubtitle.upscale' },
]

const RETRY_TYPE: Record<SceneStage, string> = {
  image: 'REGENERATE_IMAGE',
  video: 'REGENERATE_VIDEO',
  upscale: 'UPSCALE_VIDEO',
}

export default function PipelineView({ projectId, videoId }: PipelineViewProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [project, setProject] = useState<Project | null>(null)
  const [video, setVideo] = useState<Video | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [scenes, setScenes] = useState<Scene[]>([])
  const [requests, setRequests] = useState<Request[]>([])

  const [activeStage, setActiveStage] = useState<StageKey>('image')
  const [sortFailedFirst, setSortFailedFirst] = useState(false)
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null)
  const [sheetOpen, setSheetOpen] = useState(false)
  const [reviews, setReviews] = useState<Record<string, SceneReview>>({})
  const [reviewRunning, setReviewRunning] = useState<{ sceneId: string; mode: 'light' | 'deep' } | null>(null)
  const [reviewError, setReviewError] = useState<string | null>(null)
  const [retryingSceneId, setRetryingSceneId] = useState<string | null>(null)
  const [generatingRefs, setGeneratingRefs] = useState(false)
  const [generatingImages, setGeneratingImages] = useState(false)
  const [generatingVideos, setGeneratingVideos] = useState(false)
  const [videoDialogOpen, setVideoDialogOpen] = useState(false)
  const [isConcatenating, setIsConcatenating] = useState(false)

  async function handleQuickConcat() {
    if (!videoId) return
    setIsConcatenating(true)
    try {
      const res = await postAPI<{ ok: boolean; video_url: string }>(`/api/videos/${videoId}/concat`, {})
      if (res.ok) {
        navigate(`/storytime?project_id=${projectId}&video_id=${videoId}`)
      }
    } catch (e) {
      console.error('Concat failed:', e)
      alert('Ghép video thất bại: ' + (e instanceof Error ? e.message : String(e)))
    } finally {
      setIsConcatenating(false)
    }
  }

  const { lastEvent } = useWebSocketContext()

  const load = useCallback(async () => {
    const [p, v, c, s, r] = await Promise.all([
      fetchAPI<Project>(`/api/projects/${projectId}`),
      fetchAPI<Video>(`/api/videos/${videoId}`),
      fetchAPI<Character[]>(`/api/projects/${projectId}/characters`),
      fetchAPI<Scene[]>(`/api/scenes?video_id=${videoId}`),
      fetchAPI<Request[]>(`/api/requests?project_id=${projectId}`),
    ])
    setProject(p)
    setVideo(v)
    setCharacters(c)
    setScenes(s)
    setRequests(r)
  }, [projectId, videoId])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!lastEvent) return
    // The backend only ever emits 'request_update' (on PROCESSING/COMPLETED/FAILED transitions),
    // 'worker_tick', and 'urls_refreshed' — any of them means something in this pipeline may have changed.
    if (lastEvent.type === 'request_update' || lastEvent.type === 'urls_refreshed') {
      load()
    }
  }, [lastEvent, load])

  // If characters exist and any lack reference image/media_id, focus on refs stage first
  useEffect(() => {
    if (characters.length > 0 && characters.some(c => !c.reference_image_url && !c.media_id)) {
      setActiveStage('refs')
    }
  }, [characters])

  const videoRequests = requests.filter(r => r.video_id === videoId)
  const anyProcessing = videoRequests.some(r => r.status === 'PROCESSING')
  const pendingCount = videoRequests.filter(r => r.status === 'PENDING').length

  const stageBreakdown: Record<StageKey, ReturnType<typeof count>> = {
    refs: count(characters.map(c => charStatus(c, requests))),
    image: count(scenes.map(s => sceneStageStatus(s, 'image'))),
    video: count(scenes.map(s => sceneStageStatus(s, 'video'))),
    upscale: count(scenes.map(s => sceneStageStatus(s, 'upscale'))),
  }

  const allRefsDone = characters.length > 0 && characters.every(c => c.reference_image_url || charStatus(c, requests) === 'COMPLETED')
  const anyRefProcessing = characters.some(c => charStatus(c, requests) === 'PROCESSING')

  const allImagesDone = scenes.length > 0 && scenes.every(s => sceneStageStatus(s, 'image') === 'COMPLETED')
  const anyImageProcessing = scenes.some(s => sceneStageStatus(s, 'image') === 'PROCESSING')

  const allVideosDone = scenes.length > 0 && scenes.every(s => sceneStageStatus(s, 'video') === 'COMPLETED')
  const anyVideoProcessing = scenes.some(s => sceneStageStatus(s, 'video') === 'PROCESSING')

  let gridScenes = scenes.slice()
  if (activeStage !== 'refs' && sortFailedFirst) {
    const rank: Record<StatusType, number> = { FAILED: 0, PROCESSING: 1, PENDING: 2, COMPLETED: 3 }
    gridScenes = gridScenes.sort((a, b) => rank[sceneStageStatus(a, activeStage as SceneStage)] - rank[sceneStageStatus(b, activeStage as SceneStage)])
  }

  const selectedScene = scenes.find(s => s.id === selectedSceneId) ?? null
  const sheetStage = activeStage === 'refs' ? 'image' : (activeStage as SceneStage)
  const sheetStageMeta = STAGE_META.find(m => m.key === activeStage)!

  function openScene(sceneId: string) {
    setSelectedSceneId(sceneId)
    setSheetOpen(true)
    setReviewError(null)
  }

  async function runReview(mode: 'light' | 'deep') {
    if (!selectedScene) return
    setReviewRunning({ sceneId: selectedScene.id, mode })
    setReviewError(null)
    try {
      const result = await fetchAPI<SceneReview>(
        `/api/videos/${videoId}/scenes/${selectedScene.id}/review?project_id=${projectId}&mode=${mode}`,
        { method: 'POST' }
      )
      setReviews(prev => ({ ...prev, [selectedScene.id]: result }))
    } catch (e) {
      setReviewError(e instanceof Error ? e.message : 'Review failed')
    } finally {
      setReviewRunning(null)
    }
  }

  async function retryStage() {
    if (!selectedScene) return
    setRetryingSceneId(selectedScene.id)
    try {
      await fetchAPI('/api/requests', {
        method: 'POST',
        body: JSON.stringify({ type: RETRY_TYPE[sheetStage], scene_id: selectedScene.id, project_id: projectId, video_id: videoId }),
      })
      await load()
    } catch (e) {
      console.error(e)
    } finally {
      setRetryingSceneId(null)
    }
  }

  const [regeneratingCharId, setRegeneratingCharId] = useState<string | null>(null)

  async function handleRegenerateChar(cid: string) {
    setRegeneratingCharId(cid)
    try {
      await fetchAPI('/api/requests', {
        method: 'POST',
        body: JSON.stringify({
          type: 'REGENERATE_CHARACTER_IMAGE',
          character_id: cid,
          project_id: projectId,
        }),
      })
      await load()
    } catch (e) {
      console.error(e)
    } finally {
      setRegeneratingCharId(null)
    }
  }

  async function handleGenerateAllRefs() {
    const uncompleted = characters.filter(c => !c.reference_image_url || charStatus(c, requests) !== 'COMPLETED')
    const toGen = uncompleted.length > 0 ? uncompleted : characters
    if (!toGen.length) return
    setGeneratingRefs(true)
    try {
      const reqs = toGen.map(c => ({
        type: 'GENERATE_CHARACTER_IMAGE',
        character_id: c.id,
        project_id: projectId,
      }))
      await postAPI('/api/requests/batch', { requests: reqs })
      await load()
    } catch (e) {
      console.error('Failed to generate character reference images:', e)
    } finally {
      setGeneratingRefs(false)
    }
  }

  async function handleGenerateAllVideos(sceneIds: string[]) {
    if (!sceneIds.length) return
    setGeneratingVideos(true)
    try {
      const reqs = sceneIds.map(scene_id => ({
        type: 'GENERATE_VIDEO',
        scene_id,
        project_id: projectId,
        video_id: videoId,
      }))
      await postAPI('/api/requests/batch', { requests: reqs })
      await load()
    } catch (e) {
      console.error(e)
    } finally {
      setGeneratingVideos(false)
    }
  }

  async function handleGenerateAllImages() {
    const uncompleted = scenes.filter(s => sceneStageStatus(s, 'image') !== 'COMPLETED')
    const toGen = uncompleted.length > 0 ? uncompleted : scenes
    if (!toGen.length) return
    setGeneratingImages(true)
    try {
      const orient = video?.orientation || project?.orientation || 'VERTICAL'
      const reqs = toGen.map(sc => ({
        type: 'GENERATE_IMAGE',
        scene_id: sc.id,
        project_id: projectId,
        video_id: videoId,
        orientation: orient,
      }))
      await postAPI('/api/requests/batch', { requests: reqs })
      await load()
    } catch (e) {
      console.error('Failed to generate scene images:', e)
    } finally {
      setGeneratingImages(false)
    }
  }

  async function handleStopPipeline() {
    try {
      await postAPI(`/api/projects/${projectId}/stop-pipeline`, {})
      await load()
    } catch (e) {
      console.error('Failed to stop pipeline:', e)
    }
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-6 pb-4" style={{ borderBottom: '1px solid var(--border)' }}>
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2.5 text-[10px] tracking-widest uppercase" style={{ color: 'var(--muted)' }}>
            <span style={{ color: 'var(--accent)' }}>{t('app.breadcrumbRoot')}</span>
            <span>/</span>
            <span>{project?.name ?? '…'}</span>
            <span>/</span>
            <span style={{ color: 'var(--text)' }}>{video?.title ?? '…'}</span>
          </div>
          <div className="flex items-baseline gap-3.5">
            <h1 className="m-0 text-xl font-semibold tracking-tight" style={{ color: 'var(--text)' }}>{t('pipeline.heading')}</h1>
            <span className="text-[11px]" style={{ color: 'var(--muted)' }}>{t('pipeline.sceneCount', { n: scenes.length })}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {characters.length > 0 && (
            <div className="flex flex-col gap-1.5 items-end">
              <span className="text-[9px] tracking-widest uppercase" style={{ color: 'var(--muted)' }}>{t('pipeline.castEntities')}</span>
              <AvatarGroup>
                {characters.map(c => (
                  <Tooltip key={c.id}>
                    <TooltipTrigger asChild>
                      <Avatar>
                        <AvatarFallback>{c.name.slice(0, 2).toUpperCase()}</AvatarFallback>
                      </Avatar>
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="flex flex-col gap-1 max-w-[240px]">
                        <span className="text-[11px] tracking-wide">{c.name} · {c.entity_type}</span>
                        {c.description && <span className="text-[11px] opacity-75 leading-snug">{c.description}</span>}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                ))}
              </AvatarGroup>
            </div>
          )}
          <div className="w-px h-8" style={{ background: 'var(--border)' }} />
          <div className="flex items-center gap-2">
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: anyProcessing ? 'var(--yellow)' : 'var(--muted)', animation: anyProcessing ? 'pulse 1.6s ease-in-out infinite' : 'none' }}
            />
            <span className="text-[11px]" style={{ color: anyProcessing ? 'var(--yellow)' : 'var(--muted)' }}>
              {stateLabel(t, anyProcessing ? 'RUNNING' : 'IDLE')}
            </span>
            <span className="text-[11px]" style={{ color: 'var(--muted)' }}>· {t('pipeline.queue', { n: pendingCount })}</span>
            {(anyProcessing || pendingCount > 0) && (
              <Button
                variant="destructive"
                size="sm"
                className="h-6 px-2 text-[10px] ml-1 bg-red-600/90 hover:bg-red-600 text-white gap-1"
                onClick={handleStopPipeline}
                title="Dừng xử lý và xóa toàn bộ hàng đợi đang chờ"
              >
                <span>🛑 Dừng</span>
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Stage rail */}
      <div className="flex items-stretch gap-2.5">
        {STAGE_META.map(m => (
          <StageNode
            key={m.key}
            idx={m.idx}
            name={t(m.nameKey)}
            subtitle={t(m.subtitleKey)}
            {...stageBreakdown[m.key]}
            isActive={activeStage === m.key}
            onClick={() => setActiveStage(m.key)}
          />
        ))}
      </div>

      {/* Human-in-the-Loop Checkpoint Guidance Banner */}
      <div
        className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl shadow-lg transition-all"
        style={{
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
          border: '1px solid rgba(148, 163, 184, 0.15)',
        }}
      >
        <div className="flex items-start gap-3.5">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-lg font-bold text-xs shrink-0 mt-0.5"
            style={{
              background: activeStage === 'refs' ? 'rgba(245, 158, 11, 0.2)' : activeStage === 'image' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              color: activeStage === 'refs' ? '#f59e0b' : activeStage === 'image' ? '#60a5fa' : '#34d399',
              border: `1px solid ${activeStage === 'refs' ? 'rgba(245, 158, 11, 0.4)' : activeStage === 'image' ? 'rgba(59, 130, 246, 0.4)' : 'rgba(16, 185, 129, 0.4)'}`,
            }}
          >
            {activeStage === 'refs' ? '01' : activeStage === 'image' ? '02' : '03'}
          </div>
          <div className="flex flex-col gap-1">
            <div className="text-xs font-semibold flex items-center gap-2 flex-wrap" style={{ color: 'var(--text)' }}>
              {activeStage === 'refs' && (
                <>
                  <span>🔍 Chặng 1: Kiểm tra Nhân vật & Bối cảnh</span>
                  {allRefsDone ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                      ✓ Đã có ảnh tham chiếu
                    </span>
                  ) : anyRefProcessing ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium animate-pulse" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                      ⏳ Đang tạo ảnh ({stageBreakdown.refs.done}/{stageBreakdown.refs.total})
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ background: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8' }}>
                      Chờ kiểm tra ({stageBreakdown.refs.done}/{stageBreakdown.refs.total})
                    </span>
                  )}
                </>
              )}
              {activeStage === 'image' && (
                <>
                  <span>🖼️ Chặng 2: Kiểm tra Ảnh bối cảnh các phân cảnh</span>
                  {allImagesDone ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                      ✓ Tất cả ảnh đã hoàn tất
                    </span>
                  ) : anyImageProcessing ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium animate-pulse" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                      ⏳ Đang tạo ảnh ({stageBreakdown.image.done}/{stageBreakdown.image.total})
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ background: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8' }}>
                      Chờ tạo ảnh ({stageBreakdown.image.done}/{stageBreakdown.image.total})
                    </span>
                  )}
                </>
              )}
              {activeStage === 'video' && (
                <>
                  <span>🎬 Chặng 3: Tạo Video chuyển động các phân cảnh</span>
                  {allVideosDone ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                      ✓ Hoàn thành tất cả video
                    </span>
                  ) : anyVideoProcessing ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium animate-pulse" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                      ⏳ Đang render video ({stageBreakdown.video.done}/{stageBreakdown.video.total})
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ background: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8' }}>
                      Chờ bạn duyệt tạo video
                    </span>
                  )}
                </>
              )}
              {activeStage === 'upscale' && (
                <span>💎 Chặng 4: Nâng cấp chất lượng 4K</span>
              )}
            </div>
            <p className="text-[11px] m-0" style={{ color: 'var(--muted)' }}>
              {activeStage === 'refs' &&
                'Xem xét kỹ ảnh tham chiếu nhân vật và thông tin bối cảnh bên dưới. Khi đã ưng ý, bấm nút bên phải để bắt đầu tạo ảnh bối cảnh.'}
              {activeStage === 'image' &&
                (allImagesDone
                  ? 'Tất cả ảnh bối cảnh đã xong! Hãy duyệt kỹ từng khung hình bên dưới. Khi bạn đồng ý, bấm nút bên phải để bắt đầu tạo video.'
                  : 'Kiểm tra mô tả prompt ảnh cảnh bên dưới. Bấm nút bên phải để tiến hành tạo ảnh cho các phân cảnh.')}
              {activeStage === 'video' &&
                (allVideosDone
                  ? 'Tuyệt vời! Tất cả video phân cảnh đã hoàn thành. Hãy kiểm tra các video bên dưới hoặc bấm nút bên phải để sang Storytime ghép thành phim hoàn chỉnh.'
                  : 'Chỉ tạo video sau khi bạn đã kiểm tra và đồng ý với ảnh bối cảnh ở bước trước.')}
              {activeStage === 'upscale' &&
                'Nâng cấp độ phân giải các video đã hoàn thành lên 4K.'}
            </p>
          </div>
        </div>

        {/* Stage Checkpoint Action Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          {activeStage === 'refs' && (
            <>
              {!allRefsDone && (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={generatingRefs || anyRefProcessing}
                  onClick={handleGenerateAllRefs}
                  className="text-xs h-8"
                >
                  {generatingRefs || anyRefProcessing ? 'Đang gửi...' : '▶ Tạo tất cả ảnh nhân vật'}
                </Button>
              )}
              <Button
                size="sm"
                onClick={() => {
                  setActiveStage('image')
                  if (!allImagesDone && !anyImageProcessing && stageBreakdown.image.done === 0) {
                    handleGenerateAllImages()
                  }
                }}
                style={{ background: 'var(--accent)', color: '#fff' }}
                className="text-xs h-8 font-semibold flex items-center gap-1.5 shadow-md"
              >
                <span>Tiếp tục: Tạo ảnh bối cảnh</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </>
          )}

          {activeStage === 'image' && (
            <>
              {!allImagesDone && (
                <Button
                  size="sm"
                  disabled={generatingImages || anyImageProcessing}
                  onClick={handleGenerateAllImages}
                  style={{ background: 'var(--accent)', color: '#fff' }}
                  className="text-xs h-8"
                >
                  {generatingImages || anyImageProcessing ? 'Đang gửi...' : '▶ Tạo tất cả ảnh bối cảnh'}
                </Button>
              )}
              {allImagesDone && (
                <Button
                  size="sm"
                  onClick={() => setVideoDialogOpen(true)}
                  className="text-xs h-8 font-semibold flex items-center gap-1.5 shadow-md"
                  style={{ background: '#10b981', color: '#fff' }}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Tôi đồng ý, Tạo Video các cảnh →</span>
                </Button>
              )}
            </>
          )}

          {activeStage === 'video' && (
            allVideosDone ? (
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setVideoDialogOpen(true)}
                  className="text-xs h-8"
                >
                  Tùy chọn tạo lại...
                </Button>
                <Button
                  size="sm"
                  onClick={handleQuickConcat}
                  disabled={isConcatenating}
                  className="text-xs h-8 font-bold flex items-center gap-1.5 shadow-md border-0"
                  style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#090a0f' }}
                  title="Ghép nối tất cả các phân cảnh thành 1 video duy nhất"
                >
                  {isConcatenating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Film className="w-3.5 h-3.5" />}
                  <span>{isConcatenating ? 'Đang ghép video...' : '🎬 Ghép 3 Cảnh Thành 1 Video'}</span>
                </Button>
                <Button
                  size="sm"
                  onClick={() => navigate(`/storytime?project_id=${projectId}&video_id=${videoId}`)}
                  className="text-xs h-8 font-semibold flex items-center gap-1.5 shadow-md"
                  style={{ background: '#10b981', color: '#fff' }}
                >
                  <Clapperboard className="w-3.5 h-3.5" />
                  <span>Storytime (Ghép phim & Lồng tiếng) →</span>
                </Button>
              </div>
            ) : (
              <Button
                size="sm"
                disabled={generatingVideos || anyVideoProcessing}
                onClick={() => setVideoDialogOpen(true)}
                style={{ background: 'var(--accent)', color: '#fff' }}
                className="text-xs h-8"
              >
                {generatingVideos || anyVideoProcessing ? 'Đang gửi...' : '▶ Tạo Video'}
              </Button>
            )
          )}
        </div>
      </div>

      {/* Sort toggle + scene/refs grid */}
      {activeStage === 'refs' ? (
        <div>
          <div className="flex items-center justify-between gap-4 mb-2.5">
            <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
              {t('pipeline.refsHeading', { n: characters.length })}
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={generatingRefs || anyRefProcessing}
                onClick={handleGenerateAllRefs}
                className="text-xs h-7"
              >
                {generatingRefs || anyRefProcessing ? 'Đang gửi...' : '▶ Tạo tất cả ảnh nhân vật'}
              </Button>
            </div>
          </div>
          <div className="grid gap-2.5" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
            {characters.map(c => {
              const st = charStatus(c, requests)
              const isLoc = c.entity_type === 'location'
              return (
                <div key={c.id} className="flex flex-col gap-1.5 p-3 rounded-lg text-xs" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
                  <div className="w-full rounded overflow-hidden flex items-center justify-center relative" style={{ aspectRatio: '16/9', background: '#090a0f', maxHeight: '130px' }}>
                    {c.reference_image_url ? (
                      <img src={c.reference_image_url} alt={c.name} className="w-full h-full object-contain bg-white" />
                    ) : (
                      <span style={{ color: 'var(--muted)', fontSize: '10px' }}>{t('pipeline.noImage')}</span>
                    )}
                    <span
                      className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded text-[9px] font-medium border"
                      style={{
                        background: isLoc ? 'rgba(59, 130, 246, 0.85)' : 'rgba(245, 158, 11, 0.85)',
                        color: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                      }}
                    >
                      {isLoc ? '📍 Bối cảnh' : '👤 Nhân vật'}
                    </span>
                  </div>
                  <div className="font-semibold truncate text-xs" style={{ color: 'var(--text)' }} title={c.name}>{c.name}</div>
                  {c.description && (
                    <div className="text-[10px] line-clamp-2 leading-relaxed" style={{ color: 'var(--muted)' }} title={c.description}>
                      {c.description}
                    </div>
                  )}
                  <div className="flex items-center gap-1.5 pt-1" style={{ fontSize: '10px' }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: `var(--${st === 'COMPLETED' ? 'green' : st === 'PROCESSING' ? 'yellow' : st === 'FAILED' ? 'red' : 'border'})` }} />
                    <span style={{ color: 'var(--muted)' }}>{statusLabel(t, st)}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 px-1.5 text-[10px] w-full mt-1"
                    disabled={st === 'PROCESSING' || regeneratingCharId === c.id}
                    onClick={() => handleRegenerateChar(c.id)}
                  >
                    {st === 'PROCESSING' || regeneratingCharId === c.id ? 'Đang tạo...' : 'Tạo lại ảnh'}
                  </Button>
                </div>
              )
            })}
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between gap-4">
            <h2 className="m-0 text-xs tracking-widest uppercase" style={{ color: 'var(--text)' }}>
              {t('pipeline.stageHeading', { idx: STAGE_META.find(m => m.key === activeStage)!.idx, name: t(STAGE_META.find(m => m.key === activeStage)!.nameKey) })}
            </h2>
            <div className="flex items-center gap-2">
              {activeStage === 'image' && (
                <Button
                  size="sm"
                  disabled={generatingImages}
                  onClick={handleGenerateAllImages}
                  style={{ background: 'var(--accent)', color: '#fff' }}
                >
                  {generatingImages ? 'Đang gửi...' : '▶ Tạo tất cả ảnh'}
                </Button>
              )}
              {activeStage === 'video' && (
                allVideosDone ? (
                  <Button
                    size="sm"
                    onClick={() => navigate('/storytime')}
                    className="text-xs h-7 font-medium flex items-center gap-1.5"
                    style={{ background: '#10b981', color: '#fff' }}
                  >
                    <Clapperboard className="w-3.5 h-3.5" />
                    <span>Sang Storytime →</span>
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    disabled={generatingVideos}
                    onClick={() => setVideoDialogOpen(true)}
                    style={{ background: 'var(--accent)', color: '#fff' }}
                  >
                    {generatingVideos ? 'Đang gửi...' : '▶ Tạo Video'}
                  </Button>
                )
              )}
              <span className="text-[10px] tracking-wide uppercase" style={{ color: 'var(--muted)' }}>{t('pipeline.sort')}</span>
              <Button variant="outline" size="sm" onClick={() => setSortFailedFirst(v => !v)}>
                {sortFailedFirst ? t('pipeline.sortFailuresFirst') : t('pipeline.sortSceneOrder')}
              </Button>
            </div>
          </div>

          <div className="grid gap-3.5" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(268px, 1fr))' }}>
            {gridScenes.map(scene => {
              const stage = activeStage as SceneStage
              const req = latestRequest(requests, scene.id, stage)
              return (
                <SceneCard
                  key={scene.id}
                  scene={scene}
                  stage={stage}
                  retries={req?.retry_count ?? 0}
                  verdict={stage === 'video' ? reviews[scene.id]?.verdict : undefined}
                  onClick={() => openScene(scene.id)}
                />
              )
            })}
          </div>
        </>
      )}

      <SceneDetailSheet
        key={selectedSceneId}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        scene={selectedScene}
        stage={sheetStage}
        stageName={t(sheetStageMeta.nameKey)}
        characters={characters}
        requests={selectedScene ? requests.filter(r => r.scene_id === selectedScene.id) : []}
        review={selectedScene ? reviews[selectedScene.id] : undefined}
        reviewRunning={!!selectedScene && reviewRunning?.sceneId === selectedScene.id}
        runningMode={reviewRunning?.mode ?? null}
        reviewError={reviewError}
        onRunReview={runReview}
        onRetry={retryStage}
        retrying={!!selectedScene && retryingSceneId === selectedScene.id}
        onSceneUpdated={load}
      />

      <GenerateVideoDialog
        open={videoDialogOpen}
        onOpenChange={setVideoDialogOpen}
        scenes={scenes}
        projectId={projectId}
        videoId={videoId}
        onSubmit={handleGenerateAllVideos}
        submitting={generatingVideos}
      />
    </div>
  )
}
