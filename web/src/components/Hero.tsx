const mockFields = [
  ['Webhook Token', '••••••••••'],
  ['Port', '8000'],
  ['Symbol', 'XAUUSD'],
  ['Lot / SL / TP', '0.01 / 0 / 0'],
]

const logLines: { text: string; accent?: boolean }[] = [
  { text: '09:14:22  [INFO]  Kết nối MT5 thành công | TK #463426957', accent: true },
  { text: '09:14:22  [INFO]  Số dư: 999,999,988.85 USD | Exness', accent: true },
  { text: '09:14:25  [INFO]  Server khởi động tại port 8000' },
  { text: '09:15:03  [INFO]  Webhook nhận: {"action":"buy","symbol":"XAUUSD"}' },
  { text: '09:15:03  [INFO]  Lệnh thành công | BUY 0.01 XAUUSD @ 2345.12', accent: true },
  { text: '09:22:11  [INFO]  Webhook nhận: {"action":"sell","symbol":"XAUUSD"}' },
  { text: '09:22:11  [INFO]  Lệnh thành công | SELL 0.01 XAUUSD @ 2341.80', accent: true },
]

export default function Hero() {
  return (
    <section className="gradient-hero min-h-[92vh] flex flex-col items-center justify-center text-center px-6 py-20">

      <span className="inline-flex items-center gap-2 bg-ab-accent/10 border border-ab-accent/30 text-ab-accent text-xs font-bold px-4 py-1.5 rounded-full mb-6 tracking-widest uppercase">
        Tự động hoá giao dịch MT5
      </span>

      <h1 className="text-4xl md:text-[3.4rem] font-extrabold leading-tight max-w-3xl">
        Kết nối <span className="text-ab-accent">TradingView</span>
        <br />với MetaTrader 5 tự động
      </h1>

      <p className="text-ab-muted text-lg max-w-xl mt-5 mb-9 leading-relaxed">
        Nhận tín hiệu từ TradingView, đặt lệnh tức thì lên MT5 —
        không cần ngồi canh màn hình, không cần lập trình.
      </p>

      <div className="flex gap-4 flex-wrap justify-center">
        <a href="#install"
           className="bg-ab-accent text-ab-dark font-bold px-8 py-3.5 rounded-xl hover:bg-ab-hover transition-all hover:-translate-y-0.5 shadow-lg shadow-ab-accent/20">
          Tải phần mềm miễn phí
        </a>
        <a href="#how"
           className="border border-ab-border text-ab-muted font-semibold px-8 py-3.5 rounded-xl hover:border-ab-accent hover:text-ab-accent transition-colors">
          Xem cách hoạt động
        </a>
      </div>

      {/* App mockup */}
      <div className="animate-float mt-16 w-full max-w-3xl bg-ab-card border border-ab-border rounded-2xl overflow-hidden shadow-[0_32px_80px_rgba(0,0,0,.5)]">
        {/* Title bar */}
        <div className="bg-ab-dark px-4 py-3 flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-ab-red" />
          <span className="w-3 h-3 rounded-full bg-yellow-400" />
          <span className="w-3 h-3 rounded-full bg-ab-accent" />
          <span className="ml-3 text-ab-hint text-xs font-mono">ALGOBOT - TradingView Automation</span>
        </div>

        <div className="p-5 grid md:grid-cols-[250px_1fr] gap-4 text-left">
          {/* Settings panel */}
          <div className="bg-ab-dark rounded-xl p-4">
            <p className="text-ab-accent text-[10px] font-bold tracking-widest mb-3">CÀI ĐẶT</p>
            {mockFields.map(([label, value]) => (
              <div key={label} className="mb-3">
                <p className="text-ab-hint text-[10px] mb-1">{label}</p>
                <div className="bg-white/5 border border-ab-border rounded-md px-2.5 py-1.5 text-ab-muted text-xs font-mono">
                  {value}
                </div>
              </div>
            ))}
            <button className="w-full bg-ab-accent text-ab-dark font-bold text-xs py-2.5 rounded-lg mt-1 cursor-default">
              ▶&nbsp; Khởi động server
            </button>
          </div>

          {/* Log panel */}
          <div className="bg-ab-dark rounded-xl p-4 font-mono text-xs leading-7 text-[#a0c8e8] overflow-hidden">
            {logLines.map((line, i) => (
              <p key={i} className={line.accent ? 'text-ab-accent' : ''}>
                {line.text}
              </p>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
