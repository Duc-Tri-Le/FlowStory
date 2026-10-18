import { useState } from 'react'
import { Type, Sparkles, Check, Sliders, Eye, EyeOff } from 'lucide-react'

export interface TextOverlayConfig {
  enabled: boolean
  fontFamily: 'sans' | 'impact' | 'serif' | 'comic' | 'mono'
  fontSize: number // in px (14 - 48)
  textColor: string // Hex code
  position: 'bottom' | 'center' | 'top'
  uppercase: boolean
  wordsPerBatch: number // 0 = Toàn bộ câu (tất cả từ), 1 = 1 từ/lần, 2, 3, 4, 6...
  backgroundType?: 'none' | 'solid_dark' | 'glass' // Mặc định luôn là 'none'
  enableHighlight?: boolean // Mặc định luôn là false
  highlightColor?: string
}

export const DEFAULT_TEXT_CONFIG: TextOverlayConfig = {
  enabled: false, // Default is clean video until user explicitly chooses to enable
  fontFamily: 'sans',
  fontSize: 24,
  textColor: '#ffffff',
  position: 'bottom',
  uppercase: false,
  wordsPerBatch: 3, // 3 từ / lần là chuẩn mực tối ưu cho video ngắn / storytime
  backgroundType: 'none', // Mặc định không có background
  enableHighlight: false, // Mặc định không highlight
}

interface Props {
  config: TextOverlayConfig
  onChange: (newConfig: TextOverlayConfig) => void
  videoReady?: boolean
}

const PRESETS = [
  {
    name: 'TikTok Viral (Hot)',
    desc: 'Impact đậm, 2 từ/lần, chữ trắng nổi bật',
    config: {
      enabled: true,
      fontFamily: 'impact' as const,
      fontSize: 32,
      textColor: '#ffffff',
      position: 'center' as const,
      uppercase: true,
      wordsPerBatch: 2,
      backgroundType: 'none' as const,
      enableHighlight: false,
    },
  },
  {
    name: 'Hormozi 1 Từ/Lần',
    desc: '1 từ duy nhất, chữ vàng neon đập vào mắt',
    config: {
      enabled: true,
      fontFamily: 'impact' as const,
      fontSize: 36,
      textColor: '#facc15',
      position: 'center' as const,
      uppercase: true,
      wordsPerBatch: 1,
      backgroundType: 'none' as const,
      enableHighlight: false,
    },
  },
  {
    name: 'Noir Trinh Thám',
    desc: 'Serif điện ảnh, 4 từ/lần, chữ vàng kim cổ điển',
    config: {
      enabled: true,
      fontFamily: 'serif' as const,
      fontSize: 24,
      textColor: '#fef08a',
      position: 'bottom' as const,
      uppercase: false,
      wordsPerBatch: 4,
      backgroundType: 'none' as const,
      enableHighlight: false,
    },
  },
  {
    name: 'Phụ Đề Truyền Thống',
    desc: 'Sans thanh lịch, hiện cả câu, chữ trắng tinh',
    config: {
      enabled: true,
      fontFamily: 'sans' as const,
      fontSize: 22,
      textColor: '#ffffff',
      position: 'bottom' as const,
      uppercase: false,
      wordsPerBatch: 0,
      backgroundType: 'none' as const,
      enableHighlight: false,
    },
  },
]

// Single Clean Color Palette for Text
const TEXT_COLORS = [
  { label: 'Trắng Tinh', color: '#ffffff' },
  { label: 'Vàng Neon', color: '#facc15' },
  { label: 'Vàng Kem', color: '#fef08a' },
  { label: 'Xanh Cyan', color: '#06b6d4' },
  { label: 'Hồng Neon', color: '#ec4899' },
  { label: 'Xanh Mint', color: '#a7f3d0' },
  { label: 'Cam Rực', color: '#f97316' },
  { label: 'Xám Bạc', color: '#cbd5e1' },
]

export default function TextOverlayCustomizer({ config, onChange, videoReady = true }: Props) {
  const [activeTab, setActiveTab] = useState<'presets' | 'custom'>('presets')

  const update = (patch: Partial<TextOverlayConfig>) => {
    onChange({ ...config, ...patch, backgroundType: 'none', enableHighlight: false })
  }

  // If video is not ready yet, display an informative standby card
  if (!videoReady) {
    return (
      <div className="bg-slate-900/60 rounded-2xl p-5 border border-dashed border-slate-800 text-center flex flex-col items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-slate-800 text-slate-500 flex items-center justify-center text-xs font-mono">
          ⏳
        </div>
        <p className="text-xs font-semibold text-slate-400">
          Bước Hậu Kỳ Sau Cùng: Thêm Text / Phụ Đề
        </p>
        <p className="text-[11px] text-slate-500 max-w-sm">
          Tùy chọn thêm text vào màn hình sẽ tự động xuất hiện sau khi video hoàn tất xử lý.
        </p>
      </div>
    )
  }

  // Helper text snippet for preview box depending on wordsPerBatch
  const renderPreviewWords = () => {
    const k = config.wordsPerBatch ?? 3

    if (k === 1) {
      return (
        <span
          className="inline-block font-black tracking-wider"
          style={{
            color: config.textColor,
            textShadow: '0 2px 4px #000, 0 0 10px #000, 0 0 20px rgba(0,0,0,0.95)',
          }}
        >
          {config.uppercase ? 'VỤ ÁN MẠNG' : 'vụ án mạng'}
        </span>
      )
    }

    if (k === 2) {
      return (
        <span style={{ color: config.textColor }}>
          {config.uppercase ? 'VỤ ÁN BÍ ẨN' : 'vụ án bí ẩn'}
        </span>
      )
    }

    if (k === 3) {
      return (
        <span style={{ color: config.textColor }}>
          {config.uppercase ? 'ĐÊM HÔM ĐÓ, BÍ ẨN...' : 'Đêm hôm đó, bí ẩn...'}
        </span>
      )
    }

    if (k === 4) {
      return (
        <span style={{ color: config.textColor }}>
          {config.uppercase ? 'ĐÊM HÔM ĐÓ, VỤ ÁN XẢY RA...' : 'Đêm hôm đó, vụ án xảy ra...'}
        </span>
      )
    }

    // 5+ or All words (k === 0)
    return (
      <span style={{ color: config.textColor }}>
        Đêm hôm đó, vụ án mạng đã xảy ra tại căn phòng số bảy...
      </span>
    )
  }

  return (
    <div className="bg-slate-900/95 rounded-2xl p-5 border border-slate-800 shadow-xl flex flex-col gap-4">
      {/* 1. Header: Post-production Notice & Choice */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
            <Type className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white">
                Bước Hoàn Thiện Cuối: Thêm Text Màn Hình
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Hậu kỳ
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Lựa chọn thêm hoặc không thêm text vào màn hình sau khi video đã tạo xong
            </p>
          </div>
        </div>

        {/* Master Choice Buttons (Có thêm text vs Không thêm text) */}
        <div className="flex items-center p-1 bg-slate-950 rounded-xl border border-slate-800 shrink-0">
          <button
            onClick={() => update({ enabled: false })}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              !config.enabled
                ? 'bg-slate-800 text-slate-200 shadow-sm border border-slate-700'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <EyeOff className="w-3.5 h-3.5" />
            <span>Không Text (Sạch)</span>
          </button>

          <button
            onClick={() => update({ enabled: true })}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              config.enabled
                ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 font-bold shadow-md shadow-amber-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Có, Chèn Text</span>
          </button>
        </div>
      </div>

      {/* 2. When Disabled: Clean State Notice */}
      {!config.enabled && (
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2.5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Video đang ở chế độ <strong>màn hình sạch</strong> (không có chữ phụ đề đè lên hoạt hình).</span>
          </div>
          <button
            onClick={() => update({ enabled: true })}
            className="text-amber-400 hover:underline text-xs font-semibold shrink-0"
          >
            + Bật chèn Text ngay
          </button>
        </div>
      )}

      {/* 3. When Enabled: Full Customization Controls */}
      {config.enabled && (
        <div className="flex flex-col gap-4">
          {/* Real-time Subtitle Live Preview Box */}
          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Sparkles className="w-3 h-3 text-amber-400" />
                Khung Nhìn Thử Kiểu Chữ (Live Preview):
              </span>
              <span className="font-mono text-amber-400 text-[10px]">
                {config.fontFamily.toUpperCase()} • {config.fontSize}px • {config.wordsPerBatch === 0 ? 'CẢ CÂU' : `${config.wordsPerBatch} TỪ/LẦN`} • KHÔNG NỀN
              </span>
            </div>

            <div className="min-h-[58px] rounded-lg bg-black/60 flex items-center justify-center p-3 text-center overflow-hidden">
              <div className="px-3 py-1 transition-all max-w-full">
                <div
                  className={`font-bold tracking-wide leading-tight ${config.uppercase ? 'uppercase' : ''}`}
                  style={{
                    fontSize: `${Math.min(config.fontSize, 28)}px`,
                    fontFamily:
                      config.fontFamily === 'impact'
                        ? "'Impact', 'Arial Black', sans-serif"
                        : config.fontFamily === 'serif'
                        ? "'Georgia', 'Times New Roman', serif"
                        : config.fontFamily === 'comic'
                        ? "'Comic Sans MS', cursive, sans-serif"
                        : config.fontFamily === 'mono'
                        ? "'Courier New', monospace"
                        : "'Geist', system-ui, sans-serif",
                    color: config.textColor,
                    textShadow: '0 2px 4px #000, 0 0 10px #000, 0 0 20px rgba(0,0,0,0.95)',
                  }}
                >
                  {renderPreviewWords()}
                </div>
              </div>
            </div>
          </div>

          {/* Sub-tabs: Gợi Ý Phong Cách vs Tùy Chỉnh Chi Tiết */}
          <div className="flex items-center gap-2 p-1 bg-slate-950 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('presets')}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === 'presets'
                  ? 'bg-slate-800 text-amber-400 shadow-sm border border-slate-700'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Gợi Ý Phong Cách Nhanh</span>
            </button>
            <button
              onClick={() => setActiveTab('custom')}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === 'custom'
                  ? 'bg-slate-800 text-amber-400 shadow-sm border border-slate-700'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Tùy Chỉnh Chi Tiết (Style, Cỡ, Màu, Số Từ, Vị Trí)</span>
            </button>
          </div>

          {/* TAB 1: 1-Click Presets */}
          {activeTab === 'presets' && (
            <div className="grid grid-cols-2 gap-2.5">
              {PRESETS.map((preset, i) => {
                const isActive =
                  config.fontFamily === preset.config.fontFamily &&
                  config.uppercase === preset.config.uppercase &&
                  config.wordsPerBatch === preset.config.wordsPerBatch &&
                  config.textColor.toLowerCase() === preset.config.textColor.toLowerCase()

                return (
                  <button
                    key={i}
                    onClick={() => update(preset.config)}
                    className={`p-3 rounded-xl border text-left transition-all flex flex-col gap-1 ${
                      isActive
                        ? 'bg-amber-500/15 border-amber-500/60 shadow-md shadow-amber-500/10'
                        : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-950'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{preset.name}</span>
                      {isActive && <Check className="w-3.5 h-3.5 text-amber-400" />}
                    </div>
                    <span className="text-[11px] text-slate-400">{preset.desc}</span>
                  </button>
                )
              })}
            </div>
          )}

          {/* TAB 2: Full Detailed Customization Controls */}
          {activeTab === 'custom' && (
            <div className="flex flex-col gap-4 bg-slate-950/70 p-4 rounded-xl border border-slate-800">
              {/* 1. Style Chữ (Font Style) */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between text-xs">
                  <label className="font-semibold text-slate-200">1. Style Chữ (Kiểu Phông):</label>
                  <button
                    onClick={() => update({ uppercase: !config.uppercase })}
                    className={`text-[11px] px-2.5 py-0.5 rounded font-bold transition-all border ${
                      config.uppercase
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    {config.uppercase ? 'IN HOA (ON)' : 'In hoa (Off)'}
                  </button>
                </div>
                <div className="grid grid-cols-3 sm:grid-cols-5 gap-1.5">
                  {[
                    { id: 'sans', label: 'Sans Hiện Đại' },
                    { id: 'impact', label: 'Impact Viral' },
                    { id: 'serif', label: 'Serif Noir' },
                    { id: 'comic', label: 'Comic Vui' },
                    { id: 'mono', label: 'Monospace' },
                  ].map(f => (
                    <button
                      key={f.id}
                      onClick={() => update({ fontFamily: f.id as TextOverlayConfig['fontFamily'] })}
                      className={`py-2 px-1.5 rounded-lg text-xs font-semibold border text-center transition-all ${
                        config.fontFamily === f.id
                          ? 'bg-amber-500 text-slate-950 border-amber-500 shadow-md font-bold'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 2. Số Lượng Từ Hiển Thị Trong 1 Lần (Words Per Screen) */}
              <div className="flex flex-col gap-2 pt-1 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">2. Số Lượng Từ Hiển Thị Trong 1 Lần:</span>
                  <span className="font-mono text-amber-400 font-black text-sm">
                    {config.wordsPerBatch === 0 ? 'Toàn bộ câu (Cả câu)' : `${config.wordsPerBatch} từ / lần`}
                  </span>
                </div>

                <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
                  {[
                    { val: 1, label: '1 Từ', desc: 'Hormozi / Viral' },
                    { val: 2, label: '2 Từ', desc: 'Cụm ngắn' },
                    { val: 3, label: '3 Từ', desc: 'Chuẩn TikTok' },
                    { val: 4, label: '4 Từ', desc: 'Dễ đọc' },
                    { val: 6, label: '6 Từ', desc: 'Đoạn ngắn' },
                    { val: 0, label: 'Cả Câu', desc: 'Toàn bộ câu' },
                  ].map(item => (
                    <button
                      key={item.val}
                      onClick={() => update({ wordsPerBatch: item.val })}
                      className={`py-2 px-1.5 rounded-xl border text-center transition-all flex flex-col items-center justify-center ${
                        config.wordsPerBatch === item.val
                          ? 'bg-amber-500 text-slate-950 border-amber-500 shadow-md font-bold'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                      }`}
                    >
                      <span className="text-xs font-bold">{item.label}</span>
                      <span
                        className={`text-[10px] ${
                          config.wordsPerBatch === item.val ? 'text-slate-950 font-medium' : 'text-slate-500'
                        }`}
                      >
                        {item.desc}
                      </span>
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-3 pt-0.5">
                  <span className="text-[11px] text-slate-400">Thanh trượt:</span>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    step={1}
                    value={config.wordsPerBatch === 0 ? 10 : config.wordsPerBatch}
                    onChange={e => update({ wordsPerBatch: parseInt(e.target.value) })}
                    className="flex-1 accent-amber-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
                  />
                  <button
                    onClick={() => update({ wordsPerBatch: config.wordsPerBatch === 0 ? 3 : 0 })}
                    className={`text-[10px] px-2 py-0.5 rounded border transition-all ${
                      config.wordsPerBatch === 0
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    {config.wordsPerBatch === 0 ? '✓ Đang chọn Cả Câu' : 'Chuyển sang Cả Câu'}
                  </button>
                </div>
              </div>

              {/* 3. Kích Cỡ Chữ Bao Nhiêu (Font Size) */}
              <div className="flex flex-col gap-2 pt-1 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">3. Kích Cỡ Chữ (Font Size):</span>
                  <span className="font-mono text-amber-400 font-black text-sm">{config.fontSize}px</span>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min={14}
                    max={48}
                    step={2}
                    value={config.fontSize}
                    onChange={e => update({ fontSize: parseInt(e.target.value) })}
                    className="flex-1 accent-amber-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
                  />
                  <div className="flex gap-1.5">
                    {[
                      { sz: 18, label: 'Nhỏ' },
                      { sz: 24, label: 'Vừa' },
                      { sz: 32, label: 'Lớn' },
                      { sz: 40, label: 'Cực Đại' },
                    ].map(item => (
                      <button
                        key={item.sz}
                        onClick={() => update({ fontSize: item.sz })}
                        className={`text-[10px] px-2 py-1 rounded font-medium border transition-all ${
                          config.fontSize === item.sz
                            ? 'bg-amber-500 text-slate-950 font-bold border-amber-500 shadow-sm'
                            : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                        }`}
                      >
                        {item.label} ({item.sz})
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* 4. Màu Chữ (Đơn giản, 1 click, không highlight) */}
              <div className="flex flex-col gap-2 pt-1 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">4. Màu Chữ:</span>
                  <span className="font-mono text-[11px] text-slate-400">{config.textColor}</span>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  {TEXT_COLORS.map(c => (
                    <button
                      key={c.color}
                      onClick={() => update({ textColor: c.color })}
                      className={`w-7 h-7 rounded-full border-2 transition-transform hover:scale-110 flex items-center justify-center ${
                        config.textColor.toLowerCase() === c.color.toLowerCase()
                          ? 'border-amber-400 scale-110 shadow-md ring-2 ring-amber-400/30'
                          : 'border-transparent'
                      }`}
                      style={{ backgroundColor: c.color }}
                      title={c.label}
                    >
                      {config.textColor.toLowerCase() === c.color.toLowerCase() && (
                        <Check className="w-3.5 h-3.5 text-black drop-shadow" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* 5. Vị Trí Hiển Thị Màn Hình */}
              <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                <span className="text-xs font-semibold text-slate-300">5. Vị trí hiển thị:</span>
                <div className="flex gap-2">
                  {[
                    { id: 'bottom', label: 'Đáy Màn Hình' },
                    { id: 'center', label: 'Chính Giữa' },
                    { id: 'top', label: 'Đỉnh Màn Hình' },
                  ].map(pos => (
                    <button
                      key={pos.id}
                      onClick={() => update({ position: pos.id as TextOverlayConfig['position'] })}
                      className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                        config.position === pos.id
                          ? 'bg-amber-500 text-slate-950 font-bold border-amber-500'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      {pos.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
