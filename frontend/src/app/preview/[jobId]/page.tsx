"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface JobStatus {
    job_id: string;
    status: string;
    result?: {
        title: string;
        pages: { page_number: number; page_image: string }[];
        pdf: string;
        elapsed_seconds: number;
    };
}

export default function PreviewPage() {
    const params = useParams();
    const jobId = params.jobId as string;

    const [job, setJob] = useState<JobStatus | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [loading, setLoading] = useState(true);

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

    const downloadPDF = () => {
        window.open(`http://localhost:8000/api/download/${jobId}/pdf`, "_blank");
    };

    const downloadPNG = () => {
        window.open(`http://localhost:8000/api/download/${jobId}/png`, "_blank");
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a110e] flex items-center justify-center">
                <div className="text-[#38e07b] animate-pulse">Loading...</div>
            </div>
        );
    }

    const pages = job?.result?.pages || [];
    const totalPages = pages.length;

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
                <div className="flex items-center gap-4">
                    <Link href="/create" className="text-white/70 hover:text-white text-sm font-medium transition-colors flex items-center gap-1">
                        <span className="material-symbols-outlined text-sm">add</span>
                        Create New
                    </Link>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 flex">
                {/* Preview Area */}
                <div className="flex-1 flex items-center justify-center p-8 bg-[#0d1611]">
                    <div className="relative max-w-3xl w-full">
                        {/* Manga Page Preview */}
                        <div className="aspect-[3/4] bg-[#16261e] rounded-xl overflow-hidden border border-[#264532] shadow-2xl">
                            {job?.result && pages.length > 0 ? (
                                <img
                                    src={`http://localhost:8000/api/preview/${jobId}/${currentPage}`}
                                    alt={`Page ${currentPage}`}
                                    className="w-full h-full object-contain"
                                />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-white/30">
                                    <span className="material-symbols-outlined text-6xl">image</span>
                                </div>
                            )}
                        </div>

                        {/* Page Navigation */}
                        {totalPages > 1 && (
                            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-black/80 backdrop-blur rounded-full px-4 py-2">
                                <button
                                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                    disabled={currentPage === 1}
                                    className="text-white/70 hover:text-white disabled:text-white/20 transition-colors"
                                >
                                    <span className="material-symbols-outlined">chevron_left</span>
                                </button>
                                <span className="text-white text-sm font-medium">
                                    {currentPage} / {totalPages}
                                </span>
                                <button
                                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                    disabled={currentPage === totalPages}
                                    className="text-white/70 hover:text-white disabled:text-white/20 transition-colors"
                                >
                                    <span className="material-symbols-outlined">chevron_right</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar */}
                <div className="w-80 border-l border-white/5 bg-[#0a110e] p-6 flex flex-col">
                    <h1 className="text-xl font-bold text-white mb-1">{job?.result?.title || "Untitled"}</h1>
                    <p className="text-white/50 text-sm mb-6">{totalPages} page(s)</p>

                    {/* Page Thumbnails */}
                    <div className="flex-1 overflow-y-auto mb-6">
                        <h3 className="text-white/50 text-xs uppercase tracking-wider mb-3">Pages</h3>
                        <div className="grid grid-cols-2 gap-3">
                            {pages.map((page) => (
                                <button
                                    key={page.page_number}
                                    onClick={() => setCurrentPage(page.page_number)}
                                    className={`aspect-[3/4] rounded-lg overflow-hidden border-2 transition-all ${currentPage === page.page_number
                                            ? "border-[#38e07b] shadow-neon"
                                            : "border-white/10 hover:border-white/30"
                                        }`}
                                >
                                    <img
                                        src={`http://localhost:8000/api/preview/${jobId}/${page.page_number}`}
                                        alt={`Page ${page.page_number}`}
                                        className="w-full h-full object-cover"
                                    />
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Download Options */}
                    <div className="space-y-3">
                        <h3 className="text-white/50 text-xs uppercase tracking-wider">Download</h3>
                        <button
                            onClick={downloadPDF}
                            className="w-full py-3 rounded-lg bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] font-bold text-sm transition-all flex items-center justify-center gap-2"
                        >
                            <span className="material-symbols-outlined text-lg">picture_as_pdf</span>
                            Download PDF
                        </button>
                        <button
                            onClick={downloadPNG}
                            className="w-full py-3 rounded-lg bg-white/5 hover:bg-white/10 text-white border border-white/10 font-bold text-sm transition-all flex items-center justify-center gap-2"
                        >
                            <span className="material-symbols-outlined text-lg">image</span>
                            Download PNG
                        </button>
                    </div>

                    {/* Stats */}
                    {job?.result?.elapsed_seconds && (
                        <div className="mt-6 pt-6 border-t border-white/5">
                            <p className="text-white/30 text-xs">
                                Generated in {Math.round(job.result.elapsed_seconds / 60)} min
                            </p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
