"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { API_URL } from "@/config";

interface StepStatus {
    name: string;
    status: "pending" | "in_progress" | "completed";
    duration?: string;
}

interface JobStatus {
    job_id: string;
    status: "pending" | "generating" | "completed" | "failed";
    progress: number;
    current_step: string;
    steps?: StepStatus[];
    current_panel?: number;
    total_panels?: number;
    panel_previews?: string[];
    log_messages?: string[];
    layout?: string;
    result?: {
        title: string;
        pages: { page_number: number; page_image: string }[];
        pdf: string;
    };
    error?: string;
}

export default function GeneratePage() {
    const params = useParams();
    const router = useRouter();
    const jobId = params.jobId as string;
    const logRef = useRef<HTMLDivElement>(null);

    const [job, setJob] = useState<JobStatus | null>(null);
    const [error, setError] = useState("");

    // Auto-scroll terminal log
    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [job?.log_messages]);

    useEffect(() => {
        if (!jobId) return;

        let retryCount = 0;
        const maxRetries = 5;

        const pollStatus = async () => {
            try {
                const response = await fetch(`${API_URL}/api/status/${jobId}`, {
                    signal: AbortSignal.timeout(10000) // 10 second timeout
                });
                if (!response.ok) {
                    if (response.status === 404) {
                        setError("Job not found. It may have been deleted.");
                        return;
                    }
                    throw new Error("Failed to get status");
                }

                const data: JobStatus = await response.json();
                setJob(data);
                retryCount = 0; // Reset retry count on success

                if (data.status === "completed") {
                    // Redirect to preview after short delay
                    setTimeout(() => window.location.replace(`/preview/${jobId}`), 1500);
                } else if (data.status === "failed") {
                    setError(data.error || "Generation failed");
                } else {
                    // Continue polling
                    setTimeout(pollStatus, 2000);
                }
            } catch (err) {
                retryCount++;
                console.warn(`Status poll failed (attempt ${retryCount}/${maxRetries}):`, err);

                if (retryCount < maxRetries) {
                    // Retry with exponential backoff
                    setTimeout(pollStatus, 1000 * retryCount);
                } else {
                    setError("Failed to connect to backend. Please check if the server is running.");
                }
            }
        };

        pollStatus();
    }, [jobId, router]);

    // Get panel grid dimensions (for preview purposes)
    const getPanelGrid = () => {
        const layout = job?.layout || "dynamic";
        // For dynamic layout, we don't know the exact grid - show flexible preview
        if (layout === "dynamic") return { cols: 2, rows: 2, dynamic: true };
        if (layout === "2x2") return { cols: 2, rows: 2, dynamic: false };
        if (layout === "2x3") return { cols: 2, rows: 3, dynamic: false };
        if (layout === "3x3") return { cols: 3, rows: 3, dynamic: false };
        if (layout === "full") return { cols: 1, rows: 1, dynamic: false };
        return { cols: 2, rows: 2, dynamic: true };
    };

    const grid = getPanelGrid();

    // Calculate current panel based on completed previews (exclude "loading" placeholders)
    const completedPanels = (job?.panel_previews || []).filter(p => p && p !== "loading").length;
    const currentPanelDisplay = Math.min(completedPanels + 1, job?.total_panels || 1);

    return (
        <div className="min-h-screen bg-[#0a110e] flex flex-col">
            {/* Header */}
            <header className="z-20 flex items-center justify-between border-b border-white/5 bg-[#0a110e]/80 px-8 py-4 backdrop-blur-md">
                <Link href="/" className="flex items-center gap-4 text-white">
                    <div className="flex size-8 items-center justify-center rounded-lg bg-[#38e07b]/20 text-[#38e07b]">
                        <span className="material-symbols-outlined">auto_stories</span>
                    </div>
                    <h2 className="text-white text-lg font-bold">MangaGen<span className="text-[#38e07b]">.AI</span></h2>
                </Link>
                <div className="text-white/50 text-sm">
                    Job: <span className="text-[#38e07b] font-mono">{jobId}</span>
                </div>
            </header>

            {/* Main Content - Two Column Layout */}
            <main className="flex-1 grid lg:grid-cols-12 gap-6 p-6 max-w-7xl mx-auto w-full">
                {/* Left Column - Progress */}
                <div className="lg:col-span-5 flex flex-col gap-6">
                    {/* Status Card */}
                    <div className="glass-panel rounded-2xl p-6">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="relative w-16 h-16">
                                <div className={`absolute inset-0 rounded-full ${job?.status === "completed" ? "bg-[#38e07b]/20" : job?.status === "failed" ? "bg-red-500/20" : "bg-[#38e07b]/20 animate-ping"}`}></div>
                                <div className="relative w-full h-full bg-[#16261e] rounded-full flex items-center justify-center border border-[#38e07b]/30">
                                    <span className={`material-symbols-outlined text-2xl ${job?.status === "completed" ? "text-[#38e07b]" : job?.status === "failed" ? "text-red-400" : "text-[#38e07b] animate-pulse"}`}>
                                        {job?.status === "completed" ? "check_circle" : job?.status === "failed" ? "error" : "auto_fix_high"}
                                    </span>
                                </div>
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-white">
                                    {job?.status === "completed" ? "Generation Complete!" : job?.status === "failed" ? "Generation Failed" : "Crafting your manga..."}
                                </h1>
                                <p className="text-white/50 text-sm">{job?.current_step || "Starting..."}</p>
                            </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="mb-2 flex justify-between text-sm">
                            <span className="text-white/50">Overall Progress</span>
                            <span className="text-[#38e07b] font-bold">{job?.progress || 0}%</span>
                        </div>
                        <div className="w-full bg-white/5 rounded-full h-3 mb-4 overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-[#38e07b] to-[#6effa8] rounded-full transition-all duration-500"
                                style={{ width: `${job?.progress || 0}%` }}
                            />
                        </div>
                        {job?.total_panels && (
                            <p className="text-white/40 text-sm">
                                Processing panel {currentPanelDisplay} of {job.total_panels}
                            </p>
                        )}
                    </div>

                    {/* Timeline */}
                    <div className="glass-panel rounded-2xl p-6">
                        <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                            <span className="material-symbols-outlined text-[#38e07b]">timeline</span>
                            Progress Timeline
                        </h3>
                        <div className="space-y-3">
                            {(job?.steps || [
                                { name: "Story planning", status: "pending" },
                                { name: "Generating panels", status: "pending" },
                                { name: "Composing pages", status: "pending" },
                                { name: "Generating cover", status: "pending" },
                                { name: "Finalizing", status: "pending" },
                            ]).map((step, idx) => (
                                <div key={step.name} className="flex items-center gap-3">
                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center transition-colors ${step.status === "completed" ? "bg-[#38e07b]" :
                                        step.status === "in_progress" ? "bg-[#38e07b]/30 border-2 border-[#38e07b]" :
                                            "bg-white/5 border border-white/10"
                                        }`}>
                                        <span className={`material-symbols-outlined text-sm ${step.status === "completed" ? "text-black" :
                                            step.status === "in_progress" ? "text-[#38e07b]" :
                                                "text-white/30"
                                            }`}>
                                            {step.status === "completed" ? "check" : step.status === "in_progress" ? "pending" : "circle"}
                                        </span>
                                    </div>
                                    <span className={`text-sm flex-1 ${step.status === "completed" ? "text-[#38e07b]" :
                                        step.status === "in_progress" ? "text-white" :
                                            "text-white/30"
                                        }`}>
                                        {step.name}
                                    </span>
                                    {step.duration && <span className="text-white/30 text-xs">{step.duration}</span>}
                                    {step.status === "in_progress" && (
                                        <span className="text-[#38e07b] text-xs animate-pulse">Processing...</span>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Terminal Log */}
                    <div className="glass-panel rounded-2xl p-6 flex-1">
                        <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                            <span className="material-symbols-outlined text-[#38e07b]">terminal</span>
                            Generation Log
                        </h3>
                        <div
                            ref={logRef}
                            className="bg-black/30 rounded-lg p-4 h-40 overflow-y-auto font-mono text-xs space-y-1"
                        >
                            {(job?.log_messages || []).map((msg, idx) => (
                                <div key={idx} className={`${msg.includes("✅") ? "text-[#38e07b]" : msg.includes("❌") ? "text-red-400" : "text-white/60"}`}>
                                    {msg}
                                </div>
                            ))}
                            {job?.status === "generating" && (
                                <div className="text-[#38e07b] animate-pulse">_</div>
                            )}
                        </div>
                    </div>

                    {/* Cancel Button */}
                    {job?.status === "generating" && (
                        <button className="w-full py-3 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 font-bold text-sm transition-all flex items-center justify-center gap-2">
                            <span className="material-symbols-outlined text-lg">cancel</span>
                            Cancel Generation
                        </button>
                    )}

                    {/* Error Display */}
                    {error && (
                        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                            {error}
                            <Link href="/create" className="block mt-2 text-[#38e07b] hover:underline">
                                ← Back to Create
                            </Link>
                        </div>
                    )}
                </div>

                {/* Right Column - Live Preview */}
                <div className="lg:col-span-7 flex flex-col gap-6">
                    <div className="glass-panel rounded-2xl p-6 flex-1">
                        <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                            <span className="material-symbols-outlined text-[#38e07b]">preview</span>
                            Live Preview
                        </h3>

                        {/* Panel Grid - V5 Sliding Window with Loading Skeletons */}
                        <div className="grid grid-cols-2 gap-3 max-w-md mx-auto">
                            {(() => {
                                const allPanels = job?.panel_previews || [];
                                const completedCount = allPanels.filter(p => p && p !== "loading").length;

                                // Sliding window: show last 6 items (including loading)
                                // If we have completed panels, show mix of recent completed + upcoming loading
                                const maxVisible = 6;
                                let visiblePanels: { preview: string; index: number }[] = [];

                                // Find the "window" - start from first loading or recent completed
                                const firstLoadingIdx = allPanels.findIndex(p => p === "loading");
                                let startIdx = Math.max(0, completedCount - 2); // Show 2 completed + rest loading

                                if (firstLoadingIdx === -1) {
                                    // All complete - show last 6
                                    startIdx = Math.max(0, allPanels.length - maxVisible);
                                }

                                for (let i = startIdx; i < Math.min(startIdx + maxVisible, allPanels.length); i++) {
                                    visiblePanels.push({ preview: allPanels[i], index: i });
                                }

                                return visiblePanels.map(({ preview, index }) => {
                                    const isLoading = preview === "loading";
                                    const isEmpty = !preview;

                                    if (isLoading || isEmpty) {
                                        // Loading skeleton with spinner
                                        const isCurrentlyGenerating = index === completedCount;
                                        return (
                                            <div
                                                key={index}
                                                className={`rounded-xl overflow-hidden flex items-center justify-center transition-all duration-500 ${isCurrentlyGenerating
                                                    ? "border-2 border-[#38e07b] ring-2 ring-[#38e07b]/30 bg-[#1a3326]"
                                                    : "border border-white/10 bg-[#16261e]/50"
                                                    }`}
                                                style={{ aspectRatio: '1/1.2' }}
                                            >
                                                <div className="flex flex-col items-center gap-2">
                                                    <span className={`material-symbols-outlined text-2xl ${isCurrentlyGenerating ? "text-[#38e07b] animate-spin" : "text-white/20"
                                                        }`}>
                                                        {isCurrentlyGenerating ? "autorenew" : "image"}
                                                    </span>
                                                    <span className={`text-xs font-medium ${isCurrentlyGenerating ? "text-[#38e07b]" : "text-white/30"}`}>
                                                        Panel {index + 1}
                                                    </span>
                                                    {isCurrentlyGenerating && (
                                                        <span className="text-white/50 text-xs animate-pulse">Rendering...</span>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    }

                                    // Completed panel with fade-in
                                    return (
                                        <div
                                            key={index}
                                            className="rounded-xl border-2 border-[#264532] bg-[#16261e] overflow-hidden animate-fade-in shadow-lg"
                                            style={{ aspectRatio: '1/1.2' }}
                                        >
                                            <img
                                                src={`${API_URL}${preview}`}
                                                alt={`Panel ${index + 1}`}
                                                className="w-full h-full object-cover"
                                            />
                                        </div>
                                    );
                                });
                            })()}
                        </div>

                        {/* Panel count info */}
                        <div className="mt-4 text-center space-y-1">
                            <p className="text-white font-medium">
                                <span className="text-[#38e07b]">{(job?.panel_previews || []).filter(p => p && p !== "loading").length}</span>
                                <span className="text-white/50"> of </span>
                                <span className="text-[#38e07b]">{job?.total_panels || "..."}</span>
                                <span className="text-white/50"> panels complete</span>
                            </p>
                            {(job?.panel_previews?.length || 0) > 6 && (
                                <p className="text-white/40 text-xs flex items-center justify-center gap-1">
                                    <span className="material-symbols-outlined text-sm">view_carousel</span>
                                    Showing recent panels (sliding window)
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Success - Auto redirect notice */}
                    {job?.status === "completed" && (
                        <div className="p-6 bg-[#38e07b]/10 border border-[#38e07b]/30 rounded-2xl text-center">
                            <span className="material-symbols-outlined text-4xl text-[#38e07b] mb-2 block">rocket_launch</span>
                            <h3 className="text-white font-bold text-lg mb-1">Generation Complete!</h3>
                            <p className="text-[#38e07b] text-sm">Redirecting to preview...</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
