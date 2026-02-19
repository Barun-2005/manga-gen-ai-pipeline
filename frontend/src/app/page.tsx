"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";

// All gallery images with metadata
const GALLERY_IMAGES = [
    { src: "/gallery/gallery-1.png", title: "Storm Chronicles", style: "B&W Manga" },
    { src: "/gallery/gallery-2.png", title: "Sakura Academy", style: "Color Anime" },
    { src: "/gallery/gallery-3.png", title: "Dragon's Fury", style: "Dark Fantasy" },
    { src: "/gallery/gallery-4.png", title: "Cyber Runner", style: "Cyberpunk" },
    { src: "/gallery/gallery-5.png", title: "Midnight Eye", style: "B&W Manga" },
    { src: "/gallery/neontech.png", title: "Neon Blade", style: "Noir Manga" },
    { src: "/gallery/Samurai.png", title: "Sunset Ronin", style: "Color" },
    { src: "/gallery/gallery-6.png", title: "Forest Spirit", style: "Color Anime" },
    { src: "/gallery/gallery-7.png", title: "Iron Fist", style: "Action" },
    { src: "/gallery/gallery-8.png", title: "Wasteland", style: "Post-Apocalyptic" },
    { src: "/gallery/sample-1.png", title: "Battle Cry", style: "Shounen" },
    { src: "/gallery/sample-2.png", title: "Ocean Dream", style: "Fantasy" },
    { src: "/gallery/sample-3.png", title: "Sky Fortress", style: "Steampunk" },
    { src: "/gallery/sample-4.png", title: "Comedy Hour", style: "Slice of Life" },
    { src: "/gallery/hero-placeholder.png", title: "Dark Knight", style: "B&W Manga" },
];

// Scroll-reveal hook
function useScrollReveal(threshold = 0.12) {
    const ref = useRef<HTMLDivElement>(null);
    const [isVisible, setIsVisible] = useState(false);
    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) { setIsVisible(true); observer.disconnect(); }
            },
            { threshold }
        );
        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, [threshold]);
    return { ref, isVisible };
}

// Only show images that actually loaded
function useAvailableImages() {
    const [available, setAvailable] = useState<typeof GALLERY_IMAGES>([]);
    useEffect(() => {
        const check = async () => {
            const results = await Promise.all(
                GALLERY_IMAGES.map((img) =>
                    new Promise<(typeof GALLERY_IMAGES)[0] | null>((resolve) => {
                        const image = new Image();
                        image.onload = () => resolve(img);
                        image.onerror = () => resolve(null);
                        image.src = img.src;
                    })
                )
            );
            setAvailable(results.filter(Boolean) as typeof GALLERY_IMAGES);
        };
        check();
    }, []);
    return available;
}

// Typing animation for hero
function useTypingEffect(texts: string[], speed = 60, pause = 2000) {
    const [display, setDisplay] = useState("");
    const [textIndex, setTextIndex] = useState(0);
    const [charIndex, setCharIndex] = useState(0);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        const currentText = texts[textIndex];
        const timeout = setTimeout(() => {
            if (!deleting) {
                if (charIndex < currentText.length) {
                    setDisplay(currentText.slice(0, charIndex + 1));
                    setCharIndex(charIndex + 1);
                } else {
                    setTimeout(() => setDeleting(true), pause);
                }
            } else {
                if (charIndex > 0) {
                    setDisplay(currentText.slice(0, charIndex - 1));
                    setCharIndex(charIndex - 1);
                } else {
                    setDeleting(false);
                    setTextIndex((textIndex + 1) % texts.length);
                }
            }
        }, deleting ? speed / 2 : speed);
        return () => clearTimeout(timeout);
    }, [charIndex, deleting, textIndex, texts, speed, pause]);

    return display;
}

export default function HomePage() {
    const galleryImages = useAvailableImages();
    const [heroLoaded, setHeroLoaded] = useState(false);
    const heroImgRef = useRef<HTMLImageElement>(null);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    // Fix: detect if hero image loaded before React hydrated (browser cache)
    useEffect(() => {
        const img = heroImgRef.current;
        if (img && img.complete && img.naturalHeight > 0) {
            setHeroLoaded(true);
        }
    }, []);

    const typedText = useTypingEffect([
        "A samurai walks through rain-soaked streets...",
        "Two heroes clash above the clouds...",
        "A girl discovers a portal to another world...",
        "The last knight defends the fallen kingdom...",
    ], 45, 2500);

    // Scroll sections
    const pipeline = useScrollReveal();
    const showcase = useScrollReveal();
    const stats = useScrollReveal();
    const architecture = useScrollReveal();
    const cta = useScrollReveal();

    return (
        <div className="min-h-screen bg-[#060d0a] text-white overflow-x-hidden">
            {/* ===== NAVBAR ===== */}
            <nav className="fixed top-0 left-0 right-0 z-50 px-4 sm:px-6 py-3">
                <div className="max-w-7xl mx-auto flex items-center justify-between bg-[#0a150f]/80 backdrop-blur-xl rounded-2xl px-5 py-2.5 border border-white/[0.06] shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
                    <Link href="/" className="flex items-center gap-2.5 group">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#38e07b] to-[#2bb863] flex items-center justify-center shadow-[0_0_20px_-5px_rgba(56,224,123,0.4)] group-hover:shadow-[0_0_25px_-3px_rgba(56,224,123,0.6)] transition-shadow">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#060d0a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                            </svg>
                        </div>
                        <span className="text-white font-bold text-lg tracking-tight">MangaGen<span className="text-[#38e07b]">.AI</span></span>
                    </Link>

                    <div className="hidden md:flex items-center gap-8">
                        <a href="#pipeline" className="text-gray-400 hover:text-white text-sm font-medium transition-colors">Pipeline</a>
                        <a href="#gallery" className="text-gray-400 hover:text-white text-sm font-medium transition-colors">Gallery</a>
                        <a href="#architecture" className="text-gray-400 hover:text-white text-sm font-medium transition-colors">Architecture</a>
                        <Link href="/dashboard" className="text-gray-400 hover:text-white text-sm font-medium transition-colors">Dashboard</Link>
                    </div>

                    <div className="hidden md:flex items-center gap-3">
                        <Link href="/login" className="flex items-center justify-center rounded-xl h-9 px-5 border border-white/10 hover:border-[#38e07b]/30 text-gray-300 hover:text-white text-sm font-medium transition-all hover:bg-white/[0.03]">
                            Sign In
                        </Link>
                        <Link href="/create" className="flex items-center justify-center rounded-xl h-9 px-5 bg-[#38e07b] hover:bg-[#2bc968] text-[#060d0a] text-sm font-bold transition-all shadow-[0_0_15px_rgba(56,224,123,0.25)] hover:shadow-[0_0_25px_rgba(56,224,123,0.45)]">
                            Start Creating
                        </Link>
                    </div>

                    <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden text-white p-2">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            {mobileMenuOpen ? <path d="M18 6L6 18M6 6l12 12" /> : <path d="M4 6h16M4 12h16M4 18h16" />}
                        </svg>
                    </button>
                </div>
                {mobileMenuOpen && (
                    <div className="md:hidden mt-2 bg-[#0a150f]/95 backdrop-blur-xl rounded-2xl border border-white/[0.06] p-4 max-w-7xl mx-auto">
                        <div className="flex flex-col gap-2">
                            <a href="#pipeline" onClick={() => setMobileMenuOpen(false)} className="text-gray-300 hover:text-white px-4 py-2.5 rounded-lg hover:bg-white/5">Pipeline</a>
                            <a href="#gallery" onClick={() => setMobileMenuOpen(false)} className="text-gray-300 hover:text-white px-4 py-2.5 rounded-lg hover:bg-white/5">Gallery</a>
                            <Link href="/dashboard" className="text-gray-300 hover:text-white px-4 py-2.5 rounded-lg hover:bg-white/5">Dashboard</Link>
                            <hr className="border-white/5 my-1" />
                            <Link href="/create" className="flex items-center justify-center rounded-xl py-3 bg-[#38e07b] text-[#060d0a] font-bold">Start Creating</Link>
                        </div>
                    </div>
                )}
            </nav>

            {/* ===== HERO ===== */}
            <section className="relative pt-28 pb-16 md:pt-36 md:pb-24 px-4 sm:px-6">
                {/* BG effects */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-10 left-1/4 w-[600px] h-[600px] bg-[#38e07b]/[0.04] rounded-full blur-[150px]" />
                    <div className="absolute top-32 right-1/4 w-[500px] h-[500px] bg-[#7c3aed]/[0.03] rounded-full blur-[120px]" />
                    <div className="absolute inset-0 opacity-[0.025]" style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`, backgroundSize: '60px 60px' }} />
                </div>

                <div className="max-w-7xl mx-auto relative">
                    <div className="grid md:grid-cols-2 gap-10 md:gap-16 items-center">
                        {/* Left */}
                        <div className="flex flex-col gap-5">
                            <div className="inline-flex items-center gap-2 bg-[#38e07b]/[0.08] border border-[#38e07b]/20 rounded-full px-4 py-1.5 w-fit">
                                <div className="w-2 h-2 rounded-full bg-[#38e07b] animate-pulse" />
                                <span className="text-[#38e07b] text-xs font-semibold uppercase tracking-wider">Open Source • AI Pipeline</span>
                            </div>

                            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black leading-[0.95] tracking-tight">
                                Turn Words
                                <br />
                                <span className="bg-gradient-to-r from-[#38e07b] via-[#4fffaa] to-[#38e07b] bg-clip-text text-transparent">Into Manga</span>
                            </h1>

                            <p className="text-gray-400 text-base sm:text-lg leading-relaxed max-w-lg">
                                End-to-end manga generation pipeline. From a single text prompt to complete manga pages with consistent characters, dynamic layouts, and smart dialogue placement.
                            </p>

                            {/* Typing prompt preview */}
                            <div className="bg-[#0a150f]/80 border border-white/[0.06] rounded-2xl p-4 max-w-lg">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="w-3 h-3 rounded-full bg-red-500/60" />
                                    <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                                    <div className="w-3 h-3 rounded-full bg-green-500/60" />
                                    <span className="text-gray-500 text-xs ml-2 font-mono">story_prompt.txt</span>
                                </div>
                                <p className="text-gray-300 text-sm font-mono h-6">
                                    <span className="text-[#38e07b]">{">"} </span>
                                    {typedText}
                                    <span className="inline-block w-0.5 h-4 bg-[#38e07b] ml-0.5 animate-pulse align-middle" />
                                </p>
                            </div>

                            <div className="flex flex-wrap gap-3 mt-1">
                                <Link href="/create" className="flex h-13 items-center justify-center rounded-2xl px-8 bg-[#38e07b] hover:bg-[#2bc968] text-[#060d0a] text-base font-bold transition-all shadow-[0_0_25px_rgba(56,224,123,0.3)] hover:shadow-[0_0_35px_rgba(56,224,123,0.5)] hover:-translate-y-0.5 active:translate-y-0 group">
                                    Start Creating
                                    <svg className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
                                </Link>
                                <a href="#gallery" className="flex h-13 items-center justify-center rounded-2xl px-8 bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 hover:border-white/20 text-white text-base font-medium transition-all backdrop-blur-sm">
                                    View Gallery
                                </a>
                            </div>

                            {/* Tech stack */}
                            <div className="flex flex-wrap items-center gap-2.5 mt-2">
                                {["Python", "FastAPI", "Next.js", "Multi-LLM", "MongoDB"].map((tech) => (
                                    <span key={tech} className="text-[11px] px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.06] text-gray-500 font-medium">{tech}</span>
                                ))}
                            </div>
                        </div>

                        {/* Right — Hero Image Collage */}
                        <div className="relative flex justify-center md:justify-end">
                            <div className="relative w-[340px] sm:w-[400px] md:w-[440px]">
                                {/* Main hero image */}
                                <div className="relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl shadow-black/50 bg-[#0a150f] aspect-[3/4]">
                                    <div className="absolute -inset-6 bg-gradient-to-br from-[#38e07b]/20 via-transparent to-[#7c3aed]/10 rounded-3xl blur-3xl opacity-50" />
                                    <img
                                        ref={heroImgRef}
                                        src="/gallery/hero-manga.png"
                                        alt="AI Generated Manga Cover"
                                        className={`relative w-full h-full object-cover transition-all duration-700 ${heroLoaded ? 'opacity-100 scale-100' : 'opacity-0 scale-105'}`}
                                        onLoad={() => setHeroLoaded(true)}
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-[#060d0a]/90 via-transparent to-[#060d0a]/20" />
                                    <div className="absolute bottom-4 left-4 right-4">
                                        <div className="flex items-center gap-2 bg-black/60 backdrop-blur-md rounded-xl px-4 py-2.5 border border-white/10">
                                            <div className="w-2 h-2 rounded-full bg-[#38e07b]" />
                                            <span className="text-white text-sm font-medium">AI Generated • Full Pipeline Output</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Floating side thumbnails */}
                                <div className="absolute -left-10 top-16 w-20 h-28 rounded-xl overflow-hidden border border-white/10 shadow-xl animate-float-slow hidden md:block">
                                    <img src="/gallery/neontech.png" alt="" className="w-full h-full object-cover" />
                                </div>
                                <div className="absolute -right-8 top-1/3 w-20 h-28 rounded-xl overflow-hidden border border-white/10 shadow-xl animate-float-delayed hidden md:block">
                                    <img src="/gallery/Samurai.png" alt="" className="w-full h-full object-cover" />
                                </div>

                                {/* Floating stat badge */}
                                <div className="absolute -left-6 bottom-20 bg-[#0f1f17]/95 backdrop-blur-xl rounded-xl p-3 border border-[#38e07b]/20 shadow-xl animate-float-slow hidden md:block">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xl">⚡</span>
                                        <div>
                                            <p className="text-white text-xs font-bold">15+ Layouts</p>
                                            <p className="text-gray-500 text-[10px]">AI-selected per scene</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ===== PIPELINE — HOW IT WORKS ===== */}
            <section id="pipeline" ref={pipeline.ref} className={`py-20 md:py-28 px-4 sm:px-6 transition-all duration-1000 ${pipeline.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <span className="text-[#38e07b] text-sm font-bold uppercase tracking-widest">The Pipeline</span>
                        <h2 className="text-3xl sm:text-4xl md:text-5xl font-black mt-3 tracking-tight">From Prompt to Manga in <span className="text-[#38e07b]">3 Steps</span></h2>
                        <p className="text-gray-400 mt-4 max-w-2xl mx-auto text-base sm:text-lg">Write your story. The AI handles everything else — planning, art, layout, dialogue.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-5">
                        {[
                            {
                                step: "01", title: "Describe Your Story", image: "/gallery/step-describe.png",
                                desc: "Write your story prompt. Define characters with appearances, set the tone, pick your art style — B&W manga or color anime.",
                                color: "from-[#38e07b]/10 to-transparent"
                            },
                            {
                                step: "02", title: "AI Generates Everything", image: "/gallery/step-generate.png",
                                desc: "The pipeline breaks your script into panels, maintains character consistency across pages, selects optimal layouts, and renders every image.",
                                color: "from-[#7c3aed]/10 to-transparent"
                            },
                            {
                                step: "03", title: "Edit & Export", image: "/gallery/step-publish.png",
                                desc: "Fine-tune dialogue bubbles, adjust panel compositions, regenerate any panel, then export as high-quality PDF or individual PNGs.",
                                color: "from-[#38e07b]/10 to-transparent"
                            },
                        ].map((item, i) => (
                            <div key={item.step} className="group relative bg-[#0a150f]/60 backdrop-blur-md border border-white/[0.06] rounded-2xl overflow-hidden hover:border-[#38e07b]/20 transition-all duration-500 hover:-translate-y-1" style={{ transitionDelay: `${i * 100}ms` }}>
                                {/* Step image */}
                                <div className="relative h-48 overflow-hidden">
                                    <div className={`absolute inset-0 bg-gradient-to-b ${item.color}`} />
                                    <img src={item.image} alt={item.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
                                    <div className="absolute inset-0 bg-gradient-to-t from-[#0a150f] via-[#0a150f]/50 to-transparent" />
                                    <div className="absolute top-4 left-4 text-[#38e07b]/20 text-5xl font-black">{item.step}</div>
                                </div>
                                <div className="p-6">
                                    <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                                    <p className="text-gray-400 text-sm leading-relaxed">{item.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ===== STATS ===== */}
            <section ref={stats.ref} className={`py-16 px-4 sm:px-6 transition-all duration-1000 ${stats.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
                <div className="max-w-5xl mx-auto">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                            { value: "15+", label: "Panel Layouts", desc: "AI picks per scene" },
                            { value: "5", label: "LLM Providers", desc: "Auto-fallback chain" },
                            { value: "∞", label: "Continuation", desc: "Extend any chapter" },
                            { value: "PDF", label: "Export Ready", desc: "Print-quality output" },
                        ].map((stat, i) => (
                            <div key={stat.label} className="bg-gradient-to-br from-[#0f1a14] to-[#0a150f] border border-white/[0.06] rounded-2xl p-6 text-center hover:border-[#38e07b]/20 transition-all group" style={{ transitionDelay: `${i * 80}ms` }}>
                                <div className="text-3xl md:text-4xl font-black bg-gradient-to-br from-[#38e07b] to-[#4fffaa] bg-clip-text text-transparent group-hover:scale-110 transition-transform inline-block">{stat.value}</div>
                                <div className="text-white font-semibold text-sm mt-2">{stat.label}</div>
                                <div className="text-gray-500 text-xs mt-0.5">{stat.desc}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ===== GALLERY ===== */}
            <section id="gallery" ref={showcase.ref} className={`py-20 md:py-28 px-4 sm:px-6 transition-all duration-1000 ${showcase.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
                <div className="max-w-7xl mx-auto">
                    <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4 mb-12">
                        <div>
                            <span className="text-[#38e07b] text-sm font-bold uppercase tracking-widest">Showcase</span>
                            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black mt-3 tracking-tight">Made With MangaGen</h2>
                            <p className="text-gray-400 mt-3 text-base sm:text-lg">Every image below was generated by our AI pipeline.</p>
                        </div>
                        <Link href="/create" className="hidden sm:flex items-center gap-2 text-[#38e07b] hover:text-[#4fffaa] font-semibold transition-colors group whitespace-nowrap">
                            Create yours <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" /></svg>
                        </Link>
                    </div>

                    {galleryImages.length > 0 ? (
                        <div className="columns-2 md:columns-3 lg:columns-4 gap-3 sm:gap-4 space-y-3 sm:space-y-4">
                            {galleryImages.map((img, i) => (
                                <div key={i} className="group relative break-inside-avoid rounded-2xl overflow-hidden border border-white/[0.06] hover:border-[#38e07b]/20 transition-all duration-500 bg-[#0a150f]">
                                    <img src={img.src} alt={img.title} className="w-full object-cover transition-transform duration-700 group-hover:scale-[1.03]" loading="lazy" />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
                                        <h3 className="text-white font-bold text-sm">{img.title}</h3>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#38e07b]/20 text-[#38e07b] font-semibold">{img.style}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
                            {[200, 280, 220, 260, 240, 200, 280, 240].map((h, i) => (
                                <div key={i} className="break-inside-avoid rounded-2xl bg-[#0a150f] border border-white/[0.04] animate-pulse" style={{ height: `${h}px` }} />
                            ))}
                        </div>
                    )}
                </div>
            </section>

            {/* ===== ARCHITECTURE ===== */}
            <section id="architecture" ref={architecture.ref} className={`py-20 md:py-28 px-4 sm:px-6 transition-all duration-1000 ${architecture.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
                <div className="max-w-5xl mx-auto">
                    <div className="text-center mb-12">
                        <span className="text-[#38e07b] text-sm font-bold uppercase tracking-widest">Under The Hood</span>
                        <h2 className="text-3xl sm:text-4xl md:text-5xl font-black mt-3 tracking-tight">The Pipeline Architecture</h2>
                        <p className="text-gray-400 mt-4 max-w-2xl mx-auto text-base sm:text-lg">A multi-stage AI pipeline where each component specializes in one task.</p>
                    </div>

                    {/* Architecture diagram */}
                    <div className="relative bg-[#0a150f]/80 border border-white/[0.06] rounded-3xl p-6 sm:p-10 overflow-hidden">
                        <div className="absolute inset-0 opacity-[0.015]" style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)`, backgroundSize: '30px 30px' }} />

                        <div className="relative flex flex-col gap-4">
                            {[
                                { label: "📝 Story Director", desc: "Multi-LLM story planning with 5-provider fallback chain", badges: ["Groq", "OpenRouter", "Cerebras", "SambaNova", "Gemini"] },
                                { label: "🎨 Image Factory", desc: "Panel rendering with multiple art engines and style consistency", badges: ["Pollinations", "Z-Image", "Flux Dev", "Flux Schnell"] },
                                { label: "📐 Layout Engine", desc: "15+ manga page templates selected by AI based on scene archetype", badges: ["Dynamic", "2x2 Grid", "2x3 Grid", "Full Bleed", "Custom"] },
                                { label: "💬 Dialogue Placer", desc: "Smart bubble positioning with multiple styles and font control", badges: ["Speech", "Thought", "Shout", "Narrator", "Whisper"] },
                                { label: "📄 PDF Composer", desc: "Print-quality PDF assembly with proper bleed and margins", badges: ["PDF Export", "PNG Export", "Multi-page"] },
                            ].map((stage, i) => (
                                <div key={i} className="flex flex-col sm:flex-row gap-4 items-start sm:items-center bg-[#0f1a14]/60 border border-white/[0.06] rounded-xl p-4 sm:p-5 hover:border-[#38e07b]/20 transition-colors group">
                                    <div className="flex-1 min-w-0">
                                        <h4 className="text-base font-bold text-white group-hover:text-[#38e07b] transition-colors">{stage.label}</h4>
                                        <p className="text-gray-400 text-sm mt-1">{stage.desc}</p>
                                    </div>
                                    <div className="flex flex-wrap gap-1.5 shrink-0">
                                        {stage.badges.map((b) => (
                                            <span key={b} className="text-[10px] px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.06] text-gray-400 font-medium whitespace-nowrap">{b}</span>
                                        ))}
                                    </div>
                                    {i < 4 && (
                                        <div className="hidden sm:block absolute right-1/2 translate-x-1/2">
                                        </div>
                                    )}
                                </div>
                            ))}
                            {/* Flow arrows between stages */}
                            <div className="absolute left-8 top-14 bottom-14 w-px bg-gradient-to-b from-[#38e07b]/30 via-[#38e07b]/10 to-[#38e07b]/30 hidden sm:block" />
                        </div>
                    </div>
                </div>
            </section>

            {/* ===== CTA ===== */}
            <section ref={cta.ref} className={`py-20 md:py-28 px-4 sm:px-6 transition-all duration-1000 ${cta.isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
                <div className="max-w-4xl mx-auto">
                    <div className="relative rounded-3xl overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-br from-[#0f2418] via-[#0a150f] to-[#0f1a2e]" />
                        <div className="absolute inset-0 opacity-30" style={{ backgroundImage: `radial-gradient(circle at 30% 50%, rgba(56,224,123,0.15), transparent 50%), radial-gradient(circle at 70% 50%, rgba(124,58,237,0.1), transparent 50%)` }} />
                        {/* Hero image accent */}
                        <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-10 hidden md:block">
                            <img src="/gallery/hero-manga.png" alt="" className="w-full h-full object-cover" />
                        </div>
                        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)`, backgroundSize: '40px 40px' }} />

                        <div className="relative px-6 py-14 sm:px-12 md:px-16 md:py-20 text-center md:text-left">
                            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight">Your Story Deserves<br /><span className="text-[#38e07b]">Manga Pages.</span></h2>
                            <p className="text-gray-400 text-base sm:text-lg mt-4 max-w-lg">Turn any story idea into professional manga — no drawing skills needed. The AI pipeline handles everything.</p>
                            <div className="flex flex-col sm:flex-row gap-4 mt-8 justify-center md:justify-start">
                                <Link href="/create" className="inline-flex h-14 items-center justify-center rounded-2xl px-10 bg-[#38e07b] hover:bg-[#2bc968] text-[#060d0a] text-lg font-bold transition-all shadow-[0_0_30px_rgba(56,224,123,0.35)] hover:shadow-[0_0_45px_rgba(56,224,123,0.55)] hover:-translate-y-0.5">
                                    Start Creating <svg className="ml-2 w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
                                </Link>
                                <a href="https://github.com/Barun-2005/manga-gen-ai-pipeline" target="_blank" rel="noopener noreferrer" className="inline-flex h-14 items-center justify-center rounded-2xl px-10 border border-white/10 hover:border-white/20 text-white text-lg font-medium transition-all hover:bg-white/[0.03] gap-2">
                                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg>
                                    View on GitHub
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ===== FOOTER ===== */}
            <footer className="border-t border-white/[0.06] py-10 px-4 sm:px-6">
                <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#38e07b] to-[#2bb863] flex items-center justify-center">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#060d0a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /></svg>
                        </div>
                        <span className="text-white font-bold text-sm">MangaGen<span className="text-[#38e07b]">.AI</span></span>
                    </div>
                    <div className="flex items-center gap-5">
                        <Link href="/create" className="text-gray-500 hover:text-white text-sm transition-colors">Create</Link>
                        <Link href="/dashboard" className="text-gray-500 hover:text-white text-sm transition-colors">Dashboard</Link>
                        <a href="https://github.com/Barun-2005/manga-gen-ai-pipeline" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-white text-sm transition-colors">GitHub</a>
                    </div>
                    <p className="text-gray-600 text-xs">Open Source • AI-Powered • Full Pipeline</p>
                </div>
            </footer>

            <style jsx>{`
        @keyframes float-slow {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        @keyframes float-delayed {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-8px); }
        }
        .animate-float-slow { animation: float-slow 5s ease-in-out infinite; }
        .animate-float-delayed { animation: float-delayed 6s ease-in-out 1.5s infinite; }
      `}</style>
        </div>
    );
}
