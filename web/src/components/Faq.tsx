import { useState } from 'react'
import { Plus, X } from 'lucide-react'

interface FaqItem {
  q: string
  a: string
}

const faqs: FaqItem[] = [
  {
    q: 'Tôi có cần biết lập trình không?',
    a: 'Không. Phần mềm có giao diện đồ hoạ đầy đủ, chỉ cần điền thông tin vào các ô và nhấn nút. JSON template đã được tạo sẵn, bạn chỉ cần copy và dán vào TradingView.',
  },
  {
    q: 'Phần mềm có miễn phí không?',
    a: 'Phiên bản cơ bản hoàn toàn miễn phí. Nếu cần tích hợp thêm tính năng theo yêu cầu riêng (nhiều tài khoản, logic phức tạp, dashboard web...) hãy liên hệ AlgoBot VN để được tư vấn.',
  },
  {
    q: 'Máy tính có phải bật 24/7 không?',
    a: 'Có, phần mềm phải đang chạy để nhận tín hiệu. Nếu muốn chạy liên tục không cần bật máy tính, bạn có thể thuê VPS Windows giá rẻ (từ 3-5$/tháng) và cài phần mềm lên đó.',
  },
  {
    q: 'Hỗ trợ những broker nào?',
    a: 'Tất cả broker hỗ trợ MetaTrader 5: Exness, ICMarkets, XM, Vantage, OANDA... Phần mềm tự động phát hiện filling mode phù hợp với từng broker.',
  },
  {
    q: 'Cần gói TradingView nào?',
    a: 'Webhook Alert yêu cầu tài khoản TradingView từ gói Essential trở lên (không phải Free). Bạn có thể dùng trial 30 ngày để thử nghiệm.',
  },
]

export default function Faq() {
  const [open, setOpen] = useState<number | null>(null)

  return (
    <section id="faq" className="py-24 px-6">
      <div className="max-w-2xl mx-auto text-center">
        <p className="text-ab-accent text-xs font-bold tracking-widest uppercase mb-2">FAQ</p>
        <h2 className="text-3xl md:text-4xl font-extrabold mb-12">Câu hỏi thường gặp</h2>

        <div className="flex flex-col gap-3 text-left">
          {faqs.map(({ q, a }, i) => (
            <div key={i} className="bg-ab-card border border-ab-border rounded-2xl overflow-hidden">
              <button
                className="w-full flex justify-between items-center px-6 py-5 font-semibold text-sm hover:text-ab-accent transition-colors text-left"
                onClick={() => setOpen(open === i ? null : i)}
              >
                {q}
                {open === i
                  ? <X size={16} className="text-ab-accent flex-shrink-0 ml-3" />
                  : <Plus size={16} className="text-ab-accent flex-shrink-0 ml-3" />
                }
              </button>
              {open === i && (
                <p className="px-6 pb-5 text-ab-muted text-sm leading-relaxed">{a}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
