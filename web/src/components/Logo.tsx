export default function Logo({ size = 22 }: { size?: number }) {
  return (
    <span className="inline-flex items-center font-extrabold tracking-tight" style={{ fontSize: size, gap: -size * 0.05 }}>
      <span className="text-white">A</span>

      {/* Candlestick icon */}
      <svg
        width={size * 0.9}
        height={size * 0.9}
        viewBox="0 0 24 24"
        fill="none"
      >
          {/* Single candle */}
        <line x1="12" y1="2"  x2="12" y2="6"  stroke="#00c896" strokeWidth="1.8" strokeLinecap="round" />
        <rect x="9" y="6" width="6" height="12" rx="1" fill="#00c896" />
        <line x1="12" y1="18" x2="12" y2="22" stroke="#00c896" strokeWidth="1.8" strokeLinecap="round" />
      </svg>

      <span className="text-white">GOBOT</span>
    </span>
  )
}
