import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { fetchAPI } from '../api/client'
import type { Project } from '../types'
import ProjectDetailPage from './ProjectDetailPage'
import { useTranslation } from '../i18n/useTranslation'
import type { TranslationKey } from '../i18n/translations'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardAction, CardFooter } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Button } from '../components/ui/button'
import CreateProjectModal from '../components/projects/CreateProjectModal'
import { Trash2 } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog'

type FilterTab = 'ACTIVE' | 'ARCHIVED' | 'ALL'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString()
}

function TierBadge({ tier, t }: { tier: string | null; t: (key: TranslationKey) => string }) {
  if (!tier) return null
  const isTwo = tier.includes('TWO')
  return <Badge variant={isTwo ? 'default' : 'secondary'}>{isTwo ? t('projects.tier2') : t('projects.tier1')}</Badge>
}

function ProjectCard({
  project,
  onClick,
  onDelete,
  t,
}: {
  project: Project
  onClick: () => void
  onDelete: (e: React.MouseEvent, p: Project) => void
  t: (key: TranslationKey, params?: Record<string, string | number>) => string
}) {
  return (
    <Card className="py-4 gap-3 h-full cursor-pointer transition-all hover:border-slate-700 relative group" onClick={onClick}>
      <CardHeader>
        <CardTitle className="text-sm truncate pr-2">{project.name}</CardTitle>
        {project.description && (
          <CardDescription className="text-[11px] leading-relaxed line-clamp-2">{project.description}</CardDescription>
        )}
        <CardAction className="flex items-center gap-1.5">
          <TierBadge tier={project.user_paygate_tier} t={t} />
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-slate-400 hover:text-red-400 hover:bg-red-500/15 opacity-60 group-hover:opacity-100 transition-opacity"
            title="Xóa dự án này"
            onClick={(e) => onDelete(e, project)}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-1.5">
          {project.material && <Badge variant="outline">{project.material}</Badge>}
          <Badge variant="outline">{project.status}</Badge>
        </div>
      </CardContent>
      <CardFooter>
        <span className="text-[10px] tracking-wide" style={{ color: 'var(--muted)' }}>{t('projects.footer', { date: formatDate(project.created_at), id: project.id.slice(0, 8) })}</span>
      </CardFooter>
    </Card>
  )
}

export default function ProjectsPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const [tab, setTab] = useState<FilterTab>('ACTIVE')
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [openCreate, setOpenCreate] = useState(false)
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null)
  const [deleting, setDeleting] = useState(false)

  const loadProjects = () => {
    fetchAPI<Project[]>('/api/projects')
      .then(setProjects)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadProjects()
  }, [])

  const handleDeleteProject = async () => {
    if (!projectToDelete) return
    setDeleting(true)
    try {
      await fetchAPI(`/api/projects/${projectToDelete.id}`, { method: 'DELETE' })
      setProjectToDelete(null)
      loadProjects()
    } catch (e) {
      console.error('Failed to delete project:', e)
    } finally {
      setDeleting(false)
    }
  }

  // If there's an :id param, show detail page
  if (id) {
    return <ProjectDetailPage projectId={id} onBack={() => navigate('/projects')} />
  }

  const filtered = projects.filter(p => {
    if (tab === 'ALL') return p.status !== 'DELETED'
    return p.status === tab
  })

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <Tabs value={tab} onValueChange={v => setTab(v as FilterTab)}>
          <TabsList>
            <TabsTrigger value="ACTIVE">{t('projects.tab.active')}</TabsTrigger>
            <TabsTrigger value="ARCHIVED">{t('projects.tab.archived')}</TabsTrigger>
            <TabsTrigger value="ALL">{t('projects.tab.all')}</TabsTrigger>
          </TabsList>
        </Tabs>
        <span className="ml-auto text-[11px]" style={{ color: 'var(--muted)' }}>{t('projects.count', { n: filtered.length })}</span>
        <Button size="sm" variant="default" className="h-8 gap-1.5 text-xs shadow-sm" onClick={() => setOpenCreate(true)}>
          ✨ Tạo Dự Án Mới
        </Button>
      </div>

      {loading ? (
        <div className="text-xs" style={{ color: 'var(--muted)' }}>{t('projects.loading')}</div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 rounded-lg border gap-3" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
          <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>Chưa có dự án nào</span>
          <span className="text-xs" style={{ color: 'var(--muted)' }}>Khởi tạo dự án mới từ kịch bản hoặc liên kết UUID Google Flow để bắt đầu.</span>
          <Button size="sm" variant="default" className="gap-1.5 text-xs mt-1" onClick={() => setOpenCreate(true)}>
            ✨ Tạo Dự Án Mới từ Kịch Bản
          </Button>
        </div>
      ) : (
        <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
          {filtered.map(p => (
            <ProjectCard
              key={p.id}
              project={p}
              onClick={() => navigate(`/projects/${p.id}`)}
              onDelete={(e) => {
                e.stopPropagation()
                setProjectToDelete(p)
              }}
              t={t}
            />
          ))}
        </div>
      )}

      <CreateProjectModal
        open={openCreate}
        onOpenChange={setOpenCreate}
        onCreated={() => loadProjects()}
      />

      {/* Delete Confirmation Modal */}
      <Dialog open={!!projectToDelete} onOpenChange={(open) => !open && setProjectToDelete(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-400">
              <Trash2 className="w-5 h-5 text-red-500" />
              <span>Xóa dự án?</span>
            </DialogTitle>
            <DialogDescription className="text-xs pt-2 leading-relaxed" style={{ color: 'var(--muted)' }}>
              Bạn có chắc chắn muốn xóa dự án <strong>"{projectToDelete?.name}"</strong>?
              <br />
              Tất cả các phân cảnh, nhân vật, bối cảnh và video liên quan sẽ bị xóa khỏi hệ thống. Thao tác này không thể hoàn tác.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0 pt-3">
            <Button variant="ghost" size="sm" onClick={() => setProjectToDelete(null)} disabled={deleting}>
              Hủy
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={handleDeleteProject}
              disabled={deleting}
              className="bg-red-600 hover:bg-red-500 text-white"
            >
              {deleting ? 'Đang xóa...' : 'Xác nhận xóa'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
