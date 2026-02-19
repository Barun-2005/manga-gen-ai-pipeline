"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import DialogueLayer, { BubbleData } from "@/components/DialogueLayer";
import { API_URL } from "@/config";
import StoryViewer from "@/components/StoryViewer";

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
        manga_title?: string;
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

    // Sidebar tab state: "story" | "edit" | "style"
    const [sidebarTab, setSidebarTab] = useState<"story" | "edit" | "style">("edit");

    // Dialogue regeneration state
    const [regeneratingDialogue, setRegeneratingDialogue] = useState(false);
    const [dialogueStyleHint, setDialogueStyleHint] = useState("");

    // Editable titles state
    const [mangaTitle, setMangaTitle] = useState("");
    const [chapterTitle, setChapterTitle] = useState("");
    const [editingMangaTitle, setEditingMangaTitle] = useState(false);
    const [editingChapterTitle, setEditingChapterTitle] = useState(false);

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

    // V4: Get actual panel geometry from page data (with fallback to grid calculation)
    const getPanelGeometry = (): Array<{ x: number; y: number; w: number; h: number }> => {
        const pages = job?.result?.pages || [];
        const currentPageData = pages[currentPage - 1];

        if (!currentPageData) {
            // Fallback to equal grid
            return Array.from({ length: grid.cols * grid.rows }, (_, idx) => ({
                x: (idx % grid.cols) * (100 / grid.cols),
                y: Math.floor(idx / grid.cols) * (100 / grid.rows),
                w: 100 / grid.cols,
                h: 100 / grid.rows
            }));
        }

        // Try to read panels array with x,y,w,h from V4 backend
        const panels = (currentPageData as any).panels || [];
        if (panels.length > 0 && panels[0]?.w !== undefined) {
            // V4: Use actual panel geometry from layout template
            return panels.map((panel: any) => ({
                x: panel.x ?? 0,
                y: panel.y ?? 0,
                w: panel.w ?? 50,
                h: panel.h ?? 50
            }));
        }

        // Fallback to equal grid based on panel count
        const panelCount = panels.length || (grid.cols * grid.rows);
        const cols = Math.ceil(Math.sqrt(panelCount));
        const rows = Math.ceil(panelCount / cols);
        return Array.from({ length: panelCount }, (_, idx) => ({
            x: (idx % cols) * (100 / cols),
            y: Math.floor(idx / cols) * (100 / rows),
            w: 100 / cols,
            h: 100 / rows
        }));
    };

    const panelGeometry = getPanelGeometry();
    const totalPanels = panelGeometry.length;

    // V4 DEBUG: Log panel geometry to verify values
    useEffect(() => {
        if (panelGeometry.length > 0) {
            console.log(`📐 Panel Geometry for Page ${currentPage}:`, panelGeometry);
        }
    }, [currentPage, panelGeometry.length]);

    useEffect(() => {
        if (!jobId) return;

        const fetchJob = async () => {
            try {
                const response = await fetch(`${API_URL}/api/status/${jobId}`);
                if (response.ok) {
                    const data = await response.json();
                    setJob(data);

                    // Initialize title states from result
                    if (data.result) {
                        setMangaTitle(data.result.manga_title || data.result.title || "Untitled");
                        setChapterTitle(data.result.title || "Chapter 1");
                    }

                    // Also fetch saved dialogues if this is a saved project
                    try {
                        const dialogueResponse = await fetch(`${API_URL}/api/projects/${jobId}/dialogues`);
                        if (dialogueResponse.ok) {
                            const dialogueData = await dialogueResponse.json();
                            if (dialogueData.dialogues && Object.keys(dialogueData.dialogues).length > 0) {
                                console.log("📝 Loaded saved dialogues:", Object.keys(dialogueData.dialogues).length, "panels");
                                setPanelDialogues(dialogueData.dialogues);
                            }
                        }
                    } catch (dialogueErr) {
                        console.log("No saved dialogues found (normal for new projects)");
                    }
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
        window.open(`${API_URL}/api/download/${jobId}/${type}${dialoguesParam}`, "_blank");
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
            const response = await fetch(`${API_URL}/api/projects/save`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    job_id: jobId,
                    manga_title: mangaTitle || job?.result?.manga_title || job?.result?.title || "Untitled Manga",
                    title: chapterTitle || job?.result?.title || "Chapter 1",
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
            const response = await fetch(`${API_URL}/api/regenerate/${jobId}`, {
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
                const jobResponse = await fetch(`${API_URL}/api/status/${jobId}`);
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

    // Handle dialogue regeneration (V3 Phase 4)
    const handleRegenerateDialogue = async () => {
        if (selectedPanel === null) return;
        setRegeneratingDialogue(true);

        try {
            const response = await fetch(`${API_URL}/api/dialogues/regenerate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    job_id: jobId,
                    page: currentPage,
                    panel: selectedPanel + 1, // API uses 1-indexed panels
                    style_hint: dialogueStyleHint || undefined
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.new_dialogues) {
                    // Convert API response to BubbleData format
                    const panelId = `page-${currentPage}-panel-${selectedPanel}`;
                    const newBubbles: BubbleData[] = data.new_dialogues.map((dlg: any, idx: number) => ({
                        id: dlg.dialogue_id || `bubble-${Date.now()}-${idx}`,
                        text: dlg.text,
                        x: 10 + (idx * 15) % 60, // Space out bubbles
                        y: 10 + (idx * 20) % 50,
                        style: dlg.type || "speech",
                        character: dlg.character,
                        fontSize: 14,
                        fontFamily: "Manga Sans"
                    }));

                    handleDialoguesChange(panelId, newBubbles);
                    console.log(`✅ Regenerated ${newBubbles.length} dialogues using ${data.llm_used}`);
                }
            } else {
                console.error("Dialogue regeneration failed");
            }
        } catch (err) {
            console.error("Dialogue regeneration error:", err);
        } finally {
            setRegeneratingDialogue(false);
            setDialogueStyleHint("");
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
                    <div className="flex flex-col gap-0.5">
                        {/* Editable Manga Title */}
                        {editingMangaTitle ? (
                            <input
                                type="text"
                                value={mangaTitle}
                                onChange={(e) => setMangaTitle(e.target.value)}
                                onBlur={() => setEditingMangaTitle(false)}
                                onKeyDown={(e) => e.key === "Enter" && setEditingMangaTitle(false)}
                                className="bg-transparent text-base font-bold text-white border-b border-[#38e07b] outline-none px-1 -ml-1"
                                autoFocus
                            />
                        ) : (
                            <h2
                                onClick={() => setEditingMangaTitle(true)}
                                className="text-base font-bold leading-tight text-white cursor-pointer hover:text-[#38e07b] transition-colors group"
                                title="Click to edit manga title"
                            >
                                {mangaTitle || job?.result?.title || "Untitled Project"}
                                <span className="material-symbols-outlined text-[12px] opacity-0 group-hover:opacity-50 ml-1">edit</span>
                            </h2>
                        )}
                        {/* Editable Chapter Title */}
                        {editingChapterTitle ? (
                            <input
                                type="text"
                                value={chapterTitle}
                                onChange={(e) => setChapterTitle(e.target.value)}
                                onBlur={() => setEditingChapterTitle(false)}
                                onKeyDown={(e) => e.key === "Enter" && setEditingChapterTitle(false)}
                                className="bg-transparent text-xs text-white/50 border-b border-[#38e07b]/50 outline-none px-1 -ml-1"
                                autoFocus
                            />
                        ) : (
                            <span
                                onClick={() => setEditingChapterTitle(true)}
                                className="text-xs text-white/50 cursor-pointer hover:text-white/70 transition-colors"
                                title="Click to edit chapter name"
                            >
                                Ch. 1: {chapterTitle || "Untitled Chapter"} • {totalPages} pages
                            </span>
                        )}
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
                                        src={`${API_URL}/api/preview/${jobId}/${page.page_number}`}
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
                                        src={`${API_URL}/api/preview/${jobId}/${currentPage}`}
                                        alt={`Page ${currentPage}`}
                                        className="w-full h-full object-contain bg-white"
                                    />

                                    {/* V4: Interactive Panel Overlays - Absolute Positioning from Layout Template */}
                                    <div className="absolute inset-0">
                                        {panelGeometry.map((geom, idx) => {
                                            const panelId = `page-${currentPage}-panel-${idx}`;
                                            const dialogues = panelDialogues[panelId] || [];

                                            return (
                                                <div
                                                    key={idx}
                                                    onClick={() => setSelectedPanel(selectedPanel === idx ? null : idx)}
                                                    className={`absolute cursor-pointer rounded-sm transition-all ${selectedPanel === idx
                                                        ? "border-2 border-[#38e07b] bg-[#38e07b]/10 shadow-[0_0_15px_rgba(56,224,123,0.3)]"
                                                        : "border-2 border-transparent hover:border-[#38e07b]/50 hover:bg-[#38e07b]/5"
                                                        }`}
                                                    style={{
                                                        // V4: Subtract 4px gap to prevent overlap with neighboring panels
                                                        left: `calc(${geom.x}% + 2px)`,
                                                        top: `calc(${geom.y}% + 2px)`,
                                                        width: `calc(${geom.w}% - 4px)`,
                                                        height: `calc(${geom.h}% - 4px)`
                                                    }}
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

                {/* Right Sidebar: Editor Tools — Tabbed Layout */}
                <aside className="w-80 bg-[#0a110e] border-l border-white/5 flex flex-col">
                    {/* Sidebar Header: Panel Info + Selected Bubble Quick Actions */}
                    <div className="shrink-0 border-b border-white/5">
                        <div className="px-4 pt-4 pb-2">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[#38e07b] text-sm">crop_free</span>
                                    <h3 className="font-bold text-sm text-white">
                                        {selectedPanel !== null ? `Panel ${selectedPanel + 1}` : "Canvas"}
                                    </h3>
                                </div>
                                {/* Quick Actions */}
                                <div className="flex items-center gap-1">
                                    {selectedBubble && (
                                        <button
                                            onClick={deleteSelectedBubble}
                                            className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/20 transition-colors"
                                            title="Delete bubble (Del)"
                                        >
                                            <span className="material-symbols-outlined text-[16px]">delete</span>
                                        </button>
                                    )}
                                </div>
                            </div>
                            {/* Selected Bubble Indicator */}
                            {selectedBubble && (() => {
                                const bubbleData = getSelectedBubbleData();
                                return bubbleData ? (
                                    <div className="mt-2 flex items-center gap-2 text-xs text-white/60 bg-[#16261e] rounded-lg px-3 py-1.5 border border-[#264532]">
                                        <span className="material-symbols-outlined text-[14px] text-[#38e07b]">chat_bubble</span>
                                        <span className="truncate flex-1">{bubbleData.text || "Empty bubble"}</span>
                                        <span className="text-[10px] text-white/30 capitalize">{bubbleData.style}</span>
                                    </div>
                                ) : null;
                            })()}
                        </div>

                        {/* Tab Navigation */}
                        <div className="flex px-2">
                            {([
                                { id: "story" as const, icon: "menu_book", label: "Story" },
                                { id: "edit" as const, icon: "edit", label: "Edit" },
                                { id: "style" as const, icon: "palette", label: "Style" },
                            ]).map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setSidebarTab(tab.id)}
                                    className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium border-b-2 transition-colors ${sidebarTab === tab.id
                                        ? "text-[#38e07b] border-[#38e07b] bg-[#38e07b]/5"
                                        : "text-gray-500 border-transparent hover:text-white hover:border-white/20"
                                        }`}
                                >
                                    <span className="material-symbols-outlined text-[16px]">{tab.icon}</span>
                                    {tab.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Tab Content — fills remaining height */}
                    <div className="flex-1 overflow-y-auto">
                        {sidebarTab === "story" ? (
                            /* ═══ STORY TAB ═══ */
                            <div className="h-full">
                                <StoryViewer
                                    jobId={jobId}
                                    currentPage={currentPage}
                                    selectedPanel={selectedPanel}
                                    onSelectPage={(pageNum) => setCurrentPage(pageNum)}
                                />
                            </div>
                        ) : (
                            /* ═══ EDIT & STYLE TABS (combined for simplicity, sectioned visually) ═══ */
                            <div className="p-4 space-y-4">
                                {selectedPanel !== null ? (
                                    <>
                                        {/* ═══ EDIT TAB SECTIONS ═══ */}
                                        {sidebarTab === "edit" && (
                                            <>
                                                {/* ── Panel Regeneration ── */}
                                                <div>
                                                    <div className="flex items-center gap-2 mb-2.5">
                                                        <span className="material-symbols-outlined text-[#38e07b] text-sm">autorenew</span>
                                                        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Regenerate Panel</h4>
                                                    </div>
                                                    <div className="bg-[#16261e] rounded-xl border border-[#264532] p-3 space-y-2.5">
                                                        <textarea
                                                            value={regenPrompt}
                                                            onChange={(e) => setRegenPrompt(e.target.value)}
                                                            placeholder="Describe how to regenerate... (e.g., 'close-up face, dramatic shadows')"
                                                            className="w-full h-16 bg-[#0a110e] border border-[#264532] rounded-lg px-3 py-2 text-xs text-white placeholder:text-white/30 focus:outline-none focus:border-[#38e07b] resize-none"
                                                        />
                                                        <button
                                                            onClick={handleRegenerate}
                                                            disabled={regenerating}
                                                            className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] text-xs font-bold transition-colors disabled:opacity-50"
                                                        >
                                                            <span className={`material-symbols-outlined text-sm ${regenerating ? "animate-spin" : ""}`}>autorenew</span>
                                                            {regenerating ? "Regenerating..." : "Regenerate"}
                                                        </button>
                                                    </div>
                                                </div>

                                                <div className="h-px bg-white/5"></div>

                                                {/* ── AI Dialogue Regeneration ── */}
                                                <div>
                                                    <div className="flex items-center gap-2 mb-2.5">
                                                        <span className="material-symbols-outlined text-[#38e07b] text-sm">auto_awesome</span>
                                                        <h4 className="text-xs font-bold text-white uppercase tracking-wider">AI Dialogue</h4>
                                                    </div>
                                                    <div className="bg-gradient-to-br from-[#16261e] to-[#1a2a22] rounded-xl border border-[#38e07b]/20 p-3 space-y-2.5">
                                                        <input
                                                            type="text"
                                                            value={dialogueStyleHint}
                                                            onChange={(e) => setDialogueStyleHint(e.target.value)}
                                                            placeholder="Style hint: dramatic, funnier, intense..."
                                                            className="w-full bg-[#0d1a14] border border-[#264532] rounded-lg py-2 px-3 text-xs text-white placeholder:text-white/30 focus:outline-none focus:border-[#38e07b]"
                                                        />
                                                        <button
                                                            onClick={handleRegenerateDialogue}
                                                            disabled={regeneratingDialogue}
                                                            className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-[#38e07b]/20 hover:bg-[#38e07b]/30 border border-[#38e07b]/40 text-[#38e07b] text-xs font-bold transition-colors disabled:opacity-50"
                                                        >
                                                            <span className={`material-symbols-outlined text-sm ${regeneratingDialogue ? "animate-spin" : ""}`}>
                                                                {regeneratingDialogue ? "sync" : "auto_fix_high"}
                                                            </span>
                                                            {regeneratingDialogue ? "Regenerating..." : "Regenerate Dialogue"}
                                                        </button>
                                                    </div>
                                                </div>

                                                <div className="h-px bg-white/5"></div>

                                                {/* ── Bubble Text Editor ── */}
                                                <div>
                                                    <div className="flex items-center gap-2 mb-2.5">
                                                        <span className="material-symbols-outlined text-[#38e07b] text-sm">edit_note</span>
                                                        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Bubble Text</h4>
                                                    </div>
                                                    <textarea
                                                        value={editingText}
                                                        onChange={(e) => updateBubbleText(e.target.value)}
                                                        placeholder={selectedBubble ? "Edit dialogue text..." : "Select a bubble to edit..."}
                                                        disabled={!selectedBubble}
                                                        className="w-full bg-[#16261e] border border-[#264532] rounded-xl p-3 text-sm text-white focus:ring-2 focus:ring-[#38e07b] focus:border-transparent outline-none resize-none disabled:opacity-40"
                                                        rows={2}
                                                    />
                                                </div>
                                            </>
                                        )}

                                        {/* ═══ STYLE TAB SECTIONS ═══ */}
                                        {sidebarTab === "style" && (
                                            <>
                                                <div className="h-px bg-white/5"></div>

                                                {/* ── Font & Size (compact row) ── */}
                                                <div>
                                                    <div className="flex items-center gap-2 mb-2.5">
                                                        <span className="material-symbols-outlined text-[#38e07b] text-sm">text_format</span>
                                                        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Typography</h4>
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-2">
                                                        <select
                                                            value={fontFamily}
                                                            onChange={(e) => updateBubbleFontFamily(e.target.value)}
                                                            disabled={!selectedBubble}
                                                            className="bg-[#16261e] border border-[#264532] rounded-lg py-2 px-2.5 text-xs text-white appearance-none disabled:opacity-40"
                                                        >
                                                            <option value="Manga Sans">Manga Sans</option>
                                                            <option value="Action Bold">Action Bold</option>
                                                            <option value="Whisper Thin">Whisper Thin</option>
                                                            <option value="Comic Sans MS">Comic Style</option>
                                                            <option value="Arial Black">Impact Bold</option>
                                                        </select>
                                                        <div className="flex items-center bg-[#16261e] border border-[#264532] rounded-lg overflow-hidden">
                                                            <button
                                                                onClick={() => updateBubbleFontSize(-2)}
                                                                disabled={!selectedBubble}
                                                                className="px-2 py-2 hover:bg-[#264532] disabled:opacity-40"
                                                            >
                                                                <span className="material-symbols-outlined text-xs text-white">remove</span>
                                                            </button>
                                                            <span className="flex-1 text-center text-xs text-white font-mono">{fontSize}px</span>
                                                            <button
                                                                onClick={() => updateBubbleFontSize(2)}
                                                                disabled={!selectedBubble}
                                                                className="px-2 py-2 hover:bg-[#264532] disabled:opacity-40"
                                                            >
                                                                <span className="material-symbols-outlined text-xs text-white">add</span>
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="h-px bg-white/5"></div>

                                                {/* ── Bubble Style Grid (8 styles, 4 cols) ── */}
                                                <div>
                                                    <div className="flex items-center gap-2 mb-2.5">
                                                        <span className="material-symbols-outlined text-[#38e07b] text-sm">chat</span>
                                                        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Bubble Style</h4>
                                                    </div>
                                                    <div className="grid grid-cols-4 gap-1.5">
                                                        {BUBBLE_STYLES.map((style) => (
                                                            <button
                                                                key={style.id}
                                                                onClick={() => updateBubbleStyle(style.id)}
                                                                disabled={!selectedBubble}
                                                                className={`flex flex-col items-center gap-0.5 py-2 rounded-lg border transition-all disabled:opacity-40 ${bubbleStyle === style.id
                                                                    ? "border-[#38e07b] bg-[#38e07b]/10 text-[#38e07b]"
                                                                    : "border-[#264532] bg-[#16261e] hover:border-[#38e07b]/50 text-white/70"
                                                                    }`}
                                                                title={style.label}
                                                            >
                                                                <span className="material-symbols-outlined text-[16px]">{style.icon}</span>
                                                                <span className="text-[9px] font-medium">{style.label}</span>
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>

                                                <div className="h-px bg-white/5"></div>

                                                {/* ── Arrow Direction (4 dirs, compact) ── */}
                                                <div>
                                                    <div className="flex items-center gap-2 mb-2.5">
                                                        <span className="material-symbols-outlined text-[#38e07b] text-sm">call_made</span>
                                                        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Tail Direction</h4>
                                                    </div>
                                                    <div className="grid grid-cols-4 gap-1.5">
                                                        {[
                                                            { dir: "top" as const, icon: "arrow_upward", label: "Up" },
                                                            { dir: "bottom" as const, icon: "arrow_downward", label: "Down" },
                                                            { dir: "left" as const, icon: "arrow_back", label: "Left" },
                                                            { dir: "right" as const, icon: "arrow_forward", label: "Right" },
                                                        ].map((item) => (
                                                            <button
                                                                key={item.dir}
                                                                onClick={() => updateBubbleTailDirection(item.dir)}
                                                                disabled={!selectedBubble}
                                                                className={`flex flex-col items-center gap-0.5 py-2 rounded-lg border transition-all disabled:opacity-40 ${tailDirection === item.dir
                                                                    ? "border-[#38e07b] bg-[#38e07b]/10 text-[#38e07b]"
                                                                    : "border-[#264532] bg-[#16261e] hover:border-[#38e07b]/50 text-white/70"
                                                                    }`}
                                                                title={item.label}
                                                            >
                                                                <span className="material-symbols-outlined text-[16px]">{item.icon}</span>
                                                                <span className="text-[9px] font-medium">{item.label}</span>
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            </>
                                        )}
                                    </>
                                ) : (
                                    <div className="flex flex-col items-center justify-center py-16 text-center">
                                        <span className="material-symbols-outlined text-5xl text-white/10 mb-4">touch_app</span>
                                        <p className="text-white/50 text-sm font-medium">Click on a panel to edit</p>
                                        <p className="text-white/30 text-xs mt-2 max-w-[200px]">Regenerate images, edit dialogue, and customize bubble styles</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                </aside>
            </main>
        </div >
    );
}
