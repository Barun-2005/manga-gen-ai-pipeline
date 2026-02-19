"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { API_URL } from "@/config";

interface Character {
    id: string;
    name: string;
    role: string;
    appearance: string;
}

export default function CreatePage() {
    const router = useRouter();
    const [storyPrompt, setStoryPrompt] = useState("");
    const [title, setTitle] = useState("");
    const [style, setStyle] = useState<"bw_manga" | "color_anime">("bw_manga");
    // V4: "dynamic" lets AI choose layouts based on page archetypes
    const [layout, setLayout] = useState<"dynamic" | "2x2" | "2x3" | "full">("dynamic");
    const [pageCount, setPageCount] = useState(1);
    // DUAL ENGINE: pollinations (cloud), z_image (local), flux_dev (pro), flux_schnell (draft)
    const [engine, setEngine] = useState<"pollinations" | "z_image" | "flux_dev" | "flux_schnell">("pollinations");
    const [characters, setCharacters] = useState<Character[]>([
        { id: "1", name: "Akira", role: "Protagonist", appearance: "Spiky blue hair, scar on left cheek. Stoic expression." }
    ]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [isEnhancing, setIsEnhancing] = useState(false);
    const [error, setError] = useState("");

    const addCharacter = () => {
        const newId = Date.now().toString();
        setCharacters([...characters, { id: newId, name: "", role: "Support", appearance: "" }]);
    };

    const removeCharacter = (id: string) => {
        setCharacters(characters.filter(c => c.id !== id));
    };

    const updateCharacter = (id: string, field: keyof Character, value: string) => {
        setCharacters(characters.map(c => c.id === id ? { ...c, [field]: value } : c));
    };

    const handleEnhancePrompt = async () => {
        if (!storyPrompt.trim()) {
            setError("Enter a prompt first to enhance");
            return;
        }

        setIsEnhancing(true);
        try {
            const response = await fetch(`${API_URL}/api/enhance-prompt`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: storyPrompt })
            });

            if (response.ok) {
                const data = await response.json();
                setStoryPrompt(data.enhanced);
            }
        } catch (err) {
            console.error("Enhance error:", err);
        } finally {
            setIsEnhancing(false);
        }
    };

    const handleGenerate = async () => {
        if (!storyPrompt.trim()) {
            setError("Please enter a story prompt");
            return;
        }

        setIsGenerating(true);
        setError("");

        try {
            // Build prompt
            let fullPrompt = storyPrompt;
            if (characters.length > 0) {
                const charDescs = characters.map(c => `${c.name}: ${c.appearance}`).join(". ");
                fullPrompt = `${storyPrompt}\n\nCharacters: ${charDescs}`;
            }

            console.log("Submitting generation request...");

            // Get API keys from localStorage (BYOK)
            let apiKeys = {};
            const storedKeys = localStorage.getItem("mangagen_api_keys");
            if (storedKeys) {
                try {
                    apiKeys = JSON.parse(storedKeys);
                } catch (e) {
                    console.error("Failed to parse API keys", e);
                }
            }

            const response = await fetch(`${API_URL}/api/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    story_prompt: fullPrompt,
                    title: title || "My Manga",
                    style: style,
                    layout: layout,
                    pages: pageCount,
                    engine: engine,
                    api_keys: apiKeys, // Send keys to backend
                    characters: characters.map(c => ({
                        name: c.name,
                        appearance: c.appearance,
                        personality: ""
                    }))
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Failed to start generation");
            }

            const data = await response.json();
            console.log("Generation success, checking job_id:", data);

            if (!data.job_id) {
                throw new Error("Backend returned no job ID");
            }

            // FORCE HARD REDIRECT - The nuclear option since router.push isn't working for the user
            console.log("Redirecting to:", `/generate/${data.job_id}`);
            window.location.href = `/generate/${data.job_id}`;

        } catch (err) {
            console.error("Generation failed:", err);
            setError(err instanceof Error ? err.message : "Generation failed. Is the backend running?");
            setIsGenerating(false);
        }
    };

    return (
        <div className="relative flex h-screen w-full flex-col overflow-hidden bg-[#0a110e]">
            {/* Header */}
            <header className="z-20 flex items-center justify-between whitespace-nowrap border-b border-white/5 bg-[#0a110e]/80 px-8 py-4 backdrop-blur-md">
                <Link href="/" className="flex items-center gap-4 text-white">
                    <div className="flex size-8 items-center justify-center rounded-lg bg-[#38e07b]/20 text-[#38e07b]">
                        <span className="material-symbols-outlined">auto_stories</span>
                    </div>
                    <h2 className="text-white text-lg font-bold leading-tight tracking-tight">MangaGen<span className="text-[#38e07b]">.AI</span></h2>
                </Link>
                <nav className="hidden md:flex items-center gap-6">
                    <Link className="text-white/70 hover:text-[#38e07b] transition-colors text-sm font-medium" href="/">Home</Link>
                    <span className="text-white text-sm font-medium border-b-2 border-[#38e07b] pb-0.5">Create</span>
                    <Link className="text-white/70 hover:text-[#38e07b] transition-colors text-sm font-medium" href="/dashboard">Library</Link>
                </nav>
            </header>

            {/* Main Content */}
            <main className="flex flex-1 overflow-hidden relative">
                {/* Background decorative glow */}
                <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                    <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-[#38e07b]/5 rounded-full blur-[100px]"></div>
                    <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-[120px]"></div>
                </div>

                <div className="container mx-auto h-full max-w-[1600px] p-6 z-10 flex gap-6">
                    {/* LEFT COLUMN: Story & Characters */}
                    <div className="flex-1 flex flex-col gap-6 overflow-hidden h-full">
                        <div className="flex flex-col gap-1 shrink-0">
                            <h1 className="text-3xl font-bold text-white tracking-tight">Create New Page</h1>
                            <p className="text-white/50 text-sm">Transform your imagination into manga panels.</p>
                        </div>

                        <div className="flex-1 overflow-y-auto pr-2 space-y-6 pb-24">
                            {/* Story Prompt Section */}
                            <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
                                <div className="flex items-center gap-2 text-[#38e07b]">
                                    <span className="material-symbols-outlined text-[20px]">edit_note</span>
                                    <span className="text-sm font-bold uppercase tracking-wider">Story Narrative</span>
                                </div>
                                <textarea
                                    className="w-full bg-black/20 border border-white/10 rounded-xl p-4 text-white placeholder:text-white/20 focus:outline-none focus:border-[#38e07b] focus:ring-1 focus:ring-[#38e07b]/50 transition-all resize-none h-40 leading-relaxed text-lg"
                                    placeholder="Describe the scene, dialogue, and action here. E.g., The hero stands on a cliff edge looking at the sunset, wind blowing through their hair..."
                                    value={storyPrompt}
                                    onChange={(e) => setStoryPrompt(e.target.value)}
                                />
                                <div className="flex justify-between items-center px-1">
                                    <span className="text-xs text-white/30">{storyPrompt.length} characters</span>
                                    <button
                                        onClick={handleEnhancePrompt}
                                        disabled={isEnhancing}
                                        className="text-xs text-[#38e07b] hover:text-white transition-colors flex items-center gap-1 disabled:opacity-50"
                                    >
                                        <span className={`material-symbols-outlined text-[14px] ${isEnhancing ? 'animate-spin' : ''}`}>
                                            {isEnhancing ? 'sync' : 'auto_awesome'}
                                        </span>
                                        {isEnhancing ? 'Enhancing...' : 'Improve Prompt'}
                                    </button>
                                </div>
                            </div>

                            {/* Character Section */}
                            <div className="flex items-center justify-between pt-2">
                                <h3 className="text-white text-lg font-bold">Characters</h3>
                                <button
                                    onClick={addCharacter}
                                    className="text-xs font-bold text-[#38e07b] border border-[#38e07b]/30 bg-[#38e07b]/10 hover:bg-[#38e07b]/20 px-3 py-1.5 rounded-full transition-all flex items-center gap-1"
                                >
                                    <span className="material-symbols-outlined text-[14px]">add</span> Add Character
                                </button>
                            </div>

                            {characters.map((char, idx) => (
                                <div key={char.id} className="glass-panel p-5 rounded-xl border-l-4 border-l-[#38e07b]/50 relative group">
                                    <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                                        <button onClick={() => removeCharacter(char.id)} className="text-white/40 hover:text-white transition-colors">
                                            <span className="material-symbols-outlined text-[18px]">delete</span>
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="col-span-1">
                                            <label className="block text-xs font-medium text-white/50 mb-1.5 uppercase tracking-wide">Name</label>
                                            <input
                                                className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2.5 text-white focus:border-[#38e07b] focus:ring-0 outline-none transition-colors text-sm font-medium"
                                                type="text"
                                                value={char.name}
                                                onChange={(e) => updateCharacter(char.id, "name", e.target.value)}
                                                placeholder="Character name"
                                            />
                                        </div>
                                        <div className="col-span-1">
                                            <label className="block text-xs font-medium text-white/50 mb-1.5 uppercase tracking-wide">Role</label>
                                            <select
                                                className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2.5 text-white focus:border-[#38e07b] focus:ring-0 outline-none transition-colors text-sm"
                                                value={char.role}
                                                onChange={(e) => updateCharacter(char.id, "role", e.target.value)}
                                            >
                                                <option value="Protagonist">Protagonist</option>
                                                <option value="Antagonist">Antagonist</option>
                                                <option value="Support">Support</option>
                                            </select>
                                        </div>
                                        <div className="col-span-1 md:col-span-2">
                                            <label className="block text-xs font-medium text-white/50 mb-1.5 uppercase tracking-wide">Appearance & Personality</label>
                                            <input
                                                className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2.5 text-white/80 focus:border-[#38e07b] focus:ring-0 outline-none transition-colors text-sm"
                                                type="text"
                                                value={char.appearance}
                                                onChange={(e) => updateCharacter(char.id, "appearance", e.target.value)}
                                                placeholder="Spiky blue hair, scar on left cheek, determined expression..."
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* RIGHT COLUMN: Configuration — Compact & Sticky */}
                    <div className="w-[360px] shrink-0 flex flex-col h-full">
                        <div className="flex-1 overflow-y-auto pr-2 space-y-4 pb-4">
                            {/* Art Style — Compact Toggle */}
                            <div className="glass-panel rounded-xl p-4">
                                <h3 className="text-white text-xs font-bold uppercase tracking-wider mb-3 flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[#38e07b] text-[16px]">palette</span> Art Style
                                </h3>
                                <div className="grid grid-cols-2 gap-2">
                                    <label className="cursor-pointer">
                                        <input type="radio" name="style" checked={style === "bw_manga"} onChange={() => setStyle("bw_manga")} className="peer sr-only" />
                                        <div className="rounded-lg overflow-hidden border-2 border-transparent peer-checked:border-[#38e07b] peer-checked:shadow-neon transition-all h-32 relative">
                                            <img src="/gallery/style-bw.png" alt="B&W Manga" className="w-full h-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900" style={{ zIndex: -1 }}><span className="text-xl font-black text-white/20">B&W</span></div>
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent flex items-end p-2">
                                                <p className="text-white text-xs font-bold">B&W Manga</p>
                                            </div>
                                            <div className="absolute top-1.5 right-1.5 text-[#38e07b] opacity-0 peer-checked:opacity-100 transition-opacity">
                                                <span className="material-symbols-outlined filled text-[18px]">check_circle</span>
                                            </div>
                                        </div>
                                    </label>
                                    <label className="cursor-pointer">
                                        <input type="radio" name="style" checked={style === "color_anime"} onChange={() => setStyle("color_anime")} className="peer sr-only" />
                                        <div className="rounded-lg overflow-hidden border-2 border-transparent peer-checked:border-[#38e07b] peer-checked:shadow-neon transition-all h-32 relative">
                                            <img src="/gallery/style-color.png" alt="Color Anime" className="w-full h-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-indigo-900 to-purple-900" style={{ zIndex: -1 }}><span className="text-xl font-black text-white/20">Color</span></div>
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent flex items-end p-2">
                                                <p className="text-white text-xs font-bold">Color Anime</p>
                                            </div>
                                            <div className="absolute top-1.5 right-1.5 text-[#38e07b] opacity-0 peer-checked:opacity-100 transition-opacity">
                                                <span className="material-symbols-outlined filled text-[18px]">check_circle</span>
                                            </div>
                                        </div>
                                    </label>
                                </div>
                            </div>

                            {/* Engine Selection — Compact Rows */}
                            <div className="glass-panel rounded-xl p-4">
                                <h3 className="text-white text-xs font-bold uppercase tracking-wider mb-3 flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[#38e07b] text-[16px]">memory</span> Generation Engine
                                </h3>
                                <div className="space-y-1.5">
                                    {([
                                        { value: "pollinations" as const, label: "Cloud", badge: "Pollinations", badgeColor: "bg-green-500/20 text-green-300", desc: "Free • ~30s/page", icon: "cloud", type: "cloud" },
                                        { value: "z_image" as const, label: "Standard", badge: "Z-Image", badgeColor: "bg-white/10 text-white/70", desc: "B&W Focus • ~60s/page", icon: "image", type: "local" },
                                        { value: "flux_dev" as const, label: "Pro", badge: "Flux Dev", badgeColor: "bg-purple-500/20 text-purple-300", desc: "High Fidelity • ~120s/page", icon: "auto_awesome", type: "local" },
                                        { value: "flux_schnell" as const, label: "Draft", badge: "Flux Schnell", badgeColor: "bg-orange-500/20 text-orange-300", desc: "Fast Preview • ~35s/page", icon: "bolt", type: "local" },
                                    ]).map((eng) => (
                                        <label key={eng.value} className="cursor-pointer block">
                                            <input type="radio" name="engine" checked={engine === eng.value} onChange={() => setEngine(eng.value)} className="peer sr-only" />
                                            <div className="flex items-center gap-3 rounded-lg px-3 py-2.5 border border-transparent peer-checked:border-[#38e07b] peer-checked:bg-[#38e07b]/10 hover:bg-white/[0.03] transition-all">
                                                <span className="material-symbols-outlined text-white/50 peer-checked:text-[#38e07b] text-[18px]">{eng.icon}</span>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-1.5">
                                                        <span className="text-white text-sm font-semibold">{eng.label}</span>
                                                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${eng.badgeColor}`}>{eng.badge}</span>
                                                        {eng.type === "local" && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 font-medium">Local</span>}
                                                    </div>
                                                    <p className="text-white/40 text-[11px]">{eng.desc}</p>
                                                </div>
                                                <div className="text-[#38e07b] opacity-0 peer-checked:opacity-100 transition-opacity shrink-0">
                                                    <span className="material-symbols-outlined filled text-[16px]">check_circle</span>
                                                </div>
                                            </div>
                                        </label>
                                    ))}
                                </div>

                                {/* Info banner for local engines */}
                                {(engine === "z_image" || engine === "flux_dev" || engine === "flux_schnell") && (
                                    <div className="mt-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-start gap-2">
                                        <span className="material-symbols-outlined text-amber-400 text-[16px] mt-0.5 shrink-0">info</span>
                                        <p className="text-amber-300/80 text-[11px] leading-relaxed">
                                            {engine === "z_image"
                                                ? "This engine runs locally via the MangaGen backend. Not available on the hosted demo."
                                                : "Requires ComfyUI running locally with Flux models. Not available on the hosted version."
                                            }
                                            <br />
                                            <button onClick={() => setEngine("pollinations")} className="text-amber-300 underline hover:text-amber-200 mt-1 inline-block">Switch to Cloud (free) →</button>
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* Layout + Chapter — Combined Card */}
                            <div className="glass-panel rounded-xl p-4 space-y-4">
                                {/* Panel Layout */}
                                <div>
                                    <h3 className="text-white text-xs font-bold uppercase tracking-wider mb-3 flex items-center gap-2">
                                        <span className="material-symbols-outlined text-[#38e07b] text-[16px]">grid_view</span> Panel Layout
                                    </h3>
                                    <div className="grid grid-cols-4 gap-2">
                                        <label className="cursor-pointer group">
                                            <input type="radio" name="layout" checked={layout === "dynamic"} onChange={() => setLayout("dynamic")} className="peer sr-only" />
                                            <div className="aspect-square bg-white/5 rounded-lg border border-white/10 peer-checked:border-[#38e07b] peer-checked:bg-[#38e07b]/10 transition-all flex flex-col items-center justify-center gap-1.5 group-hover:border-white/30">
                                                <span className="material-symbols-outlined text-white/70 text-xl">auto_awesome</span>
                                                <span className="text-[10px] text-white/50 font-medium">AI</span>
                                            </div>
                                        </label>
                                        {(["2x2", "2x3", "full"] as const).map((opt) => (
                                            <label key={opt} className="cursor-pointer group">
                                                <input type="radio" name="layout" checked={layout === opt} onChange={() => setLayout(opt)} className="peer sr-only" />
                                                <div className="aspect-square bg-white/5 rounded-lg border border-white/10 peer-checked:border-[#38e07b] peer-checked:bg-[#38e07b]/10 transition-all flex flex-col items-center justify-center gap-1.5 group-hover:border-white/30">
                                                    <div className={`grid gap-0.5 w-8 h-8 ${opt === "2x2" ? "grid-cols-2" : opt === "2x3" ? "grid-cols-2" : "grid-cols-1"}`}>
                                                        {opt === "2x2" && <>{[0, 1, 2, 3].map(i => <div key={i} className="bg-white/60 rounded-sm" />)}</>}
                                                        {opt === "2x3" && <><div className="bg-white/60 rounded-sm h-3" /><div className="bg-white/60 rounded-sm h-3" /><div className="bg-white/60 rounded-sm h-2.5 col-span-2" /><div className="bg-white/60 rounded-sm h-2.5 col-span-2" /></>}
                                                        {opt === "full" && <div className="bg-white/60 rounded-sm h-full" />}
                                                    </div>
                                                    <span className="text-[10px] text-white/50 font-medium">{opt === "full" ? "Full" : opt}</span>
                                                </div>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <div className="h-px bg-white/5" />

                                {/* Chapter Details — Inline */}
                                <div>
                                    <h3 className="text-white text-xs font-bold uppercase tracking-wider mb-3 flex items-center gap-2">
                                        <span className="material-symbols-outlined text-[#38e07b] text-[16px]">menu_book</span> Chapter
                                    </h3>
                                    <div className="space-y-3">
                                        <input
                                            className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-[#38e07b] focus:ring-0 outline-none transition-colors text-sm placeholder:text-white/20"
                                            placeholder="Chapter title (e.g. The Awakening)"
                                            type="text"
                                            value={title}
                                            onChange={(e) => setTitle(e.target.value)}
                                        />
                                        <div className="flex items-center justify-between">
                                            <span className="text-xs text-white/50">Pages</span>
                                            <div className="flex items-center bg-black/30 rounded-lg p-0.5 border border-white/5">
                                                <button onClick={() => setPageCount(Math.max(1, pageCount - 1))} className="w-7 h-7 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 rounded-md transition-colors">
                                                    <span className="material-symbols-outlined text-[14px]">remove</span>
                                                </button>
                                                <span className="w-7 text-center text-white font-mono text-sm">{pageCount}</span>
                                                <button onClick={() => setPageCount(Math.min(10, pageCount + 1))} className="w-7 h-7 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 rounded-md transition-colors">
                                                    <span className="material-symbols-outlined text-[14px]">add</span>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Sticky Generate Footer */}
                        <div className="shrink-0 pt-3 pb-2 border-t border-white/5 bg-[#0a110e]">
                            {error && (
                                <div className="mb-2 p-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs">
                                    {error}
                                </div>
                            )}
                            <div className="flex items-center justify-between mb-2 px-1">
                                <div className="flex items-center gap-1.5 text-white/60 text-[11px] font-medium">
                                    <span className="material-symbols-outlined text-[#38e07b] text-[14px]">{engine === "pollinations" ? "cloud" : engine.startsWith("flux") ? "auto_awesome" : "memory"}</span>
                                    {engine === "pollinations" ? "Cloud (Pollinations)" : engine === "z_image" ? "Local (Z-Image)" : engine === "flux_dev" ? "Pro (Flux Dev)" : "Draft (Flux Schnell)"}
                                </div>
                                <span className="text-[11px] text-white/30">{engine === "pollinations" ? "~30s/page" : engine === "z_image" ? "~60s/page" : engine === "flux_dev" ? "~120s/page" : "~35s/page"}</span>
                            </div>
                            <button
                                onClick={handleGenerate}
                                disabled={isGenerating}
                                className="w-full group relative overflow-hidden rounded-full bg-[#38e07b] p-0.5 transition-all hover:shadow-neon-hover disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <div className="absolute inset-0 bg-gradient-to-r from-[#38e07b] via-[#6effa8] to-[#38e07b] opacity-80 group-hover:opacity-100 transition-opacity"></div>
                                <div className="relative flex h-11 w-full items-center justify-center gap-2 rounded-full bg-[#0a110e]/10 backdrop-blur-[2px] px-6 transition-all group-hover:bg-transparent">
                                    <span className="material-symbols-outlined text-black font-bold">
                                        {isGenerating ? "hourglass_empty" : "auto_fix_high"}
                                    </span>
                                    <span className="text-black text-sm font-bold tracking-wide">
                                        {isGenerating ? "GENERATING..." : "GENERATE MANGA"}
                                    </span>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
