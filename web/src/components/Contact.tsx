export default function Contact() {
  return (
    <section id="contact" className="gradient-contact py-28 px-6 text-center">
      <div className="max-w-2xl mx-auto">
        <p className="text-ab-accent text-xs font-bold tracking-widest uppercase mb-2">Liên hệ</p>
        <h2 className="text-3xl md:text-4xl font-extrabold mb-4">
          Cần hỗ trợ hoặc code theo yêu cầu?
        </h2>
        <p className="text-ab-muted mb-12 leading-relaxed">
          AlgoBot VN nhận code bot MT5, MT4, chỉ báo TradingView theo yêu cầu.<br />
          Liên hệ để được tư vấn miễn phí.
        </p>

        <div className="flex flex-wrap justify-center gap-4 mb-12">
          <a href="https://www.facebook.com/profile.php?id=100087370578208&locale=vi_VN"
             target="_blank" rel="noopener noreferrer"
             className="bg-ab-card border border-ab-border hover:border-ab-accent rounded-2xl px-8 py-5 min-w-[160px] transition-colors group">
            <p className="text-ab-hint text-xs font-bold tracking-widest uppercase mb-2">Facebook</p>
            <p className="text-ab-accent font-semibold text-base group-hover:underline">AlgoBot VN</p>
          </a>

          <a href="https://zalo.me/0856176102"
             target="_blank" rel="noopener noreferrer"
             className="bg-ab-card border border-ab-border hover:border-ab-accent rounded-2xl px-8 py-5 min-w-[160px] transition-colors group">
            <p className="text-ab-hint text-xs font-bold tracking-widest uppercase mb-2">Zalo</p>
            <p className="text-ab-accent font-semibold text-base group-hover:underline">0856 176 102</p>
          </a>

          <a href="https://algobotvn.com"
             target="_blank" rel="noopener noreferrer"
             className="bg-ab-card border border-ab-border hover:border-ab-accent rounded-2xl px-8 py-5 min-w-[160px] transition-colors group">
            <p className="text-ab-hint text-xs font-bold tracking-widest uppercase mb-2">Website</p>
            <p className="text-ab-accent font-semibold text-base group-hover:underline">algobotvn.com</p>
          </a>
        </div>

        <a href="https://drive.google.com/uc?export=download&id=1JBXXeHSnRF3MGdrfsO5n2KU0QDmLte6J"
           target="_blank" rel="noopener noreferrer"
           className="inline-block bg-ab-accent text-ab-dark font-bold text-base px-10 py-4 rounded-xl hover:bg-ab-hover transition-all hover:-translate-y-0.5 shadow-lg shadow-ab-accent/20">
          Tải phần mềm miễn phí
        </a>
      </div>
    </section>
  )
}
