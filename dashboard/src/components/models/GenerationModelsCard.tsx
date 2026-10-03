import { useState, useEffect } from 'react'
import { Zap, Video, Sparkles, Check, RefreshCw, Sliders, Info } from 'lucide-react'
import { useModelsContext } from '../../hooks/useModelsContext'
import { useTranslation } from '../../i18n/useTranslation'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardAction } from '../ui/card'
import { Button } from '../ui/button'

const CONTROL_CLASS = 'text-xs px-2.5 py-1.5 rounded outline-none w-full'
const CONTROL_STYLE = { background: 'var(--card)', color: 'var(--text)', border: '1px solid var(--border)' }

interface ModelOption {
  id: string
  family: 'omni_flash' | 'veo'
  veoKey?: string
  label: string
  badge: string
  badgeColor: string
  badgeBg: string
  recommended?: boolean
  cost: string
  duration: string
  chaining: string
  desc: string
}

const MODEL_OPTIONS: ModelOption[] = [
  {
    id: 'omni_flash',
    family: 'omni_flash',
    label: 'Omni Flash',
    badge: 'Mặc định · 7-15 cr',
    badgeColor: 'rgb(245, 158, 11)',
    badgeBg: 'rgba(234, 179, 8, 0.15)',
    recommended: true,
    cost: '7 - 15 cr',
    duration: '4s - 10s',
    chaining: 'Nối cảnh First+Last',
    desc: 'Model thế hệ mới nhất của Google Flow. Tốc độ cao, tuỳ chọn độ dài (4s: 7cr, 6s: 10cr, 8s: 12cr, 10s: 15cr) và nối cảnh mượt mà.',
  },
  {
    id: 'veo_3_1_i2v_lite',
    family: 'veo',
    veoKey: 'veo_3_1_i2v_lite',
    label: 'Veo 3.1 Lite',
    badge: '10 credits · Nhanh',
    badgeColor: 'rgb(59, 130, 246)',
    badgeBg: 'rgba(59, 130, 246, 0.15)',
    recommended: false,
    cost: '10 credits',
    duration: '8s cố định',
    chaining: 'Veo Chaining',
    desc: 'Tốc độ render nhanh trong dòng Veo 3, chi phí 10 credits cho mỗi video 8 giây, chất lượng tiêu chuẩn.',
  },
  {
    id: 'veo_3_1_i2v_s_fast_ultra',
    family: 'veo',
    veoKey: 'veo_3_1_i2v_s_fast_ultra',
    label: 'Veo 3.1 Fast',
    badge: '20 credits · Tốc độ cao',
    badgeColor: 'rgb(168, 85, 247)',
    badgeBg: 'rgba(139, 92, 246, 0.15)',
    recommended: false,
    cost: '20 credits',
    duration: '8s cố định',
    chaining: 'Veo Chaining',
    desc: 'Tốc độ tạo nhanh với độ chi tiết cao, chi phí 20 credits cho mỗi video 8 giây.',
  },
  {
    id: 'veo_3_1_i2v_quality',
    family: 'veo',
    veoKey: 'veo_3_1_i2v_quality',
    label: 'Veo 3.1 Quality',
    badge: '100 credits · Cực cao',
    badgeColor: 'rgb(236, 72, 153)',
    badgeBg: 'rgba(236, 72, 153, 0.15)',
    recommended: false,
    cost: '100 credits',
    duration: '8s cố định',
    chaining: 'Veo Chaining',
    desc: 'Chất lượng hình ảnh và chuyển động cao cấp nhất của Veo 3.1, chi phí 100 credits cho mỗi video 8 giây.',
  },
  {
    id: 'veo_3_1_i2v_lite_low_priority',
    family: 'veo',
    veoKey: 'veo_3_1_i2v_lite_low_priority',
    label: 'Veo 3.1 Lite Low Priority',
    badge: '0 Credits · Miễn phí',
    badgeColor: 'rgb(34, 197, 94)',
    badgeBg: 'rgba(34, 197, 94, 0.15)',
    recommended: false,
    cost: '0 credits (Free)',
    duration: '8s cố định',
    chaining: 'Veo Chaining',
    desc: 'Hàng đợi thường, 0 credits, chạy an toàn trên mọi loại tài khoản (kể cả ADVANCED). Tiết kiệm chi phí tối đa cho dự án dài.',
  },
]

export default function GenerationModelsCard() {
  const { t } = useTranslation()
  const { models, updateModels, loading, refreshModels } = useModelsContext()

  const [family, setFamily] = useState<'omni_flash' | 'veo'>('omni_flash')
  const [veoModel, setVeoModel] = useState<string>('veo_3_1_i2v_lite_low_priority')
  const [isCustomVeo, setIsCustomVeo] = useState(false)
  const [customVeoKey, setCustomVeoKey] = useState('')
  const [omniDuration, setOmniDuration] = useState<number>(6)
  const [omniResolution, setOmniResolution] = useState<'360p' | '720p'>('720p')
  const [imageModel, setImageModel] = useState<string>('NANO_BANANA_PRO')

  const [saving, setSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<{ ok: boolean; text: string } | null>(null)

  // Initialize draft when models are loaded
  useEffect(() => {
    if (!models) return
    const fam = models.default_video_model_family ?? 'omni_flash'
    const vm = models.default_veo_model ?? models.batch_video_models?.default ?? 'veo_3_1_i2v_lite_low_priority'
    setFamily(fam)
    const isKnown = MODEL_OPTIONS.some(p => p.family === 'veo' && p.veoKey === vm)
    if (isKnown) {
      setVeoModel(vm)
      setIsCustomVeo(false)
    } else {
      setIsCustomVeo(true)
      setCustomVeoKey(vm)
      setVeoModel(vm)
    }
    setOmniDuration(models.default_omni_duration ?? 6)
    setOmniResolution(models.default_omni_resolution ?? '720p')
    setImageModel(models.default_image_model ?? 'NANO_BANANA_PRO')
  }, [models])

  const effectiveVeoModel = isCustomVeo ? customVeoKey.trim() : veoModel

  const isDirty = models !== null && (
    family !== models.default_video_model_family ||
    effectiveVeoModel !== (models.default_veo_model ?? models.batch_video_models?.default ?? 'veo_3_1_i2v_lite_low_priority') ||
    omniDuration !== (models.default_omni_duration ?? 6) ||
    omniResolution !== (models.default_omni_resolution ?? '720p') ||
    imageModel !== (models.default_image_model ?? 'NANO_BANANA_PRO')
  )

  function handleSelectOption(opt: ModelOption) {
    setSaveStatus(null)
    if (opt.family === 'omni_flash') {
      setFamily('omni_flash')
      setIsCustomVeo(false)
    } else {
      setFamily('veo')
      if (opt.veoKey) setVeoModel(opt.veoKey)
      setIsCustomVeo(false)
    }
  }

  async function handleSave() {
    setSaving(true)
    setSaveStatus(null)
    try {
      const ok = await updateModels({
        default_video_model_family: family,
        default_veo_model: effectiveVeoModel,
        default_omni_duration: omniDuration,
        default_omni_resolution: omniResolution,
        default_image_model: imageModel,
      })
      if (ok) {
        setSaveStatus({ ok: true, text: t('models.saved') })
      } else {
        setSaveStatus({ ok: false, text: t('models.saveFailed') })
      }
    } catch (e) {
      setSaveStatus({ ok: false, text: e instanceof Error ? e.message : 'Error' })
    } finally {
      setSaving(false)
    }
  }

  if (loading && !models) {
    return (
      <Card className="py-4">
        <CardContent>
          <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted)' }}>
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span>Đang tải thông tin model...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  const activeLabel = family === 'omni_flash'
    ? 'Omni Flash (Mặc định)'
    : isCustomVeo
      ? `Veo 3: ${effectiveVeoModel || 'Tùy chỉnh'}`
      : (MODEL_OPTIONS.find(o => o.family === 'veo' && o.veoKey === veoModel)?.label ?? veoModel)

  return (
    <Card className="py-4">
      <CardHeader>
        <CardTitle className="text-xs tracking-widest uppercase flex items-center gap-2">
          <span>{t('models.title')}</span>
          <span
            className="text-[9px] font-semibold px-2 py-0.5 rounded tracking-normal normal-case flex items-center gap-1"
            style={{
              background: family === 'omni_flash' ? 'rgba(234, 179, 8, 0.15)' : 'rgba(139, 92, 246, 0.15)',
              color: family === 'omni_flash' ? 'rgb(245, 158, 11)' : 'rgb(168, 85, 247)',
            }}
          >
            {family === 'omni_flash' ? <Zap className="w-3 h-3 text-amber-400" /> : <Sparkles className="w-3 h-3 text-purple-400" />}
            <span>Đang chọn: {activeLabel}</span>
          </span>
        </CardTitle>
        <CardDescription className="text-[11px]">
          Chọn mô hình bạn muốn dùng để tạo video (Omni Flash mặc định hoặc chọn một trong các model Veo 3 phù hợp).
        </CardDescription>
        <CardAction>
          <span className="text-[9px] tracking-widest" style={{ color: isDirty ? 'var(--yellow)' : 'var(--muted)' }}>
            {isDirty ? t('settings.unsaved') : t('settings.inSync')}
          </span>
        </CardAction>
      </CardHeader>

      <CardContent>
        <div className="flex flex-col gap-4">
          {/* Unified Video Model Selector List */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-semibold tracking-widest uppercase" style={{ color: 'var(--muted)' }}>
                MÔ HÌNH TẠO VIDEO (CHỌN 1 TRONG CÁC MODEL DƯỚI ĐÂY)
              </span>
              <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
                Nhấn trực tiếp để đổi model đang dùng
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {MODEL_OPTIONS.map(opt => {
                const isSelected = opt.family === 'omni_flash'
                  ? family === 'omni_flash'
                  : family === 'veo' && !isCustomVeo && veoModel === opt.veoKey

                const isOmni = opt.family === 'omni_flash'

                return (
                  <div
                    key={opt.id}
                    onClick={() => handleSelectOption(opt)}
                    className={`relative flex flex-col justify-between p-3 rounded-lg border cursor-pointer transition-all duration-150 ${
                      isSelected
                        ? isOmni ? 'ring-2 ring-amber-400/70 border-amber-400' : 'ring-2 ring-purple-400/70 border-purple-400'
                        : 'hover:border-[var(--muted)]'
                    }`}
                    style={{
                      background: isSelected ? 'var(--surface)' : 'var(--card)',
                      boxShadow: isSelected
                        ? (isOmni ? '0 0 14px rgba(234, 179, 8, 0.15)' : '0 0 14px rgba(139, 92, 246, 0.15)')
                        : 'none',
                    }}
                  >
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center justify-between gap-1">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-5 h-5 rounded flex items-center justify-center flex-shrink-0"
                            style={{ background: opt.badgeBg, color: opt.badgeColor }}
                          >
                            {isOmni ? <Zap className="w-3.5 h-3.5" /> : <Video className="w-3.5 h-3.5" />}
                          </div>
                          <span className="text-xs font-semibold" style={{ color: isSelected ? 'var(--text)' : 'var(--text)' }}>
                            {opt.label}
                          </span>
                        </div>
                        {isSelected && (
                          <div className="flex items-center gap-1">
                            <span
                              className="text-[9px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wider"
                              style={{ background: opt.badgeBg, color: opt.badgeColor }}
                            >
                              ĐANG CHỌN
                            </span>
                            <Check className="w-3.5 h-3.5" style={{ color: opt.badgeColor }} />
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span
                          className="text-[9px] font-medium px-1.5 py-0.5 rounded"
                          style={{ background: opt.badgeBg, color: opt.badgeColor }}
                        >
                          {opt.badge}
                        </span>
                        {opt.recommended && (
                          <span className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">
                            Khuyên dùng
                          </span>
                        )}
                      </div>

                      <p className="text-[11px] leading-relaxed mt-0.5" style={{ color: 'var(--muted)' }}>
                        {opt.desc}
                      </p>
                    </div>

                    <div className="flex items-center gap-1.5 mt-2.5 pt-2 border-t text-[10px]" style={{ borderColor: 'var(--border)', color: 'var(--muted)' }}>
                      <span className="px-1.5 py-0.5 rounded" style={{ background: 'var(--bg)', border: '1px solid var(--border)' }}>
                        {opt.cost}
                      </span>
                      <span className="px-1.5 py-0.5 rounded" style={{ background: 'var(--bg)', border: '1px solid var(--border)' }}>
                        {opt.duration}
                      </span>
                      <span className="px-1.5 py-0.5 rounded truncate" style={{ background: 'var(--bg)', border: '1px solid var(--border)' }}>
                        {opt.chaining}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Custom Veo Key Option */}
            <div className="flex items-center gap-2 mt-1 px-1">
              <input
                type="checkbox"
                id="customVeoCheck"
                checked={isCustomVeo}
                onChange={e => {
                  const checked = e.target.checked
                  setIsCustomVeo(checked)
                  if (checked) {
                    setFamily('veo')
                  }
                  setSaveStatus(null)
                }}
                className="cursor-pointer"
              />
              <label htmlFor="customVeoCheck" className="text-xs cursor-pointer select-none" style={{ color: 'var(--text)' }}>
                Tùy chỉnh mã model Veo khác…
              </label>
              {isCustomVeo && (
                <input
                  type="text"
                  value={customVeoKey}
                  onChange={e => {
                    setCustomVeoKey(e.target.value)
                    setFamily('veo')
                    setSaveStatus(null)
                  }}
                  placeholder="Nhập mã model Veo (ví dụ: veo_3_1_i2v_s_fast_ultra)"
                  className={CONTROL_CLASS}
                  style={{ ...CONTROL_STYLE, maxWidth: '320px' }}
                />
              )}
            </div>
          </div>

          {/* Conditional Sub-settings based on chosen model */}
          {family === 'omni_flash' ? (
            <div
              className="flex flex-col gap-2 p-3 rounded-lg border"
              style={{
                background: 'rgba(234, 179, 8, 0.04)',
                borderColor: 'rgba(234, 179, 8, 0.3)',
              }}
            >
              <div className="flex items-center gap-2">
                <Sliders className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-[10px] font-semibold tracking-widest uppercase text-amber-400">
                  THÔNG SỐ CẤU HÌNH OMNI FLASH
                </span>
                <span className="text-[10px] text-[var(--muted)]">
                  (Áp dụng khi sinh video bằng Omni Flash)
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1">
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] font-medium" style={{ color: 'var(--text)' }}>
                    Thời lượng cảnh mặc định:
                  </span>
                  <select
                    value={omniDuration}
                    onChange={e => { setOmniDuration(Number(e.target.value)); setSaveStatus(null) }}
                    className={CONTROL_CLASS}
                    style={CONTROL_STYLE}
                  >
                    <option value={4}>4 giây · 7 credits (Tiết kiệm nhất)</option>
                    <option value={6}>6 giây · 10 credits (Cân bằng · Mặc định)</option>
                    <option value={8}>8 giây · 12 credits (Chuẩn 8s)</option>
                    <option value={10}>10 giây · 15 credits (Cảnh dài)</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <span className="text-[10px] font-medium" style={{ color: 'var(--text)' }}>
                    Độ phân giải render:
                  </span>
                  <select
                    value={omniResolution}
                    onChange={e => { setOmniResolution(e.target.value as '360p' | '720p'); setSaveStatus(null) }}
                    className={CONTROL_CLASS}
                    style={CONTROL_STYLE}
                  >
                    <option value="720p">720p HD (Chất lượng chuẩn)</option>
                    <option value="360p">360p (Render siêu tốc, ít chi tiết hơn)</option>
                  </select>
                </div>
              </div>
            </div>
          ) : (
            <div
              className="flex items-start gap-2.5 p-3 rounded-lg border text-xs"
              style={{
                background: 'rgba(139, 92, 246, 0.04)',
                borderColor: 'rgba(139, 92, 246, 0.3)',
              }}
            >
              <Info className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
              <div className="flex flex-col gap-0.5">
                <span className="font-semibold text-purple-300">
                  Đang kích hoạt Google Veo 3: {effectiveVeoModel}
                </span>
                <span className="text-[11px] text-[var(--muted)] leading-relaxed">
                  Video tạo bởi Veo 3 có thời lượng cố định là <strong>8 giây</strong>. Hệ thống sẽ tự động cấu trúc prompt thành các đoạn sub-clip (0-3s, 3-6s, 6-8s) và nhúng lời thoại nhân vật phù hợp.
                </span>
              </div>
            </div>
          )}

          {/* Section: Image Model Selection */}
          <div className="flex flex-col gap-2 pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
            <span className="text-[9px] font-semibold tracking-widest uppercase" style={{ color: 'var(--muted)' }}>
              MÔ HÌNH TẠO ẢNH MẶC ĐỊNH (KEYFRAME & THAM CHIẾU NHÂN VẬT)
            </span>
            <div className="max-w-md">
              <select
                value={imageModel}
                onChange={e => { setImageModel(e.target.value); setSaveStatus(null) }}
                className={CONTROL_CLASS}
                style={CONTROL_STYLE}
              >
                <option value="NANO_BANANA_PRO">GEM_PIX_2 (Nano Banana Pro · Mặc định · Độ nét cao)</option>
                <option value="NANO_BANANA_2">NARWHAL (Nano Banana 2 · Cân bằng)</option>
                <option value="NANO_BANANA_2_LITE">HARBOR_SEAL (Nano Banana 2 Lite · Nhanh)</option>
              </select>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 pt-2">
            <Button size="sm" disabled={!isDirty || saving} onClick={handleSave}>
              {saving ? t('models.saving') : t('models.save')}
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={saving}
              onClick={() => { refreshModels(); setSaveStatus(null) }}
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Làm mới
            </Button>
            {saveStatus && (
              <span className="text-[11px]" style={{ color: saveStatus.ok ? 'var(--green)' : 'var(--red)' }}>
                {saveStatus.text}
              </span>
            )}
            {!isDirty && !saveStatus && (
              <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
                {family === 'omni_flash'
                  ? 'Đang cấu hình mặc định là Omni Flash'
                  : `Đang cấu hình Veo 3 (${effectiveVeoModel})`}
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

