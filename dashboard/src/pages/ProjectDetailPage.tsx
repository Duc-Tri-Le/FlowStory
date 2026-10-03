import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchAPI, patchAPI, getProxyDownloadUrl, downloadViaProxy } from '../api/client'
import type { Project, Character, Video, Scene, Request } from '../types'
import EditableText from '../components/projects/EditableText'
import PipelineView from '../components/pipeline/PipelineView'
import { count, charStatus, videoStageBreakdown, type SceneStage } from '../lib/stageStats'
import { useTranslation } from '../i18n/useTranslation'
import { statusLabel, stateLabel, projectStatusLabel, stageLowerLabel } from '../i18n/labels'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '../components/ui/table'
import { Button } from '../components/ui/button'

// ─── Download helper (via proxy to bypass CORS) ───────────────
async function downloadUrl(url: string, filename: string) {
  downloadViaProxy(url, filename)
  await new Promise(r => setTimeout(r, 350))
}


type Tab = 'overview' | 'characters' | 'videos' | 'pipeline'
const STAGE_KEYS: ('refs' | SceneStage)[] = ['refs', 'image', 'video', 'upscale']

interface Props {
  projectId: string
  onBack: () => void
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}

const STATUS_COLOR: Record<string, string> = {
  COMPLETED: 'var(--green)',
  PROCESSING: 'var(--yellow)',
  FAILED: 'var(--red)',
  PENDING: 'var(--muted)',
}

export default function ProjectDetailPage({ projectId, onBack }: Props) {
  const { t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = (searchParams.get('tab') as Tab) ?? 'overview'

  const [project, setProject] = useState<Project | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [videos, setVideos] = useState<Video[]>([])
  const [scenesByVideo, setScenesByVideo] = useState<Record<string, Scene[]>>({})
  const [requests, setRequests] = useState<Request[]>([])
  const [loading, setLoading] = useState(true)
  const [pipelineVideoId, setPipelineVideoId] = useState<string>('')


  // Batch download state
  const [downloadingVideoId, setDownloadingVideoId] = useState<string | null>(null)
  const [downloadProgress, setDownloadProgress] = useState<{ done: number; total: number } | null>(null)

  // Copy UUID state
  const [copiedId, setCopiedId] = useState<string | null>(null)

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

  const [regeneratingCharId, setRegeneratingCharId] = useState<string | null>(null)

  // Copy UUID to clipboard
  async function handleCopyId(id: string) {
    await navigator.clipboard.writeText(id)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  // Batch download all images for a video
  async function handleBatchDownload(videoId: string) {
    const scenes = scenesByVideo[videoId] ?? []
    const withImg = scenes.filter(s => s.vertical_image_url || s.horizontal_image_url)
    if (!withImg.length) return
    setDownloadingVideoId(videoId)
    setDownloadProgress({ done: 0, total: withImg.length })
    for (let i = 0; i < withImg.length; i++) {
      const s = withImg[i]
      const url = s.vertical_image_url || s.horizontal_image_url
      if (url) {
        const ext = url.split('.').pop()?.split('?')[0] || 'jpg'
        await downloadUrl(url, `scene_${String(i + 1).padStart(3, '0')}.${ext}`)
      }
      setDownloadProgress({ done: i + 1, total: withImg.length })
    }
    setDownloadingVideoId(null)
    setDownloadProgress(null)
  }

  // Batch download all character reference images
  async function handleBatchDownloadChars() {
    const withImg = characters.filter(c => c.reference_image_url)
    for (let i = 0; i < withImg.length; i++) {
      const ch = withImg[i]
      if (ch.reference_image_url) {
        downloadViaProxy(ch.reference_image_url, `${ch.name}_ref.jpg`)
        await new Promise(r => setTimeout(r, 350))
      }
    }
  }


  async function patchProject(field: string, value: string) {
    await patchAPI(`/api/projects/${projectId}`, { [field]: value })
    fetchAll()
  }

  async function patchChar(cid: string, field: string, value: string) {
    const updates: Record<string, string> = { [field]: value }
    if (field === 'description') {
      updates.image_prompt = value
    }
    await patchAPI(`/api/characters/${cid}`, updates)
    fetchAll()
  }

  async function handleRegenerateChar(cid: string) {
    setRegeneratingCharId(cid)
    try {
      await fetchAPI('/api/requests', {
        method: 'POST',
        body: JSON.stringify({
          type: 'REGENERATE_CHARACTER_IMAGE',
          character_id: cid,
          project_id: projectId
        })
      })
      await fetchAll()
    } catch (e) {
      console.error(e)
    } finally {
      setRegeneratingCharId(null)
    }
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
              {t('projectDetail.header', { id: project.id, date: formatDate(project.created_at), videos: videos.length, scenes: allScenes.length })}
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
        <Button variant="ghost" size="sm" onClick={onBack}>{t('projectDetail.back')}</Button>
      </div>

      <Tabs value={tab} onValueChange={v => setTab(v as Tab)}>
        <TabsList>
          <TabsTrigger value="overview">{t('projectDetail.tab.overview')}</TabsTrigger>
          <TabsTrigger value="characters">{t('projectDetail.tab.characters', { n: characters.length })}</TabsTrigger>
          <TabsTrigger value="videos">{t('projectDetail.tab.videos', { n: videos.length })}</TabsTrigger>
          <TabsTrigger value="pipeline">{t('projectDetail.tab.pipeline')}</TabsTrigger>
        </TabsList>

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

        <TabsContent value="characters" className="pt-4">
          {characters.length === 0 ? (
            <div className="text-xs" style={{ color: 'var(--muted)' }}>{t('projectDetail.noCharacters')}</div>
          ) : (
            <div className="flex flex-col gap-3.5">
              {/* Batch download reference images banner */}
              {(() => {
                const charsWithImg = characters.filter(c => c.reference_image_url)
                if (!charsWithImg.length) return null
                return (
                  <div className="flex items-center justify-between px-3.5 py-2.5 rounded-lg" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold" style={{ color: 'var(--text)' }}>🖼️ Ảnh Tham Chiếu & Nhân Vật</span>
                      <span className="text-[11px]" style={{ color: 'var(--muted)' }}>({charsWithImg.length}/{characters.length} nhân vật có ảnh)</span>
                    </div>
                    <Button size="sm" variant="default" className="h-7 text-xs gap-1.5" onClick={handleBatchDownloadChars}>
                      ⬇ Tải tất cả ảnh tham chiếu ({charsWithImg.length})
                    </Button>
                  </div>
                )
              })()}

              <div className="grid gap-3.5" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
                {characters.map(ch => {
                  const st = charStatus(ch, requests)
                  return (
                    <Card key={ch.id} className="py-0 gap-0 overflow-hidden h-full">
                      <div className="relative flex items-center justify-center group" style={{ aspectRatio: '1/1', background: 'var(--surface)', borderBottom: '1px solid var(--border)' }}>
                        {ch.reference_image_url ? (
                          <>
                            <img src={ch.reference_image_url} alt={ch.name} className="w-full h-full object-cover" />
                            {/* Prominent download button on image */}
                            <a
                              href={getProxyDownloadUrl(ch.reference_image_url, `${ch.name}_ref.jpg`)}
                              download={`${ch.name}_ref.jpg`}
                              className="absolute bottom-2 right-2 z-10 inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-medium shadow-md backdrop-blur-md"
                              style={{ background: 'rgba(15, 23, 42, 0.85)', color: '#fff', border: '1px solid rgba(255,255,255,0.25)', textDecoration: 'none' }}
                              title="Tải ảnh tham chiếu này về máy"
                            >
                              ⬇ Tải ảnh
                            </a>
                          </>
                        ) : (
                          <span className="text-[10px] tracking-wide" style={{ color: 'var(--muted)' }}>{st === 'PROCESSING' ? t('projectDetail.character.generating') : t('projectDetail.character.noReference')}</span>
                        )}
                        <span className="absolute top-2 left-2 flex items-center gap-1.5 px-1.5 py-0.5 rounded text-[9px] tracking-wide" style={{ background: 'rgba(10,10,20,0.8)', color: STATUS_COLOR[st] }}>
                          <span className="w-1.5 h-1.5 rounded-full" style={{ background: STATUS_COLOR[st] }} />{statusLabel(t, st)}
                        </span>
                        {/* Media UUID chip */}
                        {ch.media_id && (
                          <button onClick={() => handleCopyId(ch.media_id!)}
                            style={{ position: 'absolute', top: 2, right: 6, background: 'rgba(10,10,20,0.75)', border: 'none', borderRadius: 4, padding: '1px 5px', fontSize: 9, color: copiedId === ch.media_id ? 'var(--green)' : 'var(--accent)', cursor: 'pointer', fontFamily: 'monospace' }}
                            title={ch.media_id}>
                            {copiedId === ch.media_id ? '✓' : ch.media_id.slice(0, 8)}
                          </button>
                        )}
                      </div>
                      <div className="p-3 flex flex-col gap-1.5 flex-1 justify-between">
                        <div className="flex flex-col gap-1.5">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold">{ch.name}</span>
                            <Badge variant="outline">{ch.entity_type}</Badge>
                          </div>
                          <div className="text-[11px]" style={{ color: 'var(--muted)' }}>
                            <EditableText value={ch.description ?? ''} onSave={v => patchChar(ch.id, 'description', v)} multiline className="text-[11px]" />
                          </div>
                        </div>
                        <div className="flex flex-col gap-2 pt-2">
                          {/* Direct download button for reference image */}
                          {ch.reference_image_url && (
                            <a
                              href={getProxyDownloadUrl(ch.reference_image_url, `${ch.name}_ref.jpg`)}
                              download={`${ch.name}_ref.jpg`}
                              className="inline-flex items-center justify-center gap-1.5 w-full text-[11px] h-7 rounded border font-medium transition-colors"
                              style={{ borderColor: 'var(--border)', color: 'var(--text)', background: 'var(--surface)', textDecoration: 'none' }}
                              title="Tải ảnh tham chiếu này về máy"
                            >
                              ⬇ Tải ảnh tham chiếu
                            </a>
                          )}
                          {/* Regenerate button — 3-frame template is applied automatically by the backend */}
                          <Button variant="outline" size="sm" className="w-full text-[11px] h-7"
                            disabled={st === 'PROCESSING' || regeneratingCharId === ch.id}
                            onClick={() => handleRegenerateChar(ch.id)}>
                            {st === 'PROCESSING' || regeneratingCharId === ch.id ? 'Đang tạo...' : 'Tạo lại ảnh'}
                          </Button>
                          <span className="text-[9px] tracking-wide" style={{ color: 'var(--muted)' }}>{t('projectDetail.character.updated', { date: formatDate(ch.updated_at) })}</span>
                        </div>
                      </div>
                    </Card>
                  )
                })}
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="videos" className="pt-4">
          {videos.length === 0 ? (
            <div className="text-xs" style={{ color: 'var(--muted)' }}>{t('projectDetail.noVideos')}</div>
          ) : (
            <div className="flex flex-col gap-3">
              {/* Batch download panel per video */}
              {videos.map(v => {
                const scenes = scenesByVideo[v.id] ?? []
                const imgCount = scenes.filter(s => s.vertical_image_url || s.horizontal_image_url).length
                const isDownloading = downloadingVideoId === v.id
                return imgCount > 0 ? (
                  <div key={`dl-${v.id}`} className="flex items-center gap-3 px-3 py-2 rounded-lg" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                    <span className="text-[11px] font-medium flex-1" style={{ color: 'var(--text)' }}>📥 {v.title} — {imgCount} ảnh sẵn sàng tải</span>
                    {isDownloading && downloadProgress && (
                      <span className="text-[10px]" style={{ color: 'var(--muted)' }}>{downloadProgress.done}/{downloadProgress.total}</span>
                    )}
                    <Button size="sm" variant="outline" className="h-7 text-[11px]" disabled={isDownloading} onClick={() => handleBatchDownload(v.id)}>
                      {isDownloading ? '⏳ Đang tải...' : '⬇ Tải tất cả ảnh'}
                    </Button>
                  </div>
                ) : null
              })}
            <Card className="py-4">
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('projectDetail.table.video')}</TableHead>
                      <TableHead>{t('projectDetail.table.scenes')}</TableHead>
                      <TableHead>{t('projectDetail.table.progress')}</TableHead>
                      <TableHead>{t('projectDetail.table.state')}</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {videos.map(v => {
                      const scenes = scenesByVideo[v.id] ?? []
                      const breakdown = videoStageBreakdown(scenes)
                      const stages: SceneStage[] = ['image', 'video', 'upscale']
                      const totalSlots = scenes.length * stages.length
                      const doneSlots = stages.reduce((sum, s) => sum + breakdown[s].done, 0)
                      const pct = totalSlots > 0 ? Math.round((doneSlots / totalSlots) * 100) : 0
                      const anyProcessing = requests.some(r => r.video_id === v.id && r.status === 'PROCESSING')
                      const state: 'COMPLETED' | 'RUNNING' | 'QUEUED' = pct === 100 && scenes.length > 0 ? 'COMPLETED' : anyProcessing ? 'RUNNING' : 'QUEUED'
                      return (
                        <TableRow key={v.id}>
                          <TableCell>
                            <div className="flex flex-col gap-0.5">
                              <div className="text-xs">{v.title}</div>
                              <button className="text-[9px] text-left" style={{ color: copiedId === v.id ? 'var(--green)' : 'var(--muted)', fontFamily: 'monospace', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                                onClick={() => handleCopyId(v.id)} title={v.id}>
                                {copiedId === v.id ? '✓ Copied' : v.id.slice(0, 8)}
                              </button>
                            </div>
                          </TableCell>
                          <TableCell className="text-xs" style={{ color: 'var(--muted)' }}>{scenes.length}</TableCell>
                          <TableCell>
                            <div className="flex flex-col gap-1" style={{ width: 120 }}>
                              <span className="text-[10px]" style={{ color: 'var(--muted)' }}>{pct}%</span>
                              <Progress value={pct} className="h-1" />
                            </div>
                          </TableCell>
                          <TableCell><Badge variant={state === 'COMPLETED' ? 'secondary' : state === 'RUNNING' ? 'default' : 'outline'}>{stateLabel(t, state)}</Badge></TableCell>
                          <TableCell>
                            <span
                              className="text-[10px] cursor-pointer"
                              style={{ color: 'var(--accent)' }}
                              onClick={() => { setPipelineVideoId(v.id); setTab('pipeline') }}
                            >
                              {t('projectDetail.pipelineLink')}
                            </span>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="pipeline" className="pt-4">
          {videos.length === 0 ? (
            <div className="text-xs" style={{ color: 'var(--muted)' }}>{t('projectDetail.pipeline.noVideos')}</div>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-2">
                <span className="text-[9px] tracking-widest" style={{ color: 'var(--muted)' }}>{t('projectDetail.pipeline.videoLabel')}</span>
                {videos.map(v => (
                  <Button key={v.id} variant={v.id === pipelineVideoId ? 'default' : 'outline'} size="sm" onClick={() => setPipelineVideoId(v.id)}>
                    {v.title}
                  </Button>
                ))}
              </div>
              {pipelineVideoId && <PipelineView projectId={projectId} videoId={pipelineVideoId} />}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
