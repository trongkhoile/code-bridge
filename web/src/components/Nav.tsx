import Logo from './Logo'

const links = [
  { label: 'Tính năng',       href: '#features' },
  { label: 'Cách hoạt động',  href: '#how'      },
  { label: 'Cài đặt',         href: '#install'  },
  { label: 'FAQ',              href: '#faq'      },
  { label: 'Liên hệ',         href: '#contact'  },
]

export default function Nav() {
  return (
    <nav className="sticky top-0 z-50 bg-ab-dark/90 backdrop-blur-md border-b border-ab-border">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">

        <a href="#" className="flex items-center gap-2">
          <Logo size={20} />
          <span className="text-ab-muted font-medium text-sm ml-1">VN</span>
        </a>

        <ul className="hidden md:flex gap-8 list-none">
          {links.map(({ label, href }) => (
            <li key={href}>
              <a href={href} className="text-ab-muted text-sm font-medium hover:text-ab-accent transition-colors">
                {label}
              </a>
            </li>
          ))}
        </ul>

        <a href="https://drive.google.com/uc?export=download&id=1JBXXeHSnRF3MGdrfsO5n2KU0QDmLte6J"
           target="_blank" rel="noopener noreferrer"
           className="bg-ab-accent text-ab-dark font-bold text-sm px-5 py-2 rounded-lg hover:bg-ab-hover transition-colors">
          Tải về
        </a>
      </div>
    </nav>
  )
}
