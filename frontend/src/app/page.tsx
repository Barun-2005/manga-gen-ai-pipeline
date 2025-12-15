"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

// Hero prompts for variety
const HERO_PROMPTS = [
  "epic manga hero silhouette, dramatic sky, action pose, sunset",
  "anime girl with sword, cherry blossoms, dynamic pose, dramatic",
  "cyberpunk samurai, neon city, rain, reflections, dramatic",
  "dragon knight battle, flames, epic fantasy, dramatic lighting",
  "mysterious anime character, moonlight, dramatic shadows",
  "ninja in action, smoke effects, dynamic movement, night",
  "mecha pilot, cockpit, intense expression, sci-fi battle",
  "witch casting spell, magical particles, forest, mystical",
];

// Style variations to make each image unique
const STYLE_VARIATIONS = [
  "soft glow lighting, ethereal atmosphere",
  "hard shadows, cinematic contrast",
  "vibrant colors, dynamic composition",
  "moody atmosphere, muted tones",
  "golden hour lighting, warm tones",
  "cool blue tones, mysterious vibe",
  "high contrast, dramatic shadows",
  "pastel colors, dreamy aesthetic",
  "neon accents, cyberpunk style",
  "traditional ink style, high detail",
];

// Generate Pollinations URL - 768x768 (Safe middle ground)
const getPollinationsUrl = (prompt: string, seed?: number, attempt: number = 0) => {
  // Deterministically pick a style based on the seed
  const styleIndex = seed ? seed % STYLE_VARIATIONS.length : 0;
  const style = STYLE_VARIATIONS[styleIndex];

  const fullPrompt = `anime style, high quality, masterpiece, ${prompt}, ${style}`;
  const encodedPrompt = encodeURIComponent(fullPrompt);
  // Change seed slightly on retry to bust cache/errors
  const finalSeed = seed ? seed + attempt : "";
  const seedParam = finalSeed ? `&seed=${finalSeed}` : "";

  // 768x768 is safer for bandwidth/limits than 1024
  return `https://image.pollinations.ai/prompt/${encodedPrompt}?width=768&height=768&nologo=true${seedParam}`;
};

// Gallery showcase images with different styles
// Each has a local anime fallback (guaranteed to work, instant load)
const galleryItems = [
  { title: "Samurai Warrior", prompt: "samurai warrior silhouette, sunset, cherry blossoms, dramatic lighting", genre: "Action", fallback: "/placeholder-1.png" },
  { title: "Neon City", prompt: "cyberpunk girl, neon city, rain, reflections, night scene", genre: "Sci-Fi", fallback: "/placeholder-2.png" },
  { title: "Dragon Knight", prompt: "knight facing dragon, epic battle, flames, fantasy castle", genre: "Fantasy", fallback: "/placeholder-1.png" },
  { title: "School Days", prompt: "anime schoolgirl, sakura trees, spring, peaceful", genre: "Slice of Life", fallback: "/placeholder-2.png" },
  { title: "Dark Forest", prompt: "mysterious figure, dark forest, glowing eyes, horror atmosphere", genre: "Horror", fallback: "/placeholder-1.png" },
  { title: "First Love", prompt: "anime couple, umbrella, rain, romantic city lights", genre: "Romance", fallback: "/placeholder-2.png" },
  { title: "Space Explorer", prompt: "astronaut anime character, space station, stars, sci-fi", genre: "Sci-Fi", fallback: "/placeholder-1.png" },
  { title: "Sword Master", prompt: "swordsman, mountain dojo, sunrise, training stance", genre: "Action", fallback: "/placeholder-2.png" },
];

// Image component with loading state, error handling, and SMART RETRY
const DynamicImage = ({
  src,
  alt,
  className,
  fallbackSrc = "/hero-placeholder.png",
  onLoadComplete,
  maxRetries = 3
}: {
  src: string;
  alt: string;
  className?: string;
  fallbackSrc?: string;
  onLoadComplete?: () => void;
  maxRetries?: number;
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [currentSrc, setCurrentSrc] = useState(src);

  useEffect(() => {
    setIsLoaded(false);
    setHasError(false);
    setRetryCount(0);
    setCurrentSrc(src);
  }, [src]);

  const handleRetry = () => {
    if (retryCount < maxRetries) {
      console.log(`Retrying image ${alt} (${retryCount + 1}/${maxRetries})...`);
      setRetryCount(prev => prev + 1);
      // Add a timestamp to force browser to re-fetch
      setCurrentSrc(`${src}&retry=${Date.now()}`);
    } else {
      setHasError(true);
      setIsLoaded(true);
    }
  };

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {/* Static Placeholder */}
      <img
        src={fallbackSrc}
        alt="Placeholder"
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Main Image */}
      <img
        src={hasError ? fallbackSrc : currentSrc}
        alt={alt}
        className={`relative z-10 w-full h-full object-cover transition-opacity duration-700 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
        onLoad={() => { setIsLoaded(true); onLoadComplete?.(); }}
        onError={(e) => {
          console.error(`DynamicImage failed for ${currentSrc}:`, e);
          // Try to retry before showing error
          setTimeout(handleRetry, 2000 * (retryCount + 1)); // Backoff: 2s, 4s, 6s
        }}
      />


      {/* Subtle overlay to blend placeholder during transition */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-black/20 z-20 backdrop-blur-[2px] transition-opacity duration-700" />
      )}

      {/* Error Badge (Debug Indicator) */}
      {hasError && (
        <div className="absolute top-2 right-2 z-30 bg-red-500/80 backdrop-blur px-2 py-1 rounded text-[10px] font-bold text-white shadow-sm" title="Image generation failed, showing fallback">
          FAILED
        </div>
      )}
    </div>
  );
};

export default function Home() {
  // Start with static values to prevent hydration mismatch (Server != Client)
  const [heroSeed, setHeroSeed] = useState(1);
  const [heroPromptIdx, setHeroPromptIdx] = useState(0);
  const [gallerySeed, setGallerySeed] = useState(0); // Static start
  const [isClient, setIsClient] = useState(false); // Track client-side mount

  // Initialize random seeds ONLY on client
  useEffect(() => {
    setIsClient(true);
    setGallerySeed(Date.now()); // Randomize after mount
  }, []);

  // Rotate hero image periodically with different prompts
  useEffect(() => {
    const interval = setInterval(() => {
      setHeroSeed(prev => prev + 1);
      setHeroPromptIdx(prev => (prev + 1) % HERO_PROMPTS.length);
    }, 45000); // Change every 45 seconds
    return () => clearInterval(interval);
  }, []);

  // Refresh gallery images periodically
  useEffect(() => {
    // Only run on client after hydration
    if (!isClient) return;
    const interval = setInterval(() => {
      setGallerySeed(Date.now());
    }, 90000); // Change every 90 seconds
    return () => clearInterval(interval);
  }, [isClient]);

  // Generate unique seed per gallery item
  const getGallerySeed = (index: number) => {
    // If not client yet, return static seed to match server
    if (!isClient) return 1000 + index;
    return (gallerySeed % 10000) + index * 100;
  };

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
                <span className="text-xs font-medium text-[#38e07b] uppercase tracking-wider">Powered by AI</span>
              </div>

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black leading-[1.1] tracking-tight text-white">
                TURN WORDS <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#38e07b] via-white to-[#38e07b] bg-[length:200%_auto] animate-[gradient_3s_linear_infinite]">INTO WORLDS</span>
              </h1>

              <p className="text-gray-400 text-lg sm:text-xl leading-relaxed max-w-lg mx-auto lg:mx-0">
                Intelligent AI manga generator. Create complete chapters with proper pacing, character development, and meaningful dialogue.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start mt-4">
                <Link href="/create" className="flex h-14 items-center justify-center rounded-full px-8 bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] text-lg font-bold transition-all shadow-[0_0_20px_rgba(56,224,123,0.4)] hover:shadow-[0_0_30px_rgba(56,224,123,0.6)] group">
                  <span className="material-symbols-outlined mr-2 group-hover:translate-x-1 transition-transform">draw</span>
                  Create Your Manga
                </Link>
                <a href="#gallery" className="flex h-14 items-center justify-center rounded-full px-8 bg-[#264532]/30 hover:bg-[#264532]/50 border border-[#264532] text-white text-lg font-bold transition-all backdrop-blur-sm">
                  View Gallery
                </a>
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

            {/* Right Visual - Dynamic Preview */}
            <div className="relative w-full h-full min-h-[400px] lg:min-h-[600px] flex items-center justify-center">
              <div className="relative w-full aspect-[3/4] max-w-md mx-auto">
                {/* Main manga panel - with real AI image */}
                <div className="absolute inset-0 bg-[#16261e] rounded-xl overflow-hidden border border-[#264532] shadow-2xl rotate-3 hover:rotate-0 transition-transform duration-500 z-20 group">
                  <div className="absolute top-4 left-4 right-4 z-10 flex justify-between items-center">
                    <span className="bg-black/70 backdrop-blur text-white text-xs px-2 py-1 rounded">AI Generated</span>
                    <span className="material-symbols-outlined text-[#38e07b] drop-shadow-md">auto_awesome</span>
                  </div>
                  <DynamicImage
                    src={getPollinationsUrl(HERO_PROMPTS[heroPromptIdx], heroSeed)}
                    alt="AI Generated Manga"
                    className="h-full w-full"
                  />
                </div>
                {/* Background cards for depth */}
                <div
                  className="absolute inset-0 rounded-xl border border-[#264532] shadow-xl -rotate-2 scale-95 z-10 translate-x-4 translate-y-4 opacity-60 overflow-hidden"
                  style={{
                    backgroundImage: `url(${getPollinationsUrl("anime character, close-up, dramatic lighting", heroSeed + 1)})`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center'
                  }}
                ></div>
                <div
                  className="absolute inset-0 rounded-xl border border-[#264532] shadow-lg -rotate-6 scale-90 z-0 translate-x-8 translate-y-8 opacity-30 overflow-hidden"
                  style={{
                    backgroundImage: `url(${getPollinationsUrl("anime battle scene, explosion, dynamic", heroSeed + 2)})`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center'
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section - Stitch UI Design */}
      <section id="features" className="py-24 relative overflow-hidden">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-[#38e07b] font-bold tracking-wider uppercase mb-3 text-sm">Workflow</h2>
            <h3 className="text-3xl md:text-5xl font-black text-white mb-6">
              From Idea to Page in <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#38e07b] to-[#7c3aed]">3 Steps</span>
            </h3>
            <p className="text-gray-400 text-lg">Our AI engine handles the complex drawing process, perspective, and shading so you can focus purely on the story.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
            {/* Step 1 - Describe */}
            <div className="glass-card p-8 rounded-2xl relative group hover:-translate-y-2 transition-transform duration-300" style={{ background: 'rgba(26, 44, 34, 0.6)', backdropFilter: 'blur(12px)', border: '1px solid rgba(56, 224, 123, 0.1)' }}>
              <div className="absolute -top-6 left-8 bg-[#1a2c22] border border-[#264532] p-3 rounded-xl shadow-lg group-hover:border-[#38e07b]/50 transition-colors">
                <span className="material-symbols-outlined text-[#38e07b] text-3xl">edit_note</span>
              </div>
              <div className="mt-8">
                <h4 className="text-xl font-bold text-white mb-3">1. Describe</h4>
                <p className="text-gray-400 leading-relaxed mb-6">Type your scene details. Specify characters, poses, camera angles, and atmosphere.</p>
                <div className="bg-[#0f1a14] p-4 rounded-lg border border-[#264532] text-sm text-gray-300 font-mono">
                  <span className="text-[#38e07b]">&gt;</span> /imagine prompt: hero standing on rooftop, rain, cyberpunk city background...
                </div>
              </div>
            </div>

            {/* Step 2 - Generate */}
            <div className="glass-card p-8 rounded-2xl relative group hover:-translate-y-2 transition-transform duration-300" style={{ background: 'rgba(26, 44, 34, 0.6)', backdropFilter: 'blur(12px)', border: '1px solid rgba(56, 224, 123, 0.1)' }}>
              <div className="absolute -top-6 left-8 bg-[#1a2c22] border border-[#264532] p-3 rounded-xl shadow-lg group-hover:border-[#38e07b]/50 transition-colors">
                <span className="material-symbols-outlined text-[#38e07b] text-3xl">auto_fix_high</span>
              </div>
              <div className="mt-8">
                <h4 className="text-xl font-bold text-white mb-3">2. Generate</h4>
                <p className="text-gray-400 leading-relaxed mb-6">Our engine renders high-fidelity line art, screen tones, and speech bubbles instantly.</p>
                <div className="h-24 w-full bg-[#0f1a14] rounded-lg border border-[#264532] relative overflow-hidden">
                  <DynamicImage
                    src={getPollinationsUrl("manga panel being generated, line art, black and white, in progress", 999)}
                    alt="Generating..."
                    className="w-full h-full opacity-50"
                  />
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[#38e07b]/20 to-transparent animate-pulse"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-[#38e07b] text-xs font-bold uppercase tracking-widest animate-pulse drop-shadow-lg">Processing...</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 3 - Publish */}
            <div className="glass-card p-8 rounded-2xl relative group hover:-translate-y-2 transition-transform duration-300" style={{ background: 'rgba(26, 44, 34, 0.6)', backdropFilter: 'blur(12px)', border: '1px solid rgba(56, 224, 123, 0.1)' }}>
              <div className="absolute -top-6 left-8 bg-[#1a2c22] border border-[#264532] p-3 rounded-xl shadow-lg group-hover:border-[#38e07b]/50 transition-colors">
                <span className="material-symbols-outlined text-[#38e07b] text-3xl">download</span>
              </div>
              <div className="mt-8">
                <h4 className="text-xl font-bold text-white mb-3">3. Publish</h4>
                <p className="text-gray-400 leading-relaxed mb-6">Export your pages in 4K resolution, ready for digital publishing or print.</p>
                <button className="w-full py-3 rounded-lg bg-[#38e07b]/10 hover:bg-[#38e07b]/20 text-[#38e07b] border border-[#38e07b]/20 hover:border-[#38e07b] font-bold text-sm transition-all flex items-center justify-center gap-2">
                  <span className="material-symbols-outlined text-lg">file_download</span>
                  Download .PNG
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Gallery Section - Stitch UI Design */}
      <section id="gallery" className="py-24 bg-[#0d1611]">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-end mb-12 gap-6">
            <div>
              <h2 className="text-3xl md:text-4xl font-black text-white mb-2">Made With MangaGen</h2>
              <p className="text-gray-400">Explore creations from our community.</p>
            </div>
            <button className="flex items-center gap-2 text-white hover:text-[#38e07b] font-bold transition-colors">
              View Full Gallery <span className="material-symbols-outlined">arrow_forward</span>
            </button>
          </div>

          {/* Masonry-style Grid - Parallel Loading */}
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {galleryItems.map((item, index) => (
              <div key={index} className="relative group cursor-pointer rounded-xl overflow-hidden">
                <DynamicImage
                  src={getPollinationsUrl(item.prompt, getGallerySeed(index))}
                  alt={item.title}
                  className="w-full aspect-[3/4] transition-transform duration-700 group-hover:scale-105"
                  fallbackSrc={item.fallback}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-6">
                  <span className="text-[#38e07b] text-xs font-bold uppercase mb-1">{item.genre}</span>
                  <p className="text-white text-sm line-clamp-2">&quot;{item.prompt}&quot;</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-b from-[#0d1a15] to-[#0a110e]">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative rounded-3xl overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-[#38e07b]/20 via-[#7c3aed]/10 to-[#38e07b]/20"></div>
            <div className="absolute inset-0 bg-[#16261e]/80"></div>
            <div className="relative p-12 lg:p-20 text-center">
              <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white mb-6">
                Ready to Create?
              </h2>
              <p className="text-gray-300 text-xl max-w-2xl mx-auto mb-10">
                Join thousands of creators using AI to bring their manga stories to life.
              </p>
              <Link href="/create" className="inline-flex h-16 items-center justify-center rounded-full px-12 bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] text-xl font-bold transition-all shadow-[0_0_30px_rgba(56,224,123,0.5)] hover:shadow-[0_0_40px_rgba(56,224,123,0.7)]">
                Start Creating Now
                <span className="material-symbols-outlined ml-2 text-2xl">rocket_launch</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 bg-[#0a110e] border-t border-[#264532]">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#38e07b]">auto_stories</span>
              <span className="text-white font-bold">MangaGen<span className="text-[#38e07b]">.AI</span></span>
            </div>
            <p className="text-gray-500 text-sm">Free AI-powered manga creation. No limits.</p>
            <div className="flex items-center gap-6">
              <Link href="/dashboard" className="text-gray-400 hover:text-white text-sm transition-colors">Dashboard</Link>
              <Link href="/create" className="text-gray-400 hover:text-white text-sm transition-colors">Create</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
