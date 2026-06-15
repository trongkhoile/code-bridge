const steps = [
  {
    title: 'Tải phần mềm về máy',
    body: (
      <>
        <p className="text-ab-muted text-sm mb-3">Nhấn nút Tải về, giải nén file ZIP ra một thư mục bất kỳ.</p>
        <a href="https://drive.google.com/uc?export=download&id=1JBXXeHSnRF3MGdrfsO5n2KU0QDmLte6J" target="_blank" rel="noopener noreferrer" className="inline-block bg-ab-accent text-ab-dark font-bold text-sm px-5 py-2.5 rounded-lg hover:bg-ab-hover transition-colors">
          Tải ALGOBOT-TradingView.zip
        </a>
      </>
    ),
  },
  {
    title: 'Mở MetaTrader 5 và đăng nhập',
    body: (
      <>
        <p className="text-ab-muted text-sm">Phần mềm kết nối vào MT5 đang chạy sẵn trên máy. Bạn phải đăng nhập tài khoản trước.</p>
        <div className="mt-3 bg-ab-accent/8 border-l-2 border-ab-accent pl-3 py-2 text-ab-muted text-xs rounded-r-md">
          ⚠ Nếu chưa cài MT5, tải tại trang broker của bạn (Exness, ICMarkets, v.v.)
        </div>
      </>
    ),
  },
  {
    title: 'Chạy ALGOBOT-TradingView.exe',
    body: <p className="text-ab-muted text-sm">Nếu Windows hiện cảnh báo SmartScreen, bấm <strong className="text-white">More info → Run anyway</strong>.</p>,
  },
  {
    title: 'Cài đặt ngrok để nhận webhook',
    body: (
      <>
        <p className="text-ab-muted text-sm mb-3">Nếu chạy trên máy cá nhân (không phải VPS), cần ngrok để TradingView gửi được tín hiệu về.</p>
        <div className="bg-ab-dark rounded-lg p-3 text-xs text-ab-muted">
          Tải ngrok tại <span className="text-ab-accent">ngrok.com</span>, chạy lệnh:<br />
          <code className="text-ab-accent font-mono">ngrok http 8000</code><br />
          Copy URL hiện ra và dán vào ô <strong className="text-white">Public URL</strong> trong app.
        </div>
      </>
    ),
  },
  {
    title: 'Tạo Alert trên TradingView',
    body: <p className="text-ab-muted text-sm">Copy Webhook URL và JSON từ tab <em className="text-white">TradingView Alert</em> trong app, dán vào Alert trên TradingView.</p>,
  },
]

const requirements = [
  { title: 'Windows 10 / 11',      desc: 'Chỉ hỗ trợ Windows (thư viện MT5 chỉ có trên Windows)' },
  { title: 'MetaTrader 5',         desc: 'Phiên bản mới nhất, đã đăng nhập tài khoản' },
  { title: 'Kết nối Internet',     desc: 'Để nhận webhook từ TradingView' },
  { title: 'Tài khoản TradingView',desc: 'Gói Essential trở lên (có Webhook Alert)' },
  { title: 'ngrok hoặc VPS',       desc: 'Để TradingView gửi webhook về máy của bạn' },
]

const jsonExample = `{
  "token": "your_token",
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "lot": 0.01,
  "sl": 0,
  "tp": 0
}`

export default function Install() {
  return (
    <section id="install" className="bg-ab-dark py-24 px-6">
      <div className="max-w-5xl mx-auto">
        <p className="text-ab-accent text-xs font-bold tracking-widest uppercase mb-2">Hướng dẫn cài đặt</p>
        <h2 className="text-3xl md:text-4xl font-extrabold mb-12">Bắt đầu trong 5 phút</h2>

        <div className="grid lg:grid-cols-[1fr_360px] gap-10 items-start">
          {/* Steps */}
          <div className="flex flex-col gap-7">
            {steps.map(({ title, body }, i) => (
              <div key={i} className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-ab-accent text-ab-dark font-extrabold text-sm flex items-center justify-center mt-0.5">
                  {i + 1}
                </div>
                <div>
                  <h4 className="font-bold text-base mb-2">{title}</h4>
                  {body}
                </div>
              </div>
            ))}
          </div>

          {/* Right sidebar */}
          <div className="bg-ab-card border border-ab-border rounded-2xl p-6 flex flex-col gap-8">
            {/* Requirements */}
            <div>
              <h3 className="text-ab-accent font-bold text-sm mb-4 tracking-wide">Yêu cầu hệ thống</h3>
              <div className="flex flex-col gap-3">
                {requirements.map(({ title, desc }) => (
                  <div key={title} className="flex gap-2.5">
                    <span className="text-ab-accent mt-0.5 flex-shrink-0">✓</span>
                    <div>
                      <p className="font-semibold text-sm">{title}</p>
                      <p className="text-ab-muted text-xs">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* JSON example */}
            <div>
              <h3 className="text-ab-accent font-bold text-sm mb-3 tracking-wide">Định dạng JSON tín hiệu</h3>
              <pre className="bg-ab-dark rounded-xl p-4 text-xs font-mono text-[#a0c8e8] overflow-x-auto leading-relaxed">
                {jsonExample}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
