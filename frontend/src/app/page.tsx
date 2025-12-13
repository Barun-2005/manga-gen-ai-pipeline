"use client";

import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0a110e]">
      {/* Navbar */}
      <header className="fixed top-0 left-0 right-0 z-50">
        <div className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mt-4">
          <div className="bg-[#16261e]/80 backdrop-blur-md border border-[#264532] rounded-full px-6 py-3 flex items-center justify-between shadow-lg">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[#38e07b] text-3xl">auto_stories</span>
              <h1 className="text-white text-xl font-bold tracking-tight">MangaGen<span className="text-[#38e07b]">.AI</span></h1>
            </div>
            <nav className="hidden md:flex items-center gap-8">
              <a className="text-gray-300 hover:text-white text-sm font-medium transition-colors" href="#features">How it Works</a>
              <a className="text-gray-300 hover:text-white text-sm font-medium transition-colors" href="#gallery">Gallery</a>
            </nav>
            <Link href="/create" className="flex items-center justify-center rounded-full h-10 px-5 bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] text-sm font-bold transition-all shadow-[0_0_15px_rgba(56,224,123,0.3)] hover:shadow-[0_0_25px_rgba(56,224,123,0.5)]">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-gradient-radial from-[#38e07b]/15 to-transparent pointer-events-none opacity-50"></div>
        <div className="absolute top-20 right-0 w-[500px] h-[500px] bg-[#7c3aed]/10 rounded-full blur-[100px] pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-[#38e07b]/5 rounded-full blur-[100px] pointer-events-none"></div>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div className="flex flex-col gap-6 max-w-2xl text-center lg:text-left mx-auto lg:mx-0">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#264532]/50 border border-[#38e07b]/20 w-fit mx-auto lg:mx-0">
                <span className="flex h-2 w-2 rounded-full bg-[#38e07b] animate-pulse"></span>
                <span className="text-xs font-medium text-[#38e07b] uppercase tracking-wider">v2.0 Model Live Now</span>
              </div>

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black leading-[1.1] tracking-tight text-white">
                TURN WORDS <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#38e07b] via-white to-[#38e07b] bg-[length:200%_auto] animate-[gradient_3s_linear_infinite]">INTO WORLDS</span>
              </h1>

              <p className="text-gray-400 text-lg sm:text-xl leading-relaxed max-w-lg mx-auto lg:mx-0">
                The world&apos;s fastest AI manga generator. Create professional quality manga pages from simple text prompts in seconds.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start mt-4">
                <Link href="/create" className="flex h-14 items-center justify-center rounded-full px-8 bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] text-lg font-bold transition-all shadow-[0_0_20px_rgba(56,224,123,0.4)] hover:shadow-[0_0_30px_rgba(56,224,123,0.6)] group">
                  <span className="material-symbols-outlined mr-2 group-hover:translate-x-1 transition-transform">draw</span>
                  Create Your Manga
                </Link>
                <button className="flex h-14 items-center justify-center rounded-full px-8 bg-[#264532]/30 hover:bg-[#264532]/50 border border-[#264532] text-white text-lg font-bold transition-all backdrop-blur-sm">
                  View Gallery
                </button>
              </div>

              <div className="flex items-center justify-center lg:justify-start gap-4 mt-6 text-sm text-gray-500">
                <div className="flex -space-x-3">
                  <div className="w-8 h-8 rounded-full border-2 border-[#0a110e] bg-gradient-to-r from-[#38e07b] to-[#2bc968]"></div>
                  <div className="w-8 h-8 rounded-full border-2 border-[#0a110e] bg-gradient-to-r from-[#7c3aed] to-[#ec4899]"></div>
                  <div className="w-8 h-8 rounded-full border-2 border-[#0a110e] bg-gradient-to-r from-[#3b82f6] to-[#38e07b]"></div>
                </div>
                <p>Trusted by 10,000+ creators</p>
              </div>
            </div>

            {/* Right Visual - Demo Preview */}
            <div className="relative w-full h-full min-h-[400px] lg:min-h-[600px] flex items-center justify-center">
              <div className="relative w-full aspect-[3/4] max-w-md mx-auto">
                <div className="absolute inset-0 bg-[#16261e] rounded-xl overflow-hidden border border-[#264532] shadow-2xl rotate-3 hover:rotate-0 transition-transform duration-500 z-20 group">
                  <div className="absolute top-4 left-4 right-4 z-10 flex justify-between items-center">
                    <span className="bg-black/70 backdrop-blur text-white text-xs px-2 py-1 rounded">Page 01</span>
                    <span className="material-symbols-outlined text-white drop-shadow-md">favorite</span>
                  </div>
                  <div className="h-full w-full bg-gradient-to-br from-[#1a2c22] to-[#264532] flex items-center justify-center">
                    <div className="text-center">
                      <span className="material-symbols-outlined text-6xl text-[#38e07b]/50">auto_stories</span>
                      <p className="text-gray-500 mt-2 text-sm">Your manga preview</p>
                    </div>
                  </div>
                </div>
                <div className="absolute inset-0 bg-[#16261e] rounded-xl border border-[#264532] shadow-xl -rotate-2 scale-95 z-10 translate-x-4 translate-y-4 opacity-60"></div>
                <div className="absolute inset-0 bg-[#16261e] rounded-xl border border-[#264532] shadow-lg -rotate-6 scale-90 z-0 translate-x-8 translate-y-8 opacity-30"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 relative overflow-hidden" id="features">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-[#38e07b] font-bold tracking-wider uppercase mb-3 text-sm">Workflow</h2>
            <h3 className="text-3xl md:text-5xl font-black text-white mb-6">From Idea to Page in <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#38e07b] to-[#7c3aed]">3 Steps</span></h3>
            <p className="text-gray-400 text-lg">Our AI engine handles the complex drawing process so you can focus purely on the story.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
            {/* Step 1 */}
            <div className="glass-panel p-8 rounded-2xl relative group hover:-translate-y-2 transition-transform duration-300">
              <div className="absolute -top-6 left-8 bg-[#16261e] border border-[#264532] p-3 rounded-xl shadow-lg group-hover:border-[#38e07b]/50 transition-colors">
                <span className="material-symbols-outlined text-[#38e07b] text-3xl">edit_note</span>
              </div>
              <div className="mt-8">
                <h4 className="text-xl font-bold text-white mb-3">1. Describe</h4>
                <p className="text-gray-400 leading-relaxed mb-6">Type your scene details. Specify characters, poses, and atmosphere.</p>
                <div className="bg-[#0f1a14] p-4 rounded-lg border border-[#264532] text-sm text-gray-300 font-mono">
                  <span className="text-[#38e07b]">&gt;</span> hero standing on rooftop, rain, city background...
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="glass-panel p-8 rounded-2xl relative group hover:-translate-y-2 transition-transform duration-300">
              <div className="absolute -top-6 left-8 bg-[#16261e] border border-[#264532] p-3 rounded-xl shadow-lg group-hover:border-[#38e07b]/50 transition-colors">
                <span className="material-symbols-outlined text-[#38e07b] text-3xl">auto_fix_high</span>
              </div>
              <div className="mt-8">
                <h4 className="text-xl font-bold text-white mb-3">2. Generate</h4>
                <p className="text-gray-400 leading-relaxed mb-6">Our engine renders high-fidelity panels and speech bubbles instantly.</p>
                <div className="h-24 w-full bg-[#0f1a14] rounded-lg border border-[#264532] relative overflow-hidden flex items-center justify-center">
                  <span className="text-[#38e07b] text-xs font-bold uppercase tracking-widest animate-pulse">Processing...</span>
                </div>
              </div>
            </div>

            {/* Step 3 */}
            <div className="glass-panel p-8 rounded-2xl relative group hover:-translate-y-2 transition-transform duration-300">
              <div className="absolute -top-6 left-8 bg-[#16261e] border border-[#264532] p-3 rounded-xl shadow-lg group-hover:border-[#38e07b]/50 transition-colors">
                <span className="material-symbols-outlined text-[#38e07b] text-3xl">download</span>
              </div>
              <div className="mt-8">
                <h4 className="text-xl font-bold text-white mb-3">3. Download</h4>
                <p className="text-gray-400 leading-relaxed mb-6">Export your pages in high resolution, ready for publishing.</p>
                <button className="w-full py-3 rounded-lg bg-[#38e07b]/10 hover:bg-[#38e07b]/20 text-[#38e07b] border border-[#38e07b]/20 hover:border-[#38e07b] font-bold text-sm transition-all flex items-center justify-center gap-2">
                  <span className="material-symbols-outlined text-lg">file_download</span>
                  Download .PNG
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="container mx-auto px-4 relative z-10 text-center">
          <div className="max-w-4xl mx-auto bg-gradient-to-r from-[#16261e] to-[#1f3529] border border-[#264532] p-8 md:p-12 rounded-3xl relative overflow-hidden">
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-[#38e07b]/20 rounded-full blur-[80px]"></div>
            <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-[#7c3aed]/20 rounded-full blur-[80px]"></div>

            <h2 className="text-3xl md:text-5xl font-black text-white mb-6">Ready to Create?</h2>
            <p className="text-gray-300 text-lg mb-8 max-w-xl mx-auto">Start creating your manga right now. No signup required.</p>

            <Link href="/create" className="inline-flex h-12 items-center justify-center rounded-full px-8 bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] text-lg font-bold transition-all shadow-lg hover:shadow-[#38e07b]/40">
              Start Creating Free
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0a120d] border-t border-[#264532] py-8">
        <div className="container mx-auto px-4 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <span className="material-symbols-outlined text-[#38e07b]">auto_stories</span>
            <span className="text-white font-bold">MangaGen.AI</span>
          </div>
          <p className="text-gray-600 text-sm">© 2024 MangaGen AI. Built with ❤️ by Barun</p>
        </div>
      </footer>
    </div>
  );
}
