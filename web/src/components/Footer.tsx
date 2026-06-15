import Logo from './Logo'

export default function Footer() {
  return (
    <footer className="bg-ab-dark border-t border-ab-border px-6 py-7">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          <Logo size={18} />
          <span className="text-ab-muted font-medium text-sm ml-1">VN</span>
        </div>
        <p className="text-ab-hint text-sm">© 2025 AlgoBot VN. Tự động hoá giao dịch MT5 từ TradingView.</p>
        <p className="text-ab-hint text-xs">Code bot MT5, MT4, chỉ báo TradingView theo yêu cầu</p>
      </div>
    </footer>
  )
}
