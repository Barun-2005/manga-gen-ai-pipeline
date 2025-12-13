"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

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
    const [layout, setLayout] = useState<"2x2" | "2x3" | "full">("2x2");
    const [pageCount, setPageCount] = useState(1);
    const [characters, setCharacters] = useState<Character[]>([
        { id: "1", name: "Akira", role: "Protagonist", appearance: "Spiky blue hair, scar on left cheek. Stoic expression." }
    ]);
    const [isGenerating, setIsGenerating] = useState(false);
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

    const handleGenerate = async () => {
        if (!storyPrompt.trim()) {
            setError("Please enter a story prompt");
            return;
        }

        setIsGenerating(true);
        setError("");

        try {
            // Build prompt with character descriptions
            let fullPrompt = storyPrompt;
            if (characters.length > 0) {
                const charDescs = characters.map(c => `${c.name}: ${c.appearance}`).join(". ");
                fullPrompt = `${storyPrompt}\n\nCharacters: ${charDescs}`;
            }

            const response = await fetch("http://localhost:8000/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    story_prompt: fullPrompt,
                    title: title || "My Manga",
                    style: style,
                    layout: layout,
                    pages: pageCount,
                    characters: characters.map(c => ({
                        name: c.name,
                        appearance: c.appearance,
                        personality: ""
                    }))
                })
            });

            if (!response.ok) {
                throw new Error("Failed to start generation");
            }

            const data = await response.json();
            router.push(`/generate/${data.job_id}`);

        } catch (err) {
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
                                    <button className="text-xs text-[#38e07b] hover:text-white transition-colors flex items-center gap-1">
                                        <span className="material-symbols-outlined text-[14px]">auto_awesome</span> Improve Prompt
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

                    {/* RIGHT COLUMN: Configuration */}
                    <div className="w-[400px] shrink-0 flex flex-col gap-6 overflow-y-auto h-full pb-24 pr-2">
                        {/* Style Selection */}
                        <div className="glass-panel rounded-xl p-5">
                            <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2">
                                <span className="material-symbols-outlined text-[#38e07b] text-[18px]">palette</span> Art Style
                            </h3>
                            <div className="grid grid-cols-2 gap-3">
                                <label className="cursor-pointer relative group">
                                    <input
                                        type="radio"
                                        name="style"
                                        checked={style === "bw_manga"}
                                        onChange={() => setStyle("bw_manga")}
                                        className="peer sr-only"
                                    />
                                    <div className="bg-black/40 rounded-lg overflow-hidden border-2 border-transparent peer-checked:border-[#38e07b] peer-checked:shadow-neon transition-all h-32 relative flex items-center justify-center">
                                        <div className="text-center">
                                            <span className="material-symbols-outlined text-4xl text-white/70 group-hover:text-white transition-colors">contrast</span>
                                            <p className="text-white text-sm mt-2">B&W Manga</p>
                                        </div>
                                        <div className="absolute top-2 right-2 text-[#38e07b] opacity-0 peer-checked:opacity-100 transition-opacity">
                                            <span className="material-symbols-outlined filled">check_circle</span>
                                        </div>
                                    </div>
                                </label>
                                <label className="cursor-pointer relative group">
                                    <input
                                        type="radio"
                                        name="style"
                                        checked={style === "color_anime"}
                                        onChange={() => setStyle("color_anime")}
                                        className="peer sr-only"
                                    />
                                    <div className="bg-black/40 rounded-lg overflow-hidden border-2 border-transparent peer-checked:border-[#38e07b] peer-checked:shadow-neon transition-all h-32 relative flex items-center justify-center">
                                        <div className="text-center">
                                            <span className="material-symbols-outlined text-4xl text-white/70 group-hover:text-white transition-colors">colors</span>
                                            <p className="text-white text-sm mt-2">Color Anime</p>
                                        </div>
                                        <div className="absolute top-2 right-2 text-[#38e07b] opacity-0 peer-checked:opacity-100 transition-opacity">
                                            <span className="material-symbols-outlined filled">check_circle</span>
                                        </div>
                                    </div>
                                </label>
                            </div>
                        </div>

                        {/* Layout Selection */}
                        <div className="glass-panel rounded-xl p-5">
                            <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2">
                                <span className="material-symbols-outlined text-[#38e07b] text-[18px]">grid_view</span> Panel Layout
                            </h3>
                            <div className="grid grid-cols-3 gap-3">
                                {["2x2", "2x3", "full"].map((opt) => (
                                    <label key={opt} className="cursor-pointer group">
                                        <input
                                            type="radio"
                                            name="layout"
                                            checked={layout === opt}
                                            onChange={() => setLayout(opt as typeof layout)}
                                            className="peer sr-only"
                                        />
                                        <div className="aspect-square bg-white/5 rounded-lg border border-white/10 peer-checked:border-[#38e07b] peer-checked:bg-[#38e07b]/10 peer-checked:shadow-neon transition-all flex flex-col items-center justify-center gap-2 group-hover:border-white/30">
                                            <div className={`grid gap-0.5 w-10 h-10 ${opt === "2x2" ? "grid-cols-2" : opt === "2x3" ? "grid-cols-2" : "grid-cols-1"}`}>
                                                {opt === "2x2" && <>
                                                    <div className="bg-white/80 peer-checked:bg-[#38e07b] rounded-sm"></div>
                                                    <div className="bg-white/80 peer-checked:bg-[#38e07b] rounded-sm"></div>
                                                    <div className="bg-white/80 peer-checked:bg-[#38e07b] rounded-sm"></div>
                                                    <div className="bg-white/80 peer-checked:bg-[#38e07b] rounded-sm"></div>
                                                </>}
                                                {opt === "2x3" && <>
                                                    <div className="bg-white/80 rounded-sm h-4"></div>
                                                    <div className="bg-white/80 rounded-sm h-4"></div>
                                                    <div className="bg-white/80 rounded-sm h-3 col-span-2"></div>
                                                    <div className="bg-white/80 rounded-sm h-3 col-span-2"></div>
                                                </>}
                                                {opt === "full" && <div className="bg-white/80 rounded-sm h-full"></div>}
                                            </div>
                                            <span className="text-xs text-white/60 font-medium">{opt === "full" ? "Full Pg" : opt}</span>
                                        </div>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Chapter Settings */}
                        <div className="glass-panel rounded-xl p-5">
                            <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2">
                                <span className="material-symbols-outlined text-[#38e07b] text-[18px]">settings_suggest</span> Chapter Details
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs text-white/50 mb-1 block">Chapter Title</label>
                                    <input
                                        className="w-full bg-black/20 border-b border-white/10 text-white py-2 px-1 focus:outline-none focus:border-[#38e07b] transition-colors text-sm font-medium placeholder:text-white/20"
                                        placeholder="e.g. The Awakening"
                                        type="text"
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                    />
                                </div>
                                <div className="flex items-center justify-between">
                                    <label className="text-xs text-white/50">Page Count</label>
                                    <div className="flex items-center bg-black/30 rounded-lg p-1 border border-white/5">
                                        <button
                                            onClick={() => setPageCount(Math.max(1, pageCount - 1))}
                                            className="w-8 h-8 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 rounded-md transition-colors"
                                        >
                                            <span className="material-symbols-outlined text-[16px]">remove</span>
                                        </button>
                                        <span className="w-8 text-center text-white font-mono text-sm">{pageCount}</span>
                                        <button
                                            onClick={() => setPageCount(Math.min(10, pageCount + 1))}
                                            className="w-8 h-8 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 rounded-md transition-colors"
                                        >
                                            <span className="material-symbols-outlined text-[16px]">add</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Generate Button */}
                        <div className="mt-auto pt-4">
                            {error && (
                                <div className="mb-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                    {error}
                                </div>
                            )}
                            <div className="flex items-center justify-between mb-3 px-1">
                                <div className="flex items-center gap-1.5 text-white/70 text-xs font-medium">
                                    <span className="material-symbols-outlined text-[#38e07b] text-[16px]">bolt</span>
                                    Powered by <span className="text-white font-bold">Pollinations.ai</span>
                                </div>
                                <div className="text-xs text-white/40">Free • No API Key</div>
                            </div>
                            <button
                                onClick={handleGenerate}
                                disabled={isGenerating}
                                className="w-full group relative overflow-hidden rounded-full bg-[#38e07b] p-0.5 transition-all hover:shadow-neon-hover disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <div className="absolute inset-0 bg-gradient-to-r from-[#38e07b] via-[#6effa8] to-[#38e07b] opacity-80 group-hover:opacity-100 transition-opacity"></div>
                                <div className="relative flex h-12 w-full items-center justify-center gap-2 rounded-full bg-[#0a110e]/10 backdrop-blur-[2px] px-6 transition-all group-hover:bg-transparent">
                                    <span className="material-symbols-outlined text-black font-bold">
                                        {isGenerating ? "hourglass_empty" : "auto_fix_high"}
                                    </span>
                                    <span className="text-black text-base font-bold tracking-wide">
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
