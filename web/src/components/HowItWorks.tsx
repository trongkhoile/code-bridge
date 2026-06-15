import React from 'react'

const steps = [
  {
    n: '1',
    title: 'Cài & Chạy phần mềm',
    desc: 'Tải về, giải nén, mở MT5 đăng nhập rồi chạy ALGOBOT.exe. Điền token và nhấn Khởi động.',
  },
  {
    n: '2',
    title: 'Tạo Alert trên TradingView',
    desc: 'Copy Webhook URL và JSON từ app. Dán vào TradingView Alert → Notifications → Webhook URL.',
  },
  {
    n: '3',
    title: 'Tự động đặt lệnh',
    desc: 'Mỗi khi tín hiệu kích hoạt, lệnh được đặt tức thì lên tài khoản MT5 của bạn.',
  },
]

export default function HowItWorks() {
  return (
    <section id="how" className="py-24 px-6">
      <div className="max-w-4xl mx-auto text-center">
        <p className="text-ab-accent text-xs font-bold tracking-widest uppercase mb-2">Cách hoạt động</p>
        <h2 className="text-3xl md:text-4xl font-extrabold mb-14">3 bước để tự động hoá</h2>

        <div className="flex flex-col md:flex-row items-start justify-center">
          {steps.map(({ n, title, desc }, i) => (
            <React.Fragment key={n}>
              {/* Step */}
              <div className="flex flex-col items-center text-center w-56 px-4 mx-auto md:mx-0">
                <div className="w-14 h-14 rounded-full bg-ab-accent/15 border-2 border-ab-accent text-ab-accent font-extrabold text-xl flex items-center justify-center mb-5 flex-shrink-0">
                  {n}
                </div>
                <h3 className="font-bold text-base mb-2">{title}</h3>
                <p className="text-ab-muted text-sm leading-relaxed">{desc}</p>
              </div>

              {/* Arrow */}
              {i < steps.length - 1 && (
                <div className="hidden md:flex items-center justify-center flex-shrink-0 pt-5 text-ab-border text-2xl w-12">
                  →
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  )
}
