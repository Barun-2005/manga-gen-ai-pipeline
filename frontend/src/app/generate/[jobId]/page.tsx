"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

interface JobStatus {
    job_id: string;
    status: "pending" | "generating" | "completed" | "failed";
    progress: number;
    current_step: string;
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

    const [job, setJob] = useState<JobStatus | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!jobId) return;

        const pollStatus = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/status/${jobId}`);
                if (!response.ok) throw new Error("Failed to get status");

                const data: JobStatus = await response.json();
                setJob(data);

                if (data.status === "completed") {
                    // Redirect to preview after short delay
                    setTimeout(() => router.push(`/preview/${jobId}`), 1500);
                } else if (data.status === "failed") {
                    setError(data.error || "Generation failed");
                } else {
                    // Continue polling
                    setTimeout(pollStatus, 2000);
                }
            } catch (err) {
                setError("Failed to connect to backend");
            }
        };

        pollStatus();
    }, [jobId, router]);

    const steps = [
        { name: "Story analyzed", icon: "edit_note" },
        { name: "Generating panels", icon: "image" },
        { name: "Adding dialogue", icon: "chat_bubble" },
        { name: "Composing page", icon: "grid_on" },
    ];

    const getStepStatus = (stepIdx: number) => {
        if (!job) return "pending";
        const progress = job.progress;
        const stepProgress = (stepIdx + 1) * 25;
        if (progress >= stepProgress) return "completed";
        if (progress >= stepProgress - 25) return "active";
        return "pending";
    };

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
            </header>

            {/* Main Content */}
            <main className="flex-1 flex items-center justify-center p-8">
                <div className="max-w-lg w-full">
                    {/* Progress Card */}
                    <div className="glass-panel rounded-2xl p-8 text-center">
                        {/* Animated Icon */}
                        <div className="relative w-24 h-24 mx-auto mb-6">
                            <div className="absolute inset-0 bg-[#38e07b]/20 rounded-full animate-ping"></div>
                            <div className="relative w-full h-full bg-[#16261e] rounded-full flex items-center justify-center border border-[#38e07b]/30">
                                <span className="material-symbols-outlined text-4xl text-[#38e07b] animate-pulse">
                                    {job?.status === "completed" ? "check_circle" : job?.status === "failed" ? "error" : "auto_fix_high"}
                                </span>
                            </div>
                        </div>

                        <h1 className="text-2xl font-bold text-white mb-2">
                            {job?.status === "completed" ? "Generation Complete!" : job?.status === "failed" ? "Generation Failed" : "Creating Your Manga..."}
                        </h1>
                        <p className="text-white/50 mb-8">
                            {job?.current_step || "Starting generation..."}
                        </p>

                        {/* Progress Bar */}
                        <div className="w-full bg-white/5 rounded-full h-2 mb-8 overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-[#38e07b] to-[#6effa8] rounded-full transition-all duration-500"
                                style={{ width: `${job?.progress || 0}%` }}
                            ></div>
                        </div>

                        {/* Steps */}
                        <div className="space-y-3 text-left">
                            {steps.map((step, idx) => {
                                const status = getStepStatus(idx);
                                return (
                                    <div key={step.name} className="flex items-center gap-3">
                                        <div className={`w-6 h-6 rounded-full flex items-center justify-center ${status === "completed" ? "bg-[#38e07b]" :
                                                status === "active" ? "bg-[#38e07b]/30 border border-[#38e07b]" :
                                                    "bg-white/5 border border-white/10"
                                            }`}>
                                            <span className={`material-symbols-outlined text-sm ${status === "completed" ? "text-black" :
                                                    status === "active" ? "text-[#38e07b]" :
                                                        "text-white/30"
                                                }`}>
                                                {status === "completed" ? "check" : step.icon}
                                            </span>
                                        </div>
                                        <span className={`text-sm ${status === "completed" ? "text-[#38e07b]" :
                                                status === "active" ? "text-white" :
                                                    "text-white/30"
                                            }`}>
                                            {step.name}
                                        </span>
                                        {status === "active" && (
                                            <span className="ml-auto text-xs text-[#38e07b] animate-pulse">Processing...</span>
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Error Display */}
                        {error && (
                            <div className="mt-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                {error}
                                <Link href="/create" className="block mt-2 text-[#38e07b] hover:underline">
                                    ← Back to Create
                                </Link>
                            </div>
                        )}

                        {/* Success - Auto redirect notice */}
                        {job?.status === "completed" && (
                            <div className="mt-6 p-4 bg-[#38e07b]/10 border border-[#38e07b]/30 rounded-lg text-[#38e07b] text-sm">
                                <span className="material-symbols-outlined align-middle mr-1">rocket_launch</span>
                                Redirecting to preview...
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
