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

// Bubble style options - 8 manga styles
const BUBBLE_STYLES = [
    { id: "speech", icon: "chat_bubble", label: "Speech" },
    { id: "thought", icon: "cloud", label: "Thought" },
    { id: "shout", icon: "campaign", label: "Shout" },
    { id: "narrator", icon: "article", label: "Narrator" },
    { id: "scream", icon: "crisis_alert", label: "Scream" },
    { id: "whisper", icon: "hearing", label: "Whisper" },
    { id: "impact", icon: "bolt", label: "Impact" },
    { id: "radio", icon: "radio", label: "Radio" },
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
    const [fontFamily, setFontFamily] = useState("Manga Sans");
    const [tailDirection, setTailDirection] = useState<"bottom" | "top" | "left" | "right">("bottom");
    const [regenerating, setRegenerating] = useState(false);
    const [showExportMenu, setShowExportMenu] = useState(false);
    const [regenPrompt, setRegenPrompt] = useState("");

    // Save project states
    const [saving, setSaving] = useState(false);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [saveMessage, setSaveMessage] = useState<{ type: "success" | "error", text: string } | null>(null);

    // Dialogues state: Map of panelId -> BubbleData[]
    const [panelDialogues, setPanelDialogues] = useState<Record<string, BubbleData[]>>({});

    // Undo/Redo history for dialogue edits
    const [dialogueHistory, setDialogueHistory] = useState<Record<string, BubbleData[]>[]>([]);
    const [historyIndex, setHistoryIndex] = useState(-1);
    const MAX_HISTORY = 50;

    // Handle dialogue updates from the canvas - WITH UNDO SUPPORT
    const handleDialoguesChange = (panelId: string, dialogues: BubbleData[]) => {
        setPanelDialogues(prev => {
            const newState = { ...prev, [panelId]: dialogues };

            // Push to history (truncate future states if we're in the middle of history)
            setDialogueHistory(prevHistory => {
                const currentHistory = prevHistory.slice(0, historyIndex + 1);
                const newHistory = [...currentHistory, newState].slice(-MAX_HISTORY);
                setHistoryIndex(newHistory.length - 1);
                return newHistory;
            });

            return newState;
        });
    };

    // Undo function
    const handleUndo = () => {
        if (historyIndex > 0) {
            const newIndex = historyIndex - 1;
            setHistoryIndex(newIndex);
            setPanelDialogues(dialogueHistory[newIndex] || {});
        }
    };

    // Redo function
    const handleRedo = () => {
        if (historyIndex < dialogueHistory.length - 1) {
            const newIndex = historyIndex + 1;
            setHistoryIndex(newIndex);
            setPanelDialogues(dialogueHistory[newIndex] || {});
        }
    };

    // Can undo/redo checks
    const canUndo = historyIndex > 0;
    const canRedo = historyIndex < dialogueHistory.length - 1;


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

    // Update selected bubble's text - SYNCS SIDEBAR TO BUBBLE
    const updateBubbleText = (newText: string) => {
        setEditingText(newText);
        if (!selectedBubble || selectedPanel === null) return;
        const panelId = `page-${currentPage}-panel-${selectedPanel}`;
        const dialogues = panelDialogues[panelId] || [];
        const updated = dialogues.map(b =>
            b.id === selectedBubble ? { ...b, text: newText } : b
        );
        handleDialoguesChange(panelId, updated);
    };

    // Update selected bubble's font family
    const updateBubbleFontFamily = (newFont: string) => {
        setFontFamily(newFont);
        if (!selectedBubble || selectedPanel === null) return;
        const panelId = `page-${currentPage}-panel-${selectedPanel}`;
        const dialogues = panelDialogues[panelId] || [];
        const updated = dialogues.map(b =>
            b.id === selectedBubble ? { ...b, fontFamily: newFont } : b
        );
        handleDialoguesChange(panelId, updated);
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
                setFontFamily(bubble.fontFamily || "Manga Sans");
                setTailDirection(bubble.tailDirection || "bottom");
            }
        }
    };

    // Update selected bubble's tail direction
    const updateBubbleTailDirection = (newDirection: "bottom" | "top" | "left" | "right") => {
        if (!selectedBubble || selectedPanel === null) return;
        const panelId = `page-${currentPage}-panel-${selectedPanel}`;
        const dialogues = panelDialogues[panelId] || [];
        const updated = dialogues.map(b =>
            b.id === selectedBubble ? { ...b, tailDirection: newDirection } : b
        );
        setPanelDialogues(prev => ({ ...prev, [panelId]: updated }));
        setTailDirection(newDirection);
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

    // AUTO-LOAD DIALOGUES FROM LLM - This populates canvas with story dialogue!
    useEffect(() => {
        if (!job?.result?.pages) return;

        // The backend sends: page.dialogue = [{panel_index, dialogues: [{character, text, style}]}]
        type DialogueEntry = {
            panel_index: number;
            dialogues: Array<{
                character?: string;
                text: string;
                style?: string;
            }>;
        };

        const pages = job.result.pages as Array<{
            page_number: number;
            dialogue?: DialogueEntry[];
        }>;

        const newDialogues: Record<string, BubbleData[]> = {};

        pages.forEach((page, pageIdx) => {
            const pageNum = page.page_number || pageIdx + 1;
            const dialogueData = page.dialogue || [];

            // Each entry has panel_index and nested dialogues array
            dialogueData.forEach((panelDialogue) => {
                const panelIdx = panelDialogue.panel_index;
                const panelId = `page-${pageNum}-panel-${panelIdx}`;

                if (!newDialogues[panelId]) {
                    newDialogues[panelId] = [];
                }

                // Iterate through actual dialogue lines for this panel
                const dialogueLines = panelDialogue.dialogues || [];
                dialogueLines.forEach((d, dIdx) => {
                    // Better positioning: start from top-left, stack down
                    const xPos = 10 + (dIdx % 2) * 40; // Alternate left/right
                    const yPos = 10 + dIdx * 20; // Stack down

                    const bubble: BubbleData = {
                        id: `llm-${pageNum}-${panelIdx}-${dIdx}`,
                        text: d.text || "...",
                        x: Math.min(xPos, 80), // Keep within bounds
                        y: Math.min(yPos, 70),
                        style: (d.style === "narrator" || d.style === "thought" ||
                            d.style === "shout" || d.style === "whisper")
                            ? d.style as BubbleData["style"] : "speech",
                        character: d.character,
                        fontSize: 11
                    };

                    newDialogues[panelId].push(bubble);
                });
            });
        });

        // Only set if we have dialogues and panelDialogues is empty
        if (Object.keys(newDialogues).length > 0) {
            setPanelDialogues(prev => {
                // Don't overwrite if user already edited
                if (Object.keys(prev).length > 0) return prev;
                console.log("📝 Auto-loaded LLM dialogues:", Object.keys(newDialogues).length, "panels with dialogue");
                return newDialogues;
            });
        }
    }, [job]);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Don't trigger if typing in an input
            if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
                return;
            }

            // Undo: Ctrl+Z
            if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
                e.preventDefault();
                handleUndo();
            }

            // Redo: Ctrl+Y or Ctrl+Shift+Z
            if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) {
                e.preventDefault();
                handleRedo();
            }

            // Delete selected bubble
            if ((e.key === "Delete" || e.key === "Backspace") && selectedBubble) {
                e.preventDefault();
                deleteSelectedBubble();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [selectedBubble, selectedPanel, currentPage, panelDialogues, historyIndex, dialogueHistory]);

    const downloadFile = (type: "pdf" | "png" | "zip") => {
        // For PDF export, send dialogue data so backend renders bubbles on images
        const dialoguesParam = type === "pdf" ? `?dialogues=${encodeURIComponent(JSON.stringify(panelDialogues))}` : "";
        window.open(`http://localhost:8000/api/download/${jobId}/${type}${dialoguesParam}`, "_blank");
        setShowExportMenu(false);
    };

    // Save project to user profile
    const handleSaveProject = async () => {
        // Check if user is logged in
        const token = localStorage.getItem("mangagen_token");

        if (!token) {
            setShowLoginModal(true);
            return;
        }

        setSaving(true);
        setSaveMessage(null);

        try {
            const response = await fetch("http://localhost:8000/api/projects/save", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    job_id: jobId,
                    title: job?.result?.title || "Untitled Manga",
                    dialogues: panelDialogues  // All dialogue positions and text
                })
            });

            if (response.status === 401) {
                // Token invalid/expired
                setShowLoginModal(true);
                return;
            }

            if (response.ok) {
                const data = await response.json();
                setSaveMessage({ type: "success", text: "✅ Saved to your profile!" });
                setTimeout(() => setSaveMessage(null), 3000);
            } else {
                const err = await response.json();
                setSaveMessage({ type: "error", text: err.detail || "Failed to save" });
            }
        } catch (error) {
            setSaveMessage({ type: "error", text: "Network error. Please try again." });
        } finally {
            setSaving(false);
        }
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
                    prompt_override: regenPrompt || undefined
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

                    {/* Save Button */}
                    <button
                        onClick={handleSaveProject}
                        disabled={saving}
                        className="flex items-center justify-center h-9 px-4 rounded-full border border-[#38e07b] text-[#38e07b] hover:bg-[#38e07b]/10 text-sm font-bold transition-colors disabled:opacity-50"
                    >
                        <span className={`material-symbols-outlined text-[18px] mr-2 ${saving ? "animate-spin" : ""}`}>
                            {saving ? "sync" : "save"}
                        </span>
                        {saving ? "Saving..." : "Save"}
                    </button>

                    {/* Save Message Toast */}
                    {saveMessage && (
                        <div className={`absolute top-full mt-2 right-0 px-4 py-2 rounded-lg text-sm font-medium ${saveMessage.type === "success" ? "bg-green-500/20 text-green-400 border border-green-500/30" : "bg-red-500/20 text-red-400 border border-red-500/30"
                            }`}>
                            {saveMessage.text}
                        </div>
                    )}
                </div>
            </header>

            {/* Login Required Modal */}
            {showLoginModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[100]">
                    <div className="bg-[#16261e] rounded-2xl p-8 max-w-md w-full mx-4 border border-[#264532] z-[101]">
                        <div className="text-center">
                            <span className="material-symbols-outlined text-5xl text-[#38e07b] mb-4">account_circle</span>
                            <h3 className="text-xl font-bold text-white mb-2">Login to Save</h3>
                            <p className="text-gray-400 mb-6">Create an account or login to save your manga to your profile.</p>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setShowLoginModal(false)}
                                    className="flex-1 py-3 rounded-lg border border-white/20 text-white hover:bg-white/5"
                                >
                                    Cancel
                                </button>
                                <a
                                    href="/login"
                                    className="flex-1 py-3 rounded-lg bg-[#38e07b] text-[#0a110e] font-bold hover:bg-[#2bc968] text-center"
                                >
                                    Login
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            )}

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
                        {/* Undo/Redo */}
                        <button
                            onClick={handleUndo}
                            disabled={!canUndo}
                            className="w-8 h-8 flex items-center justify-center rounded-full text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
                            title="Undo (Ctrl+Z)"
                        >
                            <span className="material-symbols-outlined text-[20px]">undo</span>
                        </button>
                        <button
                            onClick={handleRedo}
                            disabled={!canRedo}
                            className="w-8 h-8 flex items-center justify-center rounded-full text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
                            title="Redo (Ctrl+Y)"
                        >
                            <span className="material-symbols-outlined text-[20px]">redo</span>
                        </button>
                        <div className="w-px h-4 bg-white/20 mx-1"></div>
                        {/* Zoom Controls */}
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
                                        <button
                                            onClick={() => setRegenPrompt("")}
                                            className="text-xs text-[#38e07b] hover:underline"
                                        >
                                            Reset
                                        </button>
                                    </div>
                                    <div className="p-4 rounded-xl bg-[#16261e] border border-[#264532]">
                                        <label className="text-xs font-semibold text-white/50 mb-2 block">
                                            Regeneration Prompt (edit to improve)
                                        </label>
                                        <textarea
                                            value={regenPrompt}
                                            onChange={(e) => setRegenPrompt(e.target.value)}
                                            placeholder="Describe how you want this panel regenerated... (e.g., 'close-up face, more dramatic shadows, angry expression')"
                                            className="w-full h-20 bg-[#0a110e] border border-[#264532] rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-[#38e07b] resize-none mb-3"
                                        />
                                        <button
                                            onClick={handleRegenerate}
                                            disabled={regenerating}
                                            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] text-sm font-bold transition-colors disabled:opacity-50"
                                        >
                                            <span className={`material-symbols-outlined text-sm ${regenerating ? "animate-spin" : ""}`}>
                                                autorenew
                                            </span>
                                            {regenerating ? "Regenerating..." : "Regenerate Panel"}
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
                                            onChange={(e) => updateBubbleText(e.target.value)}
                                            placeholder="Enter dialogue text..."
                                            className="w-full bg-[#16261e] border border-[#264532] rounded-xl p-3 text-sm text-white focus:ring-2 focus:ring-[#38e07b] focus:border-transparent outline-none resize-none"
                                            rows={3}
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-2">
                                            <label className="text-xs font-semibold text-white/50 block">Font</label>
                                            <select
                                                value={fontFamily}
                                                onChange={(e) => updateBubbleFontFamily(e.target.value)}
                                                disabled={!selectedBubble}
                                                className="w-full bg-[#16261e] border border-[#264532] rounded-lg py-2 px-3 text-xs text-white appearance-none disabled:opacity-50"
                                            >
                                                <option value="Manga Sans">Manga Sans</option>
                                                <option value="Action Bold">Action Bold</option>
                                                <option value="Whisper Thin">Whisper Thin</option>
                                                <option value="Comic Sans MS">Comic Style</option>
                                                <option value="Arial Black">Impact Bold</option>
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

                                    {/* Tail Direction Control */}
                                    <div className="space-y-2">
                                        <label className="text-xs font-semibold text-white/50 block">Arrow Direction</label>
                                        <div className="grid grid-cols-4 gap-2">
                                            {[
                                                { dir: "top" as const, icon: "arrow_upward", label: "Top" },
                                                { dir: "bottom" as const, icon: "arrow_downward", label: "Bottom" },
                                                { dir: "left" as const, icon: "arrow_back", label: "Left" },
                                                { dir: "right" as const, icon: "arrow_forward", label: "Right" },
                                            ].map((item) => (
                                                <button
                                                    key={item.dir}
                                                    onClick={() => updateBubbleTailDirection(item.dir)}
                                                    disabled={!selectedBubble}
                                                    className={`aspect-square rounded-lg border-2 flex items-center justify-center transition-all disabled:opacity-50 ${tailDirection === item.dir
                                                        ? "border-[#38e07b] bg-[#38e07b]/10"
                                                        : "border-[#264532] bg-[#16261e] hover:border-[#38e07b]/50"
                                                        }`}
                                                    title={item.label}
                                                >
                                                    <span className="material-symbols-outlined text-white text-sm">
                                                        {item.icon}
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
