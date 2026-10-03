import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Zap, Video, ChevronDown, Check, Settings, Sparkles } from 'lucide-react'
import { useModelsContext } from '../../hooks/useModelsContext'
import { useTranslation } from '../../i18n/useTranslation'

interface ModelPreset {
  id: string
  family: 'omni_flash' | 'veo'
  veoModel?: string
  label: string
  shortLabel: string
  badge: string
  cost: string
  description: string
}

export default function ModelSwitcher() {
  const { t } = useTranslation()
  const { models, updateModels, loading } = useModelsContext()
  const [open, setOpen] = useState(false)
  const [switching, setSwitching] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const currentFamily = models?.default_video_model_family ?? 'omni_flash'
  const currentVeoModel = models?.default_veo_model ?? 'veo_3_1_i2v_lite_low_priority'

  const presets: ModelPreset[] = [
    {
      id: 'omni_flash',
      family: 'omni_flash',
      label: 'Omni Flash',
      shortLabel: 'Omni Flash',
      badge: 'Mặc định',
      cost: '7-15 cr',
      description: 'Tiết kiệm, hỗ trợ nối cảnh First+Last frame, 4s: 7cr, 6s: 10cr, 8s: 12cr, 10s: 15cr',
    },
    {
      id: 'veo_lite',
      family: 'veo',
      veoModel: 'veo_3_1_i2v_lite',
      label: 'Veo 3.1 Lite',
      shortLabel: 'Veo 3.1 Lite',
      badge: '10 cr',
      cost: '10 cr',
      description: 'Tốc độ render nhanh, 10 credits / 8s',
    },
    {
      id: 'veo_fast',
      family: 'veo',
      veoModel: 'veo_3_1_i2v_s_fast_ultra',
      label: 'Veo 3.1 Fast',
      shortLabel: 'Veo 3.1 Fast',
      badge: '20 cr',
      cost: '20 cr',
      description: 'Tốc độ cao, chi tiết tốt, 20 credits / 8s',
    },
    {
      id: 'veo_quality',
      family: 'veo',
      veoModel: 'veo_3_1_i2v_quality',
      label: 'Veo 3.1 Quality',
      shortLabel: 'Veo 3.1 Quality',
      badge: '100 cr',
      cost: '100 cr',
      description: 'Chất lượng cao cấp nhất, 100 credits / 8s',
    },
    {
      id: 'veo_lite_low_priority',
      family: 'veo',
      veoModel: 'veo_3_1_i2v_lite_low_priority',
      label: 'Veo 3.1 Lite Low Priority',
      shortLabel: 'Veo 3.1 (0 cr)',
      badge: '0 Credits',
      cost: 'Miễn phí',
      description: 'Hàng đợi thường, không tốn credit, hỗ trợ mọi tài khoản',
    },
  ]

  const activePreset = presets.find(p => {
    if (currentFamily === 'omni_flash') return p.family === 'omni_flash'
    return p.family === 'veo' && p.veoModel === currentVeoModel
  }) ?? {
    id: 'veo_custom',
    family: 'veo' as const,
    veoModel: currentVeoModel,
    label: `Veo 3.1: ${currentVeoModel}`,
    shortLabel: 'Veo 3.1 (Tùy chỉnh)',
    badge: 'Veo 3',
    cost: 'Veo',
    description: currentVeoModel,
  }

  async function handleSelect(preset: ModelPreset) {
    if (switching) return
    setSwitching(true)
    if (preset.family === 'omni_flash') {
      await updateModels({ default_video_model_family: 'omni_flash' })
    } else if (preset.veoModel) {
      await updateModels({
        default_video_model_family: 'veo',
        default_veo_model: preset.veoModel,
      })
    }
    setSwitching(false)
    setOpen(false)
  }

  const isOmni = currentFamily === 'omni_flash'

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(prev => !prev)}
        disabled={loading || switching}
        className="flex items-center gap-2 px-2.5 py-1 rounded border text-xs font-medium transition-all duration-150 cursor-pointer hover:border-[var(--accent)]"
        style={{
          background: isOmni ? 'rgba(234, 179, 8, 0.08)' : 'rgba(139, 92, 246, 0.08)',
          borderColor: isOmni ? 'rgba(234, 179, 8, 0.35)' : 'rgba(139, 92, 246, 0.35)',
          color: 'var(--text)',
        }}
        title={t('header.quickModel')}
      >
        {isOmni ? (
          <Zap className="w-3.5 h-3.5 text-amber-400" />
        ) : (
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
        )}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] tracking-wide text-[var(--muted)] font-normal hidden sm:inline">
            {t('header.quickModel')}:
          </span>
          <span className="text-[11px] font-semibold">
            {activePreset.shortLabel}
          </span>
          <span
            className="text-[9px] px-1 py-0.2 rounded font-semibold tracking-wider uppercase ml-0.5"
            style={{
              background: isOmni ? 'rgba(234, 179, 8, 0.2)' : 'rgba(139, 92, 246, 0.2)',
              color: isOmni ? 'rgb(245, 158, 11)' : 'rgb(168, 85, 247)',
            }}
          >
            {activePreset.badge}
          </span>
        </div>
        <ChevronDown className={`w-3 h-3 text-[var(--muted)] transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-1.5 w-76 rounded-lg p-2 shadow-2xl z-50 flex flex-col gap-1 border animate-in fade-in zoom-in-95 duration-100"
          style={{
            background: 'var(--card)',
            borderColor: 'var(--border)',
            backdropFilter: 'blur(12px)',
          }}
        >
          <div className="px-2.5 py-1.5 flex items-center justify-between border-b pb-2" style={{ borderColor: 'var(--border)' }}>
            <span className="text-[10px] font-semibold tracking-widest uppercase" style={{ color: 'var(--muted)' }}>
              {t('models.family')}
            </span>
            <span className="text-[9px] text-[var(--muted)]">
              {currentFamily === 'omni_flash' ? 'Omni Flash' : 'Veo 3.1'}
            </span>
          </div>

          <div className="flex flex-col gap-1 pt-1">
            {presets.map(preset => {
              const isSelected = preset.family === 'omni_flash'
                ? currentFamily === 'omni_flash'
                : currentFamily === 'veo' && currentVeoModel === preset.veoModel

              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => handleSelect(preset)}
                  className="flex items-start gap-2.5 p-2 rounded text-left transition-colors cursor-pointer group"
                  style={{
                    background: isSelected ? 'var(--surface)' : 'transparent',
                    border: isSelected ? '1px solid var(--accent)' : '1px solid transparent',
                  }}
                >
                  <div className="mt-0.5 flex-shrink-0">
                    {preset.family === 'omni_flash' ? (
                      <Zap className={`w-3.5 h-3.5 ${isSelected ? 'text-amber-400' : 'text-[var(--muted)] group-hover:text-amber-400'}`} />
                    ) : (
                      <Video className={`w-3.5 h-3.5 ${isSelected ? 'text-purple-400' : 'text-[var(--muted)] group-hover:text-purple-400'}`} />
                    )}
                  </div>
                  <div className="flex-1 flex flex-col gap-0.5 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className={`text-[11px] font-semibold truncate ${isSelected ? 'text-[var(--accent)]' : 'text-[var(--text)]'}`}>
                        {preset.label}
                      </span>
                      <span
                        className="text-[9px] px-1 py-0.2 rounded font-medium flex-shrink-0"
                        style={{
                          background: preset.family === 'omni_flash' ? 'rgba(234, 179, 8, 0.15)' : 'rgba(139, 92, 246, 0.15)',
                          color: preset.family === 'omni_flash' ? 'rgb(245, 158, 11)' : 'rgb(168, 85, 247)',
                        }}
                      >
                        {preset.cost}
                      </span>
                    </div>
                    <span className="text-[10px] leading-tight text-[var(--muted)] line-clamp-1">
                      {preset.description}
                    </span>
                  </div>
                  {isSelected && (
                    <Check className="w-3.5 h-3.5 text-[var(--accent)] flex-shrink-0 mt-0.5" />
                  )}
                </button>
              )
            })}
          </div>

          <div className="mt-1 pt-1.5 border-t flex items-center justify-between px-1" style={{ borderColor: 'var(--border)' }}>
            <span className="text-[9px] text-[var(--muted)]">
              Mặc định: <strong className="text-[var(--text)] font-medium">Omni Flash</strong>
            </span>
            <Link
              to="/settings"
              onClick={() => setOpen(false)}
              className="flex items-center gap-1 text-[10px] hover:underline"
              style={{ color: 'var(--accent)' }}
            >
              <Settings className="w-3 h-3" />
              <span>Cài đặt chi tiết</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
