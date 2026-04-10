export function LandingHero() {
  return (
    <section className="relative py-20 md:py-28 overflow-hidden">
      {/* Soft radial blobs */}
      <div className="absolute top-0 right-0 w-[480px] h-[480px] bg-indigo-500/10 rounded-full blur-[120px] -z-10" />
      <div className="absolute -bottom-20 -left-10 w-[360px] h-[360px] bg-cyan-500/8 rounded-full blur-[100px] -z-10" />

      <div className="max-w-5xl mx-auto px-6">
        <div className="text-center flex flex-col items-center">

          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-10 bg-indigo-500/8 border border-indigo-400/30 rounded-full text-xs font-medium tracking-widest uppercase text-indigo-700">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
            Intelligent Incident Management
          </div>

          {/* Heading */}
          <h1 className="text-[42px] md:text-[72px] font-semibold leading-[1.08] tracking-[-0.03em] text-slate-900 mb-6">
            Production incidents,{" "}
            <br />
            <span className="bg-gradient-to-r from-indigo-600 to-cyan-600 bg-clip-text text-transparent">
              resolved in seconds
            </span>
          </h1>

          {/* Subtitle */}
          <p className="max-w-xl text-lg text-slate-500 leading-relaxed font-normal mb-12">
            AI-powered triage that understands your stack. Report issues, receive
            intelligent analysis, and coordinate team response — all from a single
            interface.
          </p>

          {/* CTAs */}
          <div className="flex flex-row flex-wrap gap-3 justify-center mb-14">
            <button className="inline-flex items-center gap-2 px-7 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-[10px] shadow-[0_4px_14px_rgba(79,70,229,0.28)] hover:shadow-[0_8px_24px_rgba(79,70,229,0.36)] hover:-translate-y-px transition-all duration-200">
              Start reporting
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
            <button className="inline-flex items-center gap-2 px-7 py-3.5 bg-white hover:bg-indigo-50/60 text-indigo-600 text-sm font-medium rounded-[10px] border border-indigo-300/40 hover:border-indigo-400/60 transition-all duration-200">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <path d="M9 9h6M9 13h4" />
              </svg>
              View dashboard
            </button>
          </div>

          {/* Trust bar */}
          <div className="flex items-center justify-center flex-wrap gap-6">
            {[
              {
                label: "Enterprise-grade security",
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                ),
              },
              {
                label: "Zero setup time",
                icon: (
                  <>
                    <circle cx="12" cy="12" r="10" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3" />
                  </>
                ),
              },
              {
                label: "Open source",
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                ),
              },
            ].map(({ label, icon }, i, arr) => (
              <div key={label} className="flex items-center gap-6">
                <div className="flex items-center gap-2 text-slate-400 text-xs font-normal">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    {icon}
                  </svg>
                  {label}
                </div>
                {i < arr.length - 1 && (
                  <span className="w-1 h-1 rounded-full bg-slate-300" />
                )}
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}