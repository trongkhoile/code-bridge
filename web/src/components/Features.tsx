interface Feature {
  icon: string
  title: string
  desc: string
}

const features: Feature[] = [
  { icon: '01', title: 'Đặt lệnh tức thì',       desc: 'Tín hiệu từ TradingView được nhận và đặt lệnh MT5 trong vòng chưa đầy 1 giây.' },
  { icon: '02', title: 'Bảo mật Webhook Token',   desc: 'Mỗi request phải có token hợp lệ. Không ai có thể gửi lệnh giả mạo vào hệ thống.' },
  { icon: '03', title: 'Strategy & Indicator',    desc: 'Hỗ trợ cả Pine Script Strategy tự động và Indicator thủ công với 2 JSON BUY/SELL riêng.' },
  { icon: '04', title: 'Tuỳ chỉnh Lot, SL, TP',  desc: 'Cài mặc định hoặc truyền động Lot, Stop Loss, Take Profit trực tiếp qua JSON.' },
  { icon: '05', title: 'Log realtime',            desc: 'Xem toàn bộ hoạt động theo thời gian thực. Copy webhook URL và JSON chỉ 1 click.' },
  { icon: '06', title: 'Multi-symbol',            desc: 'Một server xử lý nhiều symbol cùng lúc. Tạo nhiều Alert trên TradingView là đủ.' },
]

export default function Features() {
  return (
    <section id="features" className="bg-ab-dark py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-14">
          <p className="text-ab-accent text-xs font-bold tracking-widest uppercase mb-2">Tính năng</p>
          <h2 className="text-3xl md:text-4xl font-extrabold">Mọi thứ bạn cần để tự động hoá</h2>
          <p className="text-ab-muted mt-3 max-w-md mx-auto">Phần mềm nhẹ, chạy trên Windows, không cần VPS hay server riêng.</p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map(({ icon, title, desc }) => (
            <div key={title}
                 className="bg-ab-card border border-ab-border rounded-2xl p-7 hover:border-ab-accent hover:-translate-y-1 transition-all duration-200">
              <div className="w-11 h-11 bg-ab-accent/10 border border-ab-accent/20 rounded-xl flex items-center justify-center text-ab-accent font-bold text-sm font-mono mb-5">
                {icon}
              </div>
              <h3 className="font-bold text-base mb-2">{title}</h3>
              <p className="text-ab-muted text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
