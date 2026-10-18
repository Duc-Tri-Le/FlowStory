import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchAPI, patchAPI } from '../api/client'
import type { Project, Character, Video, Scene, Request } from '../types'
import EditableText from '../components/projects/EditableText'
import PipelineView from '../components/pipeline/PipelineView'
import { count, charStatus, videoStageBreakdown, type SceneStage } from '../lib/stageStats'
import { useTranslation } from '../i18n/useTranslation'
import { projectStatusLabel, stageLowerLabel } from '../i18n/labels'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import { Button } from '../components/ui/button'
import { Trash2 } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog'

type Tab = 'pipeline' | 'overview'
const STAGE_KEYS: ('refs' | SceneStage)[] = ['refs', 'image', 'video', 'upscale']

interface Props {
  projectId: string
  onBack: () => void
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}

export default function ProjectDetailPage({ projectId, onBack }: Props) {
  const { t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawTab = searchParams.get('tab')
  const tab: Tab = rawTab === 'overview' ? 'overview' : 'pipeline'

  const [project, setProject] = useState<Project | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [videos, setVideos] = useState<Video[]>([])
  const [scenesByVideo, setScenesByVideo] = useState<Record<string, Scene[]>>({})
  const [requests, setRequests] = useState<Request[]>([])
  const [loading, setLoading] = useState(true)
  const [pipelineVideoId, setPipelineVideoId] = useState<string>('')

  // Copy UUID state
  const [copiedId, setCopiedId] = useState<string | null>(null)

  // Delete project state
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  async function handleDeleteCurrentProject() {
    if (!project) return
    setIsDeleting(true)
    try {
      await fetchAPI(`/api/projects/${project.id}`, { method: 'DELETE' })
      setDeleteConfirmOpen(false)
      onBack()
    } catch (e) {
      console.error('Failed to delete project:', e)
    } finally {
      setIsDeleting(false)
    }
  }

  const fetchAll = useCallback(async () => {
    setLoading(true)
    const [proj, chars, vids] = await Promise.all([
      fetchAPI<Project>(`/api/projects/${projectId}`),
      fetchAPI<Character[]>(`/api/projects/${projectId}/characters`),
      fetchAPI<Video[]>(`/api/videos?project_id=${projectId}`),
    ])
    const sceneLists = await Promise.all(vids.map(v => fetchAPI<Scene[]>(`/api/scenes?video_id=${v.id}`)))
    const sbv: Record<string, Scene[]> = {}
    vids.forEach((v, i) => { sbv[v.id] = sceneLists[i] })
    const reqs = await fetchAPI<Request[]>(`/api/requests?project_id=${projectId}`)

    setProject(proj)
    setCharacters(chars)
    setVideos(vids)
    setScenesByVideo(sbv)
    setRequests(reqs)
    setPipelineVideoId(prev => prev && vids.some(v => v.id === prev) ? prev : (vids[0]?.id ?? ''))
    setLoading(false)
  }, [projectId])

  useEffect(() => { Promise.resolve().then(fetchAll) }, [fetchAll])

  function setTab(t: Tab) {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.set('tab', t)
      return next
    })
  }

  // Copy UUID to clipboard
  async function handleCopyId(id: string) {
    await navigator.clipboard.writeText(id)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  async function patchProject(field: string, value: string) {
    await patchAPI(`/api/projects/${projectId}`, { [field]: value })
    fetchAll()
  }

  if (loading || !project) {
    return <div className="text-xs" style={{ color: 'var(--muted)' }}>{t('projectDetail.loading')}</div>
  }

  const allScenes = videos.flatMap(v => scenesByVideo[v.id] ?? [])
  const stageRollup: Record<'refs' | SceneStage, ReturnType<typeof count>> = {
    refs: count(characters.map(c => charStatus(c, requests))),
    ...videoStageBreakdown(allScenes),
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-baseline gap-3">
            <h1 className="m-0 text-lg font-semibold" style={{ color: 'var(--text)' }}>{project.name}</h1>
            <Badge variant="outline">{project.material}</Badge>
            <Badge variant="outline">{projectStatusLabel(t, project.status)}</Badge>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px]" style={{ color: 'var(--muted)' }}>
              {allScenes.length} phân cảnh · tạo {formatDate(project.created_at)}
            </span>
            <button
              onClick={() => handleCopyId(project.id)}
              style={{ fontSize: 9, padding: '1px 7px', borderRadius: 4, background: copiedId === project.id ? 'var(--green)' : 'var(--surface)', border: '1px solid var(--border)', color: copiedId === project.id ? '#fff' : 'var(--accent)', cursor: 'pointer', fontFamily: 'monospace' }}
              title={project.id}
            >
              {copiedId === project.id ? '✓ Copied' : '⧉ UUID'}
            </button>
            <a href={`https://flow.google.com/studio/${project.id}`} target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 10, color: 'var(--accent)', textDecoration: 'none' }} title="Open in Google Flow">
              ↗ Flow
            </a>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/15"
            onClick={() => setDeleteConfirmOpen(true)}
            title="Xóa dự án này"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Xóa dự án</span>
          </Button>
          <Button variant="ghost" size="sm" onClick={onBack}>{t('projectDetail.back')}</Button>
        </div>
      </div>

      <Tabs value={tab} onValueChange={v => setTab(v as Tab)}>
        <TabsList>
          <TabsTrigger value="pipeline">{t('projectDetail.tab.pipeline')}</TabsTrigger>
          <TabsTrigger value="overview">{t('projectDetail.tab.overview')}</TabsTrigger>
        </TabsList>

        <TabsContent value="pipeline" className="pt-4">
          {videos.length === 0 ? (
            <div className="text-xs" style={{ color: 'var(--muted)' }}>{t('projectDetail.pipeline.noVideos')}</div>
          ) : (
            <div className="flex flex-col gap-4">
              {videos.length > 1 && (
                <div className="flex items-center gap-2">
                  <span className="text-[9px] tracking-widest" style={{ color: 'var(--muted)' }}>{t('projectDetail.pipeline.videoLabel')}</span>
                  {videos.map(v => (
                    <Button key={v.id} variant={v.id === pipelineVideoId ? 'default' : 'outline'} size="sm" onClick={() => setPipelineVideoId(v.id)}>
                      {v.title}
                    </Button>
                  ))}
                </div>
              )}
              {pipelineVideoId && <PipelineView projectId={projectId} videoId={pipelineVideoId} />}
            </div>
          )}
        </TabsContent>

        <TabsContent value="overview" className="pt-4">
          <div className="grid gap-4" style={{ gridTemplateColumns: '1.4fr 1fr' }}>
            <Card className="py-4">
              <CardHeader>
                <CardTitle className="text-xs tracking-widest uppercase">{t('projectDetail.card.projectFields')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-3.5">
                  {[
                    { label: t('projectDetail.field.name'), value: project.name, field: 'name', multiline: false },
                    { label: t('projectDetail.field.description'), value: project.description ?? '', field: 'description', multiline: true },
                    { label: t('projectDetail.field.story'), value: project.story ?? '', field: 'story', multiline: true },
                  ].map(f => (
                    <div key={f.field} className="flex flex-col gap-1">
                      <span className="text-[9px] tracking-widest" style={{ color: 'var(--muted)' }}>{f.label}</span>
                      <div className="rounded-md px-2.5 py-2 text-xs" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                        <EditableText value={f.value} onSave={v => patchProject(f.field, v)} multiline={f.multiline} className="text-xs" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="flex flex-col gap-4">
              <Card className="py-4">
                <CardHeader>
                  <CardTitle className="text-xs tracking-widest uppercase">{t('projectDetail.card.narrator')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col gap-1.5 text-[11px]">
                    <div className="flex justify-between"><span style={{ color: 'var(--muted)' }}>{t('projectDetail.narrator.enabled')}</span><span>{project.narrator_voice ? t('projectDetail.true') : t('projectDetail.false')}</span></div>
                    <div className="flex justify-between"><span style={{ color: 'var(--muted)' }}>{t('projectDetail.narrator.voice')}</span><span>{project.narrator_voice ?? t('projectDetail.noNarration')}</span></div>
                    <div className="flex justify-between"><span style={{ color: 'var(--muted)' }}>{t('projectDetail.narrator.refAudio')}</span><span>{project.narrator_ref_audio ?? t('common.dash')}</span></div>
                  </div>
                </CardContent>
              </Card>

              <Card className="py-4">
                <CardHeader>
                  <CardTitle className="text-xs tracking-widest uppercase">{t('projectDetail.card.stageRollup')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col gap-2.5">
                    {STAGE_KEYS.map(key => {
                      const c = stageRollup[key]
                      const pct = c.total > 0 ? Math.round((c.done / c.total) * 100) : 0
                      return (
                        <div key={key} className="grid items-center gap-2.5" style={{ gridTemplateColumns: '60px 1fr 50px' }}>
                          <span className="text-[10px] tracking-wide uppercase" style={{ color: 'var(--text)' }}>{stageLowerLabel(t, key)}</span>
                          <Progress value={pct} className="h-1" />
                          <span className="text-[10px] text-right" style={{ color: 'var(--muted)' }}>{c.done}/{c.total}</span>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Delete Project Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-400">
              <Trash2 className="w-5 h-5 text-red-500" />
              <span>Xóa dự án?</span>
            </DialogTitle>
            <DialogDescription className="text-xs pt-2 leading-relaxed" style={{ color: 'var(--muted)' }}>
              Bạn có chắc chắn muốn xóa dự án <strong>"{project?.name}"</strong>?
              <br />
              Tất cả các phân cảnh, nhân vật, bối cảnh và video liên quan sẽ bị xóa vĩnh viễn khỏi hệ thống. Thao tác này không thể hoàn tác.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0 pt-3">
            <Button variant="ghost" size="sm" onClick={() => setDeleteConfirmOpen(false)} disabled={isDeleting}>
              Hủy
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={handleDeleteCurrentProject}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-500 text-white"
            >
              {isDeleting ? 'Đang xóa...' : 'Xác nhận xóa'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
