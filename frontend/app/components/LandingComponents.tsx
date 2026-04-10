// ─── Feature Card ───────────────────────────────────────────────────────────

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  accent: string; // e.g. "indigo" | "cyan" | "purple" | "blue" | "emerald" | "rose"
}

function FeatureCard({ icon, title, description, accent }: FeatureCardProps) {
  return (
    <div className="group p-7 rounded-2xl bg-white border border-slate-100 hover:border-slate-200 hover:shadow-[0_8px_30px_rgba(0,0,0,0.06)] transition-all duration-300">
      <div
        className={`w-11 h-11 rounded-[10px] mb-5 flex items-center justify-center bg-${accent}-500/10 transition-all duration-300 group-hover:bg-${accent}-500/16 group-hover:scale-105`}
      >
        <div className={`text-${accent}-600`}>{icon}</div>
      </div>
      <h3 className="text-[15px] font-medium text-slate-900 mb-2 tracking-[-0.01em] group-hover:text-indigo-600 transition-colors duration-200">
        {title}
      </h3>
      <p className="text-sm text-slate-500 leading-relaxed font-normal">{description}</p>
    </div>
  );
}

// ─── Features Section ───────────────────────────────────────────────────────

export function FeaturesSection() {
  const features = [
    {
      icon: <CheckIcon />,
      title: "AI-Powered Analysis",
      description:
        "Automatic categorization, severity assessment, and intelligent recommendations powered by advanced language models.",
      accent: "indigo",
    },
    {
      icon: <LightningIcon />,
      title: "Real-Time Processing",
      description:
        "Instant incident intake, multimodal analysis of logs and screenshots, and immediate team notifications.",
      accent: "cyan",
    },
    {
      icon: <ChartIcon />,
      title: "Complete Observability",
      description:
        "End-to-end tracing with unique trace IDs, comprehensive audit logs, and actionable dashboards.",
      accent: "purple",
    },
    {
      icon: <SettingsIcon />,
      title: "Team Integration",
      description:
        "Seamless Slack notifications, email confirmations, and Trello board synchronization for team coordination.",
      accent: "blue",
    },
    {
      icon: <ShieldIcon />,
      title: "Security First",
      description:
        "Prompt injection detection, input validation, secure file handling, and compliance with SRE best practices.",
      accent: "emerald",
    },
    {
      icon: <TrendingIcon />,
      title: "Reduced MTTR",
      description:
        "Dramatically reduce mean time to resolution with intelligent triage and context-aware recommendations.",
      accent: "rose",
    },
  ];

  return (
    <section className="py-24">
      <div className="max-w-7xl mx-auto px-6">

        {/* Header */}
        <div className="text-center mb-14">
          <h2 className="text-[36px] md:text-[48px] font-semibold tracking-[-0.03em] text-slate-900 mb-4">
            Powerful capabilities
          </h2>
          <p className="text-base text-slate-500 max-w-xl mx-auto font-normal leading-relaxed">
            Everything you need to transform incident response into a streamlined, intelligent process
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature, idx) => (
            <FeatureCard key={idx} {...feature} />
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Stats Section ───────────────────────────────────────────────────────────

export function StatsSection() {
  const stats = [
    { value: "75%", label: "Faster triage" },
    { value: "24/7", label: "Automated support" },
    { value: "100%", label: "Traceability" },
    { value: "< 2s", label: "Response time" },
  ];

  return (
    <section className="py-16 bg-indigo-600 relative overflow-hidden">
      {/* Subtle inner glow blobs */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-white/8 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-cyan-400/10 rounded-full blur-[80px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
          {stats.map((stat, idx) => (
            <div key={idx} className="text-center">
              <div className="text-[36px] md:text-[52px] font-semibold text-white tracking-[-0.03em] leading-none mb-2">
                {stat.value}
              </div>
              <p className="text-indigo-200 text-sm font-normal">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── CTA Section ─────────────────────────────────────────────────────────────

export function CTASection() {
  return (
    <section className="py-24 relative overflow-hidden">
      <div className="absolute -top-40 right-0 w-[480px] h-[480px] bg-indigo-500/8 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute -bottom-40 left-0 w-[360px] h-[360px] bg-cyan-500/8 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-3xl mx-auto px-6 text-center relative z-10">
        <h2 className="text-[36px] md:text-[48px] font-semibold tracking-[-0.03em] text-slate-900 mb-5">
          Transform your incident response
        </h2>
        <p className="text-base text-slate-500 mb-10 max-w-xl mx-auto leading-relaxed font-normal">
          Join teams who are reducing incident response time and improving reliability
          with AI-powered triage and intelligent team coordination.
        </p>
        <button className="inline-flex items-center gap-2 px-7 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-[10px] shadow-[0_4px_14px_rgba(79,70,229,0.28)] hover:shadow-[0_8px_24px_rgba(79,70,229,0.36)] hover:-translate-y-px transition-all duration-200">
          Get started now
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </section>
  );
}

// ─── Footer ──────────────────────────────────────────────────────────────────

export function Footer() {
  const links = [
    {
      heading: "Product",
      items: ["Features", "Pricing", "Security"],
    },
    {
      heading: "Company",
      items: ["About", "Blog", "Careers"],
    },
    {
      heading: "Resources",
      items: ["Documentation", "API Docs", "Support"],
    },
    {
      heading: "Legal",
      items: ["Privacy", "Terms", "License"],
    },
  ];

  return (
    <footer className="border-t border-slate-200/60 bg-slate-950 text-slate-400 py-14">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10">
          {links.map(({ heading, items }) => (
            <div key={heading}>
              <h3 className="text-xs font-medium text-slate-200 mb-4 tracking-widest uppercase">
                {heading}
              </h3>
              <ul className="space-y-2.5">
                {items.map((item) => (
                  <li key={item}
                      className="text-sm text-slate-500 hover:text-slate-200 transition-colors duration-150"
                    >
                    <a>
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-slate-800 pt-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p className="text-xs text-slate-500">
            SRE Incident Triage Platform — Engineered for reliability and performance.
          </p>
          <p className="text-xs text-slate-600">
            Built with attention to security, observability, and user experience.
          </p>
        </div>
      </div>
    </footer>
  );
}

// ─── Icons ───────────────────────────────────────────────────────────────────

function CheckIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function LightningIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
  );
}

function TrendingIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  );
}