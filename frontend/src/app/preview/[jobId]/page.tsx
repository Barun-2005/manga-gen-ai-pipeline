"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import DialogueLayer, { BubbleData } from "@/components/DialogueLayer";

interface DialogueBubble {
    id: string;
    text: string;
    x: number;  // Percentage
    y: number;  // Percentage
    style: "speech" | "thought" | "shout" | "narrator";
    character?: string;
}

interface Panel {
    id: string;
    bounds: { x: number; y: number; width: number; height: number };
    imageUrl: string;
    prompt?: string;
    dialogues: DialogueBubble[];
}

interface PageData {
    page_number: number;
    page_image: string;
    panels?: Panel[];
}

interface JobStatus {
    job_id: string;
    status: string;
    result?: {
        title: string;
        pages: PageData[];
        pdf: string;
        elapsed_seconds: number;
    };
}

// Bubble style options
const BUBBLE_STYLES = [
    { id: "speech", icon: "chat_bubble", label: "Speech" },
    { id: "thought", icon: "cloud", label: "Thought" },
    { id: "shout", icon: "campaign", label: "Shout" },
    { id: "narrator", icon: "article", label: "Narrator" },
];

export default function PreviewPage() {
    const params = useParams();
    const jobId = params.jobId as string;
    const canvasRef = useRef<HTMLDivElement>(null);

    const [job, setJob] = useState<JobStatus | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [zoom, setZoom] = useState(85);
    const [selectedPanel, setSelectedPanel] = useState<number | null>(null);
    const [selectedBubble, setSelectedBubble] = useState<string | null>(null);
    const [editingText, setEditingText] = useState("");
    const [bubbleStyle, setBubbleStyle] = useState<string>("speech");
    const [fontSize, setFontSize] = useState(14);
    const [regenerating, setRegenerating] = useState(false);
    const [showExportMenu, setShowExportMenu] = useState(false);

    // Dialogues state: Map of panelId -> BubbleData[]
    const [panelDialogues, setPanelDialogues] = useState<Record<string, BubbleData[]>>({});

    // Handle dialogue updates from the canvas
    const handleDialoguesChange = (panelId: string, dialogues: BubbleData[]) => {
        setPanelDialogues(prev => ({ ...prev, [panelId]: dialogues }));
    };

    // Get the currently selected bubble data
    const getSelectedBubbleData = () => {
        if (!selectedBubble || selectedPanel === null) return null;
        const panelId = `page-${currentPage}-panel-${selectedPanel}`;
        const dialogues = panelDialogues[panelId] || [];
        return dialogues.find(b => b.id === selectedBubble);
    };

    // Update selected bubble's style
    const updateBubbleStyle = (newStyle: string) => {
        if (!selectedBubble || selectedPanel === null) return;
        const panelId = `page-${currentPage}-panel-${selectedPanel}`;
        const dialogues = panelDialogues[panelId] || [];
        const updated = dialogues.map(b =>
            b.id === selectedBubble ? { ...b, style: newStyle as BubbleData["style"] } : b
        );
        handleDialoguesChange(panelId, updated);
        setBubbleStyle(newStyle);
    };

    // Update selected bubble's font size
    const updateBubbleFontSize = (delta: number) => {
        if (!selectedBubble || selectedPanel === null) return;
        const panelId = `page-${currentPage}-panel-${selectedPanel}`;
        const dialogues = panelDialogues[panelId] || [];
        const newSize = Math.max(8, Math.min(32, fontSize + delta));
        const updated = dialogues.map(b =>
            b.id === selectedBubble ? { ...b, fontSize: newSize } : b
        );
        handleDialoguesChange(panelId, updated);
        setFontSize(newSize);
    };

    // Delete selected bubble
    const deleteSelectedBubble = () => {
        if (!selectedBubble || selectedPanel === null) return;
        const panelId = `page-${currentPage}-panel-${selectedPanel}`;
        const dialogues = panelDialogues[panelId] || [];
        const updated = dialogues.filter(b => b.id !== selectedBubble);
        handleDialoguesChange(panelId, updated);
        setSelectedBubble(null);
    };

    // Handle bubble selection from canvas (sync sidebar)
    const handleBubbleSelection = (bubbleId: string | null) => {
        setSelectedBubble(bubbleId);
        if (bubbleId && selectedPanel !== null) {
            const panelId = `page-${currentPage}-panel-${selectedPanel}`;
            const dialogues = panelDialogues[panelId] || [];
            const bubble = dialogues.find(b => b.id === bubbleId);
            if (bubble) {
                setEditingText(bubble.text);
                setBubbleStyle(bubble.style);
                setFontSize(bubble.fontSize || 14);
            }
        }
    };

    // Parse layout to get grid dimensions (supports 2x2, 2x3, 3x3, etc)
    const getGridDimensions = () => {
        // Try to get layout from job, default to 2x2
        const layout = (job?.result as { layout?: string })?.layout || "2x2";
        const parts = layout.split("x");
        return {
            cols: parseInt(parts[0]) || 2,
            rows: parseInt(parts[1]) || 2
        };
    };
    const grid = getGridDimensions();
    const totalPanels = grid.cols * grid.rows;

    useEffect(() => {
        if (!jobId) return;

        const fetchJob = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/status/${jobId}`);
                if (response.ok) {
                    const data = await response.json();
                    setJob(data);
                }
            } catch (err) {
                console.error("Failed to fetch job");
            } finally {
                setLoading(false);
            }
        };

        fetchJob();
    }, [jobId]);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Delete selected bubble
            if ((e.key === "Delete" || e.key === "Backspace") && selectedBubble) {
                // Don't trigger if typing in an input
                if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
                    return;
                }
                e.preventDefault();
                deleteSelectedBubble();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [selectedBubble, selectedPanel, currentPage, panelDialogues]);

    const downloadFile = (type: "pdf" | "png" | "zip") => {
        window.open(`http://localhost:8000/api/download/${jobId}/${type}`, "_blank");
        setShowExportMenu(false);
    };

    const handleRegenerate = async () => {
        if (selectedPanel === null) return;
        setRegenerating(true);

        try {
            const response = await fetch(`http://localhost:8000/api/regenerate/${jobId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    page: currentPage,
                    panel: selectedPanel,
                    prompt_override: editingText || undefined
                })
            });

            if (response.ok) {
                // Refresh job data to get new panel image
                const jobResponse = await fetch(`http://localhost:8000/api/status/${jobId}`);
                if (jobResponse.ok) {
                    const data = await jobResponse.json();
                    setJob(data);
                }
            } else {
                console.error("Regeneration failed");
            }
        } catch (err) {
            console.error("Regeneration error:", err);
        } finally {
            setRegenerating(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a110e] flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <span className="material-symbols-outlined text-4xl text-[#38e07b] animate-spin">autorenew</span>
                    <div className="text-[#38e07b]">Loading preview...</div>
                </div>
            </div>
        );
    }

    const pages = job?.result?.pages || [];
    const totalPages = pages.length;
    const currentPageData = pages.find(p => p.page_number === currentPage);

    return (
        <div className="h-screen bg-[#0a110e] flex flex-col overflow-hidden">
            {/* Header */}
            <header className="h-16 shrink-0 flex items-center justify-between border-b border-white/5 bg-[#0a110e]/80 px-6 backdrop-blur-md z-20">
                <div className="flex items-center gap-4">
                    <Link href="/" className="flex size-8 items-center justify-center rounded-lg bg-[#38e07b]/20 text-[#38e07b]">
                        <span className="material-symbols-outlined">auto_stories</span>
                    </Link>
                    <div className="flex flex-col">
                        <h2 className="text-base font-bold leading-tight text-white">
                            {job?.result?.title || "Untitled Project"}
                        </h2>
                        <span className="text-xs text-white/50">Chapter 1 • {totalPages} pages</span>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {/* View Mode Toggle */}
                    <div className="hidden md:flex h-9 items-center rounded-full bg-[#16261e] p-1">
                        <button className="h-full px-4 rounded-full bg-[#0a110e] text-xs font-bold text-white">
                            Full Page
                        </button>
                        <button className="h-full px-4 rounded-full text-xs font-medium text-white/50 hover:text-white">
                            Panel View
                        </button>
                    </div>

                    <div className="h-6 w-px bg-white/10 mx-2"></div>

                    {/* Save & Export */}
                    <button className="flex items-center justify-center h-9 px-4 rounded-full bg-[#16261e] hover:bg-[#264532] text-sm font-bold text-white transition-colors">
                        <span className="material-symbols-outlined text-[18px] mr-2">save</span>
                        Save
                    </button>

                    <div className="relative">
                        <button
                            onClick={() => setShowExportMenu(!showExportMenu)}
                            className="flex items-center justify-center h-9 px-4 rounded-full bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] text-sm font-bold transition-colors"
                        >
                            <span className="material-symbols-outlined text-[18px] mr-2">download</span>
                            Export
                        </button>
                        {showExportMenu && (
                            <div className="absolute right-0 top-full mt-2 w-48 bg-[#16261e] rounded-xl shadow-xl border border-[#264532] p-2 z-50">
                                <button onClick={() => downloadFile("png")} className="w-full text-left px-4 py-2 text-sm text-white hover:bg-[#264532] rounded-lg flex items-center gap-2">
                                    <span className="material-symbols-outlined text-sm">image</span>
                                    Download PNG
                                </button>
                                <button onClick={() => downloadFile("pdf")} className="w-full text-left px-4 py-2 text-sm text-white hover:bg-[#264532] rounded-lg flex items-center gap-2">
                                    <span className="material-symbols-outlined text-sm">picture_as_pdf</span>
                                    Download PDF
                                </button>
                                <button onClick={() => downloadFile("zip")} className="w-full text-left px-4 py-2 text-sm text-white hover:bg-[#264532] rounded-lg flex items-center gap-2">
                                    <span className="material-symbols-outlined text-sm">folder_zip</span>
                                    Download Assets (ZIP)
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex flex-1 overflow-hidden">
                {/* Left Sidebar: Page Navigation */}
                <aside className="w-64 bg-[#0a110e] border-r border-white/5 flex flex-col">
                    <div className="p-4 border-b border-white/5 flex justify-between items-center">
                        <h3 className="font-bold text-sm text-white">Chapter Pages</h3>
                        <button className="text-[#38e07b] hover:text-[#2bc968]">
                            <span className="material-symbols-outlined">add_circle</span>
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                        {pages.map((page) => (
                            <button
                                key={page.page_number}
                                onClick={() => setCurrentPage(page.page_number)}
                                className={`w-full text-left group relative ${currentPage === page.page_number ? "" : "opacity-60 hover:opacity-100"}`}
                            >
                                <div className={`aspect-[2/3] w-full rounded-lg overflow-hidden border-2 ${currentPage === page.page_number
                                    ? "border-[#38e07b]"
                                    : "border-transparent hover:border-white/20"
                                    }`}>
                                    <img
                                        src={`http://localhost:8000/api/preview/${jobId}/${page.page_number}`}
                                        alt={`Page ${page.page_number}`}
                                        className={`w-full h-full object-cover ${currentPage !== page.page_number ? "grayscale" : ""}`}
                                    />
                                    {currentPage === page.page_number && (
                                        <div className="absolute inset-0 bg-[#38e07b]/10"></div>
                                    )}
                                </div>
                                <div className="flex justify-between items-center mt-2 px-1">
                                    <span className={`text-sm font-medium ${currentPage === page.page_number ? "text-[#38e07b] font-bold" : "text-white"}`}>
                                        Page {page.page_number}
                                    </span>
                                    {currentPage === page.page_number && (
                                        <span className="material-symbols-outlined text-sm text-[#38e07b]">edit</span>
                                    )}
                                </div>
                            </button>
                        ))}
                    </div>
                </aside>

                {/* Center Canvas - Scrollable when zoomed */}
                <section className="flex-1 bg-[#0c1610] relative overflow-auto p-8">
                    {/* Grid Background */}
                    <div
                        className="absolute inset-0 opacity-10 pointer-events-none"
                        style={{
                            backgroundImage: "radial-gradient(#38e07b 1px, transparent 1px)",
                            backgroundSize: "24px 24px"
                        }}
                    ></div>

                    {/* Centering wrapper */}
                    <div className="min-h-full flex items-center justify-center">
                        {/* Manga Page Container */}
                        <div
                            ref={canvasRef}
                            className="relative bg-white shadow-2xl overflow-visible transition-all duration-300 flex-shrink-0"
                            style={{
                                height: `${zoom}vh`,
                                maxHeight: `${zoom}vh`,
                                aspectRatio: "2 / 3"
                            }}
                        >
                            {currentPageData ? (
                                <>
                                    <img
                                        src={`http://localhost:8000/api/preview/${jobId}/${currentPage}`}
                                        alt={`Page ${currentPage}`}
                                        className="w-full h-full object-contain bg-white"
                                    />

                                    {/* Interactive Panel Overlays - Dynamic Grid */}
                                    <div
                                        className="absolute inset-0 grid gap-1 p-1"
                                        style={{
                                            gridTemplateColumns: `repeat(${grid.cols}, 1fr)`,
                                            gridTemplateRows: `repeat(${grid.rows}, 1fr)`
                                        }}
                                    >
                                        {Array.from({ length: totalPanels }).map((_, idx) => {
                                            const panelId = `page-${currentPage}-panel-${idx}`;
                                            const dialogues = panelDialogues[panelId] || [];

                                            return (
                                                <div
                                                    key={idx}
                                                    onClick={() => setSelectedPanel(selectedPanel === idx ? null : idx)}
                                                    className={`cursor-pointer rounded-sm transition-all relative ${selectedPanel === idx
                                                        ? "border-2 border-[#38e07b] bg-[#38e07b]/10 shadow-[0_0_15px_rgba(56,224,123,0.3)]"
                                                        : "border-2 border-transparent hover:border-[#38e07b]/50 hover:bg-[#38e07b]/5"
                                                        }`}
                                                >
                                                    {/* Panel selection badge */}
                                                    {selectedPanel === idx && (
                                                        <div className="absolute top-1 right-1 bg-[#38e07b] text-[#0a110e] text-xs font-bold px-2 py-0.5 rounded-full z-40">
                                                            Panel {idx + 1}
                                                        </div>
                                                    )}

                                                    {/* Dialogue Layer - ALWAYS render, but only interactive when selected */}
                                                    <DialogueLayer
                                                        panelId={panelId}
                                                        dialogues={dialogues}
                                                        onDialoguesChange={handleDialoguesChange}
                                                        containerRef={canvasRef}
                                                        isActive={selectedPanel === idx}
                                                        onBubbleSelect={handleBubbleSelection}
                                                    />
                                                </div>
                                            );
                                        })}
                                    </div>
                                </>
                            ) : (
                                <div className="w-full h-full flex items-center justify-center bg-[#16261e] text-white/30">
                                    <span className="material-symbols-outlined text-6xl">image</span>
                                </div>
                            )}
                        </div>

                    </div>

                    {/* Canvas Controls - Fixed at bottom of canvas area */}
                    <div className="sticky bottom-6 left-1/2 -translate-x-1/2 w-fit mx-auto flex items-center gap-2 bg-[#0a110e]/90 backdrop-blur-md px-2 py-1.5 rounded-full border border-white/10 shadow-xl z-20">
                        <button
                            onClick={() => setZoom(Math.max(50, zoom - 10))}
                            className="w-8 h-8 flex items-center justify-center rounded-full text-white hover:bg-white/10"
                        >
                            <span className="material-symbols-outlined text-[20px]">remove</span>
                        </button>
                        <span className="text-xs font-mono text-gray-300 w-12 text-center">{zoom}%</span>
                        <button
                            onClick={() => setZoom(Math.min(150, zoom + 10))}
                            className="w-8 h-8 flex items-center justify-center rounded-full text-white hover:bg-white/10"
                        >
                            <span className="material-symbols-outlined text-[20px]">add</span>
                        </button>
                        <div className="w-px h-4 bg-white/20 mx-1"></div>
                        <button
                            onClick={() => setZoom(85)}
                            className="w-8 h-8 flex items-center justify-center rounded-full text-white hover:bg-white/10"
                        >
                            <span className="material-symbols-outlined text-[20px]">fit_screen</span>
                        </button>
                    </div>
                </section>

                {/* Right Sidebar: Editor Tools */}
                <aside className="w-80 bg-[#0a110e] border-l border-white/5 flex flex-col">
                    {/* Header for Selected Item */}
                    <div className="p-5 border-b border-white/5">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="material-symbols-outlined text-[#38e07b] text-sm">crop_free</span>
                            <h3 className="font-bold text-xs uppercase tracking-wider text-white/50">
                                {selectedPanel !== null ? `Panel ${selectedPanel + 1} Selected` : "Select a Panel"}
                            </h3>
                        </div>
                        <h2 className="text-lg font-bold text-white">
                            {selectedPanel !== null ? "Edit Panel" : job?.result?.title || "Preview"}
                        </h2>
                    </div>

                    <div className="flex-1 overflow-y-auto p-5 space-y-6">
                        {selectedPanel !== null ? (
                            <>
                                {/* Panel Settings */}
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center">
                                        <h4 className="text-sm font-bold text-white">Panel Settings</h4>
                                        <button className="text-xs text-[#38e07b] hover:underline">Reset</button>
                                    </div>
                                    <div className="p-4 rounded-xl bg-[#16261e] border border-[#264532]">
                                        <label className="text-xs font-semibold text-white/50 mb-2 block">Prompt</label>
                                        <p className="text-sm italic text-white/70 mb-3">
                                            "Samurai shouting commands, close up face, dramatic shadows, ink lines"
                                        </p>
                                        <button
                                            onClick={handleRegenerate}
                                            disabled={regenerating}
                                            className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-[#38e07b]/10 hover:bg-[#38e07b]/20 text-[#38e07b] text-xs font-bold transition-colors disabled:opacity-50"
                                        >
                                            <span className={`material-symbols-outlined text-sm ${regenerating ? "animate-spin" : ""}`}>
                                                autorenew
                                            </span>
                                            {regenerating ? "Regenerating..." : "Regenerate Image"}
                                        </button>
                                    </div>

                                    {/* Art Strength Slider */}
                                    <div>
                                        <label className="text-xs font-semibold text-white/50 mb-2 flex justify-between">
                                            <span>Art Strength</span>
                                            <span>75%</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            defaultValue="75"
                                            className="w-full h-1 bg-[#264532] rounded-lg appearance-none cursor-pointer accent-[#38e07b]"
                                        />
                                    </div>
                                </div>

                                <div className="h-px bg-white/5 w-full"></div>

                                {/* Dialogue Editing */}
                                <div className="space-y-4">
                                    <h4 className="text-sm font-bold text-white">Dialogue & Bubbles</h4>

                                    <div className="space-y-3">
                                        <label className="text-xs font-semibold text-white/50 block">Content</label>
                                        <textarea
                                            value={editingText}
                                            onChange={(e) => setEditingText(e.target.value)}
                                            placeholder="Enter dialogue text..."
                                            className="w-full bg-[#16261e] border border-[#264532] rounded-xl p-3 text-sm text-white focus:ring-2 focus:ring-[#38e07b] focus:border-transparent outline-none resize-none"
                                            rows={3}
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-2">
                                            <label className="text-xs font-semibold text-white/50 block">Font</label>
                                            <select className="w-full bg-[#16261e] border border-[#264532] rounded-lg py-2 px-3 text-xs text-white appearance-none">
                                                <option>Manga Sans</option>
                                                <option>Action Bold</option>
                                                <option>Whisper Thin</option>
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-xs font-semibold text-white/50 block">Size</label>
                                            <div className="flex items-center bg-[#16261e] border border-[#264532] rounded-lg overflow-hidden">
                                                <button
                                                    onClick={() => updateBubbleFontSize(-2)}
                                                    disabled={!selectedBubble}
                                                    className="p-2 hover:bg-[#264532] disabled:opacity-50"
                                                >
                                                    <span className="material-symbols-outlined text-xs text-white">remove</span>
                                                </button>
                                                <input
                                                    type="text"
                                                    value={fontSize}
                                                    readOnly
                                                    className="w-full bg-transparent text-center text-xs text-white border-none p-0"
                                                />
                                                <button
                                                    onClick={() => updateBubbleFontSize(2)}
                                                    disabled={!selectedBubble}
                                                    className="p-2 hover:bg-[#264532] disabled:opacity-50"
                                                >
                                                    <span className="material-symbols-outlined text-xs text-white">add</span>
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-xs font-semibold text-white/50 block">Bubble Style</label>
                                        <div className="grid grid-cols-4 gap-2">
                                            {BUBBLE_STYLES.map((style) => (
                                                <button
                                                    key={style.id}
                                                    onClick={() => updateBubbleStyle(style.id)}
                                                    disabled={!selectedBubble}
                                                    className={`aspect-square rounded-lg border-2 flex items-center justify-center transition-all disabled:opacity-50 ${bubbleStyle === style.id
                                                        ? "border-[#38e07b] bg-[#38e07b]/10"
                                                        : "border-[#264532] bg-[#16261e] hover:border-[#38e07b]/50"
                                                        }`}
                                                    title={style.label}
                                                >
                                                    <span className="material-symbols-outlined text-white text-sm">
                                                        {style.icon}
                                                    </span>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-center">
                                <span className="material-symbols-outlined text-4xl text-white/20 mb-4">touch_app</span>
                                <p className="text-white/50 text-sm">Click on a panel to edit</p>
                                <p className="text-white/30 text-xs mt-2">You can regenerate images, edit dialogue, and customize bubble styles</p>
                            </div>
                        )}
                    </div>

                    {/* Quick Actions Footer */}
                    {selectedPanel !== null && (
                        <div className="p-4 border-t border-white/5 bg-[#16261e]/50">
                            <button className="w-full py-2.5 rounded-full bg-[#264532] hover:bg-[#264532]/80 text-white text-sm font-bold transition-colors flex items-center justify-center gap-2">
                                <span className="material-symbols-outlined text-sm">auto_awesome</span>
                                Refine Details
                            </button>
                        </div>
                    )}
                </aside>
            </main>
        </div>
    );
}
