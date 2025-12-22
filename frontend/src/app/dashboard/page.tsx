"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Project {
    job_id: string;
    manga_title?: string;  // Series name (LLM generated)
    title: string;         // Chapter title
    pages: number;
    style: string;
    created_at: string;
    updated_at: string;
    cover_url?: string;
}

interface User {
    email: string;
    id: string;
    plan: string;
}

export default function DashboardPage() {
    const router = useRouter();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [filter, setFilter] = useState<"all" | "drafts" | "published">("all");
    const [sortBy, setSortBy] = useState<"newest" | "oldest">("newest");
    const [user, setUser] = useState<User | null>(null);
    const [showProfileMenu, setShowProfileMenu] = useState(false);

    // Continue modal states
    const [showContinueModal, setShowContinueModal] = useState(false);
    const [continueProject, setContinueProject] = useState<Project | null>(null);
    const [continuePages, setContinuePages] = useState(3);
    const [continueDirection, setContinueDirection] = useState("");
    const [continuing, setContinuing] = useState(false);

    // Settings modal states
    const [showSettings, setShowSettings] = useState(false);
    const [apiKeys, setApiKeys] = useState({
        GROQ_API_KEY: "",
        NVIDIA_API_KEY: "",
        GEMINI_API_KEY: ""
    });

    // Delete confirmation modal states
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
    const [deleting, setDeleting] = useState(false);

    // Load settings
    useEffect(() => {
        const storedKeys = localStorage.getItem("mangagen_api_keys");
        if (storedKeys) {
            setApiKeys(JSON.parse(storedKeys));
        }
    }, []);

    const handleSaveSettings = () => {
        localStorage.setItem("mangagen_api_keys", JSON.stringify(apiKeys));
        localStorage.setItem("mangagen_keys_configured", "true"); // Flag for other components
        setShowSettings(false);
        alert("Settings saved!");
    };

    // Handle continue button click
    const handleContinue = async () => {
        if (!continueProject) return;
        setContinuing(true);

        try {
            const response = await fetch(`http://localhost:8000/api/projects/${continueProject.job_id}/continue`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    pages: continuePages,
                    user_direction: continueDirection || null
                })
            });

            if (response.ok) {
                const data = await response.json();
                // Navigate to generation progress page (not preview!)
                router.push(`/generate/${data.job_id}`);
            } else {
                const err = await response.json();
                alert(err.detail || "Failed to start continuation");
            }
        } catch (error) {
            console.error("Continue failed:", error);
            alert("Network error. Please try again.");
        } finally {
            setContinuing(false);
            setShowContinueModal(false);
        }
    };

    const openContinueModal = (project: Project) => {
        setContinueProject(project);
        setContinuePages(3);
        setContinueDirection("");
        setShowContinueModal(true);
    };

    // V4: Open delete confirmation modal
    const openDeleteModal = (project: Project) => {
        setProjectToDelete(project);
        setShowDeleteModal(true);
    };

    // V4: Confirm and delete project
    const confirmDelete = async () => {
        if (!projectToDelete) return;

        setDeleting(true);
        try {
            const response = await fetch(`${API_URL}/api/projects/${projectToDelete.job_id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setProjects(prev => prev.filter(p => p.job_id !== projectToDelete.job_id));
                console.log(`🗑️ Deleted project: ${projectToDelete.job_id}`);
                setShowDeleteModal(false);
                setProjectToDelete(null);
            } else {
                const err = await response.json();
                alert(err.detail || "Failed to delete project");
            }
        } catch (error) {
            console.error("Delete failed:", error);
            alert("Network error. Please try again.");
        } finally {
            setDeleting(false);
        }
    };

    // Load user from localStorage
    useEffect(() => {
        const storedUser = localStorage.getItem("mangagen_user");
        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch {
                setUser({ email: "guest@mangagen.ai", id: "guest", plan: "free" });
            }
        } else {
            setUser({ email: "guest@mangagen.ai", id: "guest", plan: "free" });
        }
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("mangagen_token");
        localStorage.removeItem("mangagen_user");
        localStorage.removeItem("mangagen_demo");
        router.push("/login");
    };

    useEffect(() => {
        // Fetch REAL projects from API
        const fetchProjects = async () => {
            try {
                const response = await fetch("http://localhost:8000/api/projects");
                if (response.ok) {
                    const data = await response.json();
                    setProjects(data.projects || []);
                    console.log(`📦 Loaded ${data.projects?.length || 0} projects from ${data.source || 'api'}`);
                }
            } catch (error) {
                console.error("Failed to fetch projects:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchProjects();
    }, []);

    const filteredProjects = projects
        .filter(p => p.title.toLowerCase().includes(searchQuery.toLowerCase()))
        .sort((a, b) => {
            if (sortBy === "newest") {
                return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
            }
            return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
        });

    const getTimeAgo = (date: string) => {
        const now = new Date();
        const then = new Date(date);
        const diff = Math.floor((now.getTime() - then.getTime()) / 1000 / 60);
        if (diff < 60) return `${diff}m ago`;
        if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
        return `${Math.floor(diff / 1440)}d ago`;
    };

    return (
        <div className="min-h-screen bg-[#0a110e] flex">
            {/* Sidebar */}
            <aside className="w-72 hidden md:flex flex-col h-screen border-r border-white/5 bg-[#0a110e]/90 backdrop-blur-md sticky top-0">
                <div className="flex flex-col h-full p-6 justify-between">
                    {/* Logo & Nav */}
                    <div className="flex flex-col gap-8">
                        {/* Logo */}
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-[#38e07b] flex items-center justify-center shadow-[0_0_20px_-5px_rgba(56,224,123,0.3)]">
                                <span className="material-symbols-outlined text-[#0a110e]">auto_stories</span>
                            </div>
                            <div className="flex flex-col">
                                <h1 className="text-white text-lg font-bold leading-tight">MangaGen</h1>
                                <p className="text-[#38e07b]/80 text-xs font-medium uppercase tracking-wider">AI Studio</p>
                            </div>
                        </div>

                        {/* Navigation */}
                        <nav className="flex flex-col gap-2">
                            <Link
                                href="/dashboard"
                                className="flex items-center gap-3 px-4 py-3 rounded-full bg-[#38e07b]/10 text-[#38e07b] shadow-[0_0_20px_-5px_rgba(56,224,123,0.15)]"
                            >
                                <span className="material-symbols-outlined">dashboard</span>
                                <span className="text-sm font-semibold">Dashboard</span>
                            </Link>
                            <Link
                                href="/create"
                                className="flex items-center gap-3 px-4 py-3 rounded-full text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                            >
                                <span className="material-symbols-outlined">auto_awesome</span>
                                <span className="text-sm font-medium">Generate</span>
                            </Link>
                            <button className="flex items-center gap-3 px-4 py-3 rounded-full text-gray-400 hover:text-white hover:bg-white/5 transition-all w-full text-left">
                                <span className="material-symbols-outlined">face</span>
                                <span className="text-sm font-medium">Characters</span>
                            </button>
                            <button className="flex items-center gap-3 px-4 py-3 rounded-full text-gray-400 hover:text-white hover:bg-white/5 transition-all w-full text-left">
                                <span className="material-symbols-outlined">groups</span>
                                <span className="text-sm font-medium">Community</span>
                            </button>
                            <button className="flex items-center gap-3 px-4 py-3 rounded-full text-gray-400 hover:text-white hover:bg-white/5 transition-all w-full text-left">
                                <span className="material-symbols-outlined">settings</span>
                                <span className="text-sm font-medium">Settings</span>
                            </button>
                        </nav>
                    </div>

                    {/* User Profile with Dropdown */}
                    <div className="pt-6 border-t border-white/5 relative">
                        <div
                            onClick={() => setShowProfileMenu(!showProfileMenu)}
                            className="flex items-center gap-3 px-2 py-2 rounded-full hover:bg-white/5 cursor-pointer transition-colors"
                        >
                            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#38e07b] to-[#7c3aed] border-2 border-[#38e07b] flex items-center justify-center">
                                <span className="text-white font-bold text-sm">
                                    {user?.email?.charAt(0).toUpperCase() || "G"}
                                </span>
                            </div>
                            <div className="flex flex-col overflow-hidden">
                                <p className="text-white text-sm font-semibold truncate">
                                    {user?.email?.split("@")[0] || "Guest"}
                                </p>
                                <p className="text-gray-400 text-xs truncate capitalize">
                                    {user?.plan || "Free"} Plan
                                </p>
                            </div>
                            <span className={`material-symbols-outlined ml-auto text-gray-500 transition-transform ${showProfileMenu ? "rotate-180" : ""}`}>
                                expand_more
                            </span>
                        </div>

                        {/* Dropdown Menu */}
                        {showProfileMenu && (
                            <div className="absolute bottom-full left-0 right-0 mb-2 bg-[#16261e] border border-white/10 rounded-xl shadow-xl overflow-hidden">
                                <div className="px-4 py-3 border-b border-white/5">
                                    <p className="text-white text-sm font-medium truncate">{user?.email}</p>
                                    <p className="text-gray-500 text-xs">Signed in</p>
                                </div>
                                <Link href="/login" className="flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                                    <span className="material-symbols-outlined text-lg">person</span>
                                    <span className="text-sm">Profile</span>
                                </Link>
                                <button
                                    onClick={() => setShowSettings(true)}
                                    className="flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 transition-colors w-full"
                                >
                                    <span className="material-symbols-outlined text-lg">settings</span>
                                    <span className="text-sm">Settings</span>
                                </button>
                                <button
                                    onClick={handleLogout}
                                    className="flex items-center gap-3 px-4 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors w-full"
                                >
                                    <span className="material-symbols-outlined text-lg">logout</span>
                                    <span className="text-sm">Log out</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col min-h-screen overflow-y-auto bg-gradient-to-br from-[#0a110e] to-[#0a120d]">
                {/* Decorative glow */}
                <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-[#38e07b]/5 rounded-full blur-[120px] pointer-events-none"></div>

                <div className="flex-1 px-8 py-8 md:px-12 md:py-10 max-w-[1600px] mx-auto w-full z-10">
                    {/* Header */}
                    <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 mb-10">
                        <div className="flex flex-col gap-1">
                            <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight">My Projects</h2>
                            <p className="text-gray-400 text-base">Welcome back, continue your manga creation journey.</p>
                        </div>
                        <div className="flex flex-wrap items-center gap-4 w-full lg:w-auto">
                            {/* Search */}
                            <div className="relative w-full sm:w-80 group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <span className="material-symbols-outlined text-gray-500 group-focus-within:text-[#38e07b] transition-colors">search</span>
                                </div>
                                <input
                                    type="text"
                                    placeholder="Find a story..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="block w-full pl-10 pr-3 py-3 border border-white/5 rounded-full bg-[#16261e]/50 text-gray-300 placeholder-gray-500 focus:outline-none focus:bg-[#16261e] focus:border-[#38e07b]/50 focus:ring-1 focus:ring-[#38e07b]/50 text-sm transition-all"
                                />
                            </div>
                            {/* Create Button */}
                            <Link
                                href="/create"
                                className="flex items-center justify-center gap-2 bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] px-6 py-3 rounded-full font-bold transition-all shadow-[0_0_20px_-5px_rgba(56,224,123,0.3)] hover:shadow-[0_0_25px_-5px_rgba(56,224,123,0.5)] active:scale-95 w-full sm:w-auto"
                            >
                                <span className="material-symbols-outlined text-[20px] font-bold">add</span>
                                <span>Create Project</span>
                            </Link>
                        </div>
                    </header>

                    {/* Filters */}
                    <div className="flex items-center gap-3 mb-8 overflow-x-auto pb-2">
                        <button
                            onClick={() => setFilter("all")}
                            className={`whitespace-nowrap px-4 py-2 rounded-full text-sm font-medium border transition-all ${filter === "all"
                                ? "bg-[#38e07b]/20 text-[#38e07b] border-[#38e07b]/20"
                                : "bg-[#16261e] text-gray-400 hover:text-white hover:bg-white/10 border-transparent"
                                }`}
                        >
                            All Projects
                        </button>
                        <button
                            onClick={() => setFilter("drafts")}
                            className={`whitespace-nowrap px-4 py-2 rounded-full text-sm font-medium border transition-all ${filter === "drafts"
                                ? "bg-[#38e07b]/20 text-[#38e07b] border-[#38e07b]/20"
                                : "bg-[#16261e] text-gray-400 hover:text-white hover:bg-white/10 border-transparent"
                                }`}
                        >
                            Drafts
                        </button>
                        <button
                            onClick={() => setFilter("published")}
                            className={`whitespace-nowrap px-4 py-2 rounded-full text-sm font-medium border transition-all ${filter === "published"
                                ? "bg-[#38e07b]/20 text-[#38e07b] border-[#38e07b]/20"
                                : "bg-[#16261e] text-gray-400 hover:text-white hover:bg-white/10 border-transparent"
                                }`}
                        >
                            Published
                        </button>

                        <div className="flex-grow"></div>

                        <div className="hidden sm:flex items-center gap-2">
                            <span className="text-xs text-gray-500 uppercase font-bold tracking-wider">Sort by:</span>
                            <button
                                onClick={() => setSortBy(sortBy === "newest" ? "oldest" : "newest")}
                                className="flex items-center gap-1 text-sm text-gray-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-white/5 transition-colors"
                            >
                                {sortBy === "newest" ? "Newest" : "Oldest"}
                                <span className="material-symbols-outlined text-[18px]">expand_more</span>
                            </button>
                        </div>
                    </div>

                    {/* Projects Grid */}
                    {loading ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="aspect-[3/4] bg-[#16261e] rounded-2xl animate-pulse"></div>
                            ))}
                        </div>
                    ) : filteredProjects.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-20 text-center">
                            <span className="material-symbols-outlined text-6xl text-white/20 mb-4">folder_open</span>
                            <h3 className="text-white text-xl font-bold mb-2">No projects yet</h3>
                            <p className="text-gray-400 mb-6">Create your first manga to get started!</p>
                            <Link
                                href="/create"
                                className="flex items-center gap-2 bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] px-6 py-3 rounded-full font-bold transition-all"
                            >
                                <span className="material-symbols-outlined">add</span>
                                Create Project
                            </Link>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-12">
                            {filteredProjects.map((project) => (
                                <div
                                    key={project.job_id}
                                    className="group relative flex flex-col bg-[#16261e]/40 backdrop-blur-xl border border-white/5 rounded-2xl overflow-hidden hover:border-[#38e07b]/30 transition-all duration-300 hover:shadow-[0_0_20px_-5px_rgba(56,224,123,0.15)] hover:-translate-y-1"
                                >
                                    {/* Cover Image */}
                                    <div className="relative aspect-[3/4] w-full overflow-hidden bg-gradient-to-br from-[#264532] to-[#16261e]">
                                        {project.cover_url ? (
                                            <img
                                                src={`http://localhost:8000${project.cover_url}`}
                                                alt={project.title}
                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center">
                                                <span className="material-symbols-outlined text-6xl text-white/10">auto_stories</span>
                                            </div>
                                        )}
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity"></div>

                                        {/* Page Count Badge */}
                                        <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-full border border-white/10 flex items-center gap-1">
                                            <span className="material-symbols-outlined text-[14px] text-[#38e07b]">layers</span>
                                            <span className="text-xs font-medium text-white">{Array.isArray(project.pages) ? project.pages.length : project.pages} Pgs</span>
                                        </div>

                                        {/* Style Badge */}
                                        <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-full border border-white/10">
                                            <span className="text-xs font-medium text-white">
                                                {project.style === "bw_manga" ? "B&W" : "Color"}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Content */}
                                    <div className="p-5 flex flex-col flex-1 gap-3">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <h3 className="text-white font-bold text-lg leading-tight group-hover:text-[#38e07b] transition-colors">
                                                    {project.manga_title || project.title}
                                                </h3>
                                                {project.manga_title && project.manga_title !== project.title && (
                                                    <p className="text-gray-400 text-xs mt-0.5">
                                                        Ch. 1: {project.title}
                                                    </p>
                                                )}
                                                <p className="text-gray-500 text-xs mt-1">
                                                    Edited {getTimeAgo(project.updated_at)}
                                                </p>
                                            </div>
                                            <button className="text-gray-500 hover:text-white transition-colors">
                                                <span className="material-symbols-outlined">more_vert</span>
                                            </button>
                                        </div>

                                        {/* Actions */}
                                        <div className="mt-auto pt-3 flex items-center gap-2">
                                            <Link
                                                href={`/preview/${project.job_id}`}
                                                className="flex-1 bg-white/5 hover:bg-[#38e07b] hover:text-black text-white text-sm font-semibold py-2 px-4 rounded-full transition-all flex items-center justify-center gap-2 group/btn"
                                            >
                                                <span>Edit</span>
                                                <span className="material-symbols-outlined text-[16px] group-hover/btn:translate-x-0.5 transition-transform">arrow_forward</span>
                                            </Link>
                                            <button
                                                onClick={() => openContinueModal(project)}
                                                className="w-9 h-9 flex items-center justify-center rounded-full bg-[#38e07b]/20 hover:bg-[#38e07b] hover:text-black text-[#38e07b] transition-all"
                                                title="Continue Story"
                                            >
                                                <span className="material-symbols-outlined text-[18px]">add</span>
                                            </button>
                                            <button
                                                onClick={() => openDeleteModal(project)}
                                                className="w-9 h-9 flex items-center justify-center rounded-full bg-white/5 hover:bg-red-500/20 hover:text-red-500 text-gray-400 transition-all"
                                                title="Delete Project"
                                            >
                                                <span className="material-symbols-outlined text-[18px]">delete</span>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {/* Create New Card */}
                            <Link
                                href="/create"
                                className="group flex flex-col items-center justify-center aspect-[3/4] bg-[#16261e]/20 border-2 border-dashed border-white/10 rounded-2xl hover:border-[#38e07b]/50 hover:bg-[#38e07b]/5 transition-all"
                            >
                                <span className="material-symbols-outlined text-4xl text-white/20 group-hover:text-[#38e07b] transition-colors mb-3">add_circle</span>
                                <span className="text-white/50 group-hover:text-[#38e07b] font-medium">New Project</span>
                            </Link>
                        </div>
                    )}
                </div>
            </main>

            {/* Continue Modal */}
            {showContinueModal && continueProject && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[100]">
                    <div className="bg-[#16261e] rounded-2xl p-8 max-w-lg w-full mx-4 border border-[#264532]">
                        <div className="flex items-center gap-3 mb-6">
                            <span className="material-symbols-outlined text-3xl text-[#38e07b]">auto_stories</span>
                            <div>
                                <h3 className="text-xl font-bold text-white">Continue Story</h3>
                                <p className="text-gray-400 text-sm">{continueProject.title}</p>
                            </div>
                        </div>

                        <div className="space-y-5">
                            {/* Page Count */}
                            <div>
                                <label className="text-sm font-medium text-white block mb-2">
                                    Number of new pages
                                </label>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="range"
                                        min={1}
                                        max={10}
                                        value={continuePages}
                                        onChange={(e) => setContinuePages(parseInt(e.target.value))}
                                        className="flex-1 accent-[#38e07b]"
                                    />
                                    <span className="text-[#38e07b] font-bold text-lg w-8 text-center">{continuePages}</span>
                                </div>
                            </div>

                            {/* Direction (Optional) */}
                            <div>
                                <label className="text-sm font-medium text-white block mb-2">
                                    Story direction <span className="text-gray-500">(optional)</span>
                                </label>
                                <textarea
                                    value={continueDirection}
                                    onChange={(e) => setContinueDirection(e.target.value)}
                                    placeholder="e.g., 'Introduce a new villain' or 'Show a training montage'"
                                    className="w-full bg-[#0a110e] border border-[#264532] rounded-lg px-4 py-3 text-white placeholder:text-gray-500 focus:border-[#38e07b] focus:outline-none resize-none"
                                    rows={3}
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 mt-8">
                            <button
                                onClick={() => setShowContinueModal(false)}
                                className="flex-1 py-3 rounded-lg border border-white/20 text-white hover:bg-white/5"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleContinue}
                                disabled={continuing}
                                className="flex-1 py-3 rounded-lg bg-[#38e07b] text-[#0a110e] font-bold hover:bg-[#2bc968] disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {continuing ? (
                                    <>
                                        <span className="material-symbols-outlined animate-spin text-lg">sync</span>
                                        Generating...
                                    </>
                                ) : (
                                    <>
                                        <span className="material-symbols-outlined text-lg">auto_awesome</span>
                                        Generate {continuePages} Pages
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal - Beautiful danger theme */}
            {showDeleteModal && projectToDelete && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100]">
                    <div className="bg-gradient-to-b from-[#1a1a2e] to-[#16161a] rounded-2xl p-8 max-w-md w-full mx-4 border border-red-500/30 shadow-[0_0_60px_rgba(239,68,68,0.2)]">
                        {/* Danger icon */}
                        <div className="flex flex-col items-center mb-6">
                            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
                                <span className="material-symbols-outlined text-4xl text-red-500">warning</span>
                            </div>
                            <h3 className="text-xl font-bold text-white text-center">Delete Project?</h3>
                            <p className="text-gray-400 text-center mt-1">
                                &quot;{projectToDelete.manga_title || projectToDelete.title}&quot;
                            </p>
                        </div>

                        {/* Warning content */}
                        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6">
                            <p className="text-red-400 text-sm text-center mb-3">
                                This will permanently delete:
                            </p>
                            <ul className="text-gray-400 text-sm space-y-1">
                                <li className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-red-400 text-base">image</span>
                                    All pages and panel images
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-red-400 text-base">chat_bubble</span>
                                    All dialogues and bubbles
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-red-400 text-base">folder_delete</span>
                                    The entire project folder
                                </li>
                            </ul>
                        </div>

                        <p className="text-center text-gray-500 text-xs mb-6">
                            ⚠️ This action cannot be undone
                        </p>

                        {/* Action buttons */}
                        <div className="flex gap-3">
                            <button
                                onClick={() => {
                                    setShowDeleteModal(false);
                                    setProjectToDelete(null);
                                }}
                                disabled={deleting}
                                className="flex-1 py-3 rounded-xl border border-white/20 text-white hover:bg-white/5 transition-all disabled:opacity-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmDelete}
                                disabled={deleting}
                                className="flex-1 py-3 rounded-xl bg-red-500 text-white font-bold hover:bg-red-600 disabled:opacity-50 flex items-center justify-center gap-2 transition-all"
                            >
                                {deleting ? (
                                    <>
                                        <span className="material-symbols-outlined animate-spin text-lg">sync</span>
                                        Deleting...
                                    </>
                                ) : (
                                    <>
                                        <span className="material-symbols-outlined text-lg">delete_forever</span>
                                        Delete Forever
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Settings Modal */}
            {showSettings && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[110]">
                    <div className="bg-[#16261e] rounded-2xl p-8 max-w-lg w-full mx-4 border border-[#264532]">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <span className="material-symbols-outlined text-3xl text-gray-400">settings</span>
                                <div>
                                    <h3 className="text-xl font-bold text-white">API Settings</h3>
                                    <p className="text-gray-400 text-sm">Configure your own API keys</p>
                                </div>
                            </div>
                            <button onClick={() => setShowSettings(false)} className="text-gray-500 hover:text-white">
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium text-white block mb-2">Groq API Key</label>
                                <input
                                    type="password"
                                    value={apiKeys.GROQ_API_KEY}
                                    onChange={(e) => setApiKeys({ ...apiKeys, GROQ_API_KEY: e.target.value })}
                                    placeholder="gsk_..."
                                    className="w-full bg-[#0a110e] border border-[#264532] rounded-lg px-4 py-3 text-white placeholder:text-gray-600 focus:border-[#38e07b] focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium text-white block mb-2">NVIDIA API Key</label>
                                <input
                                    type="password"
                                    value={apiKeys.NVIDIA_API_KEY}
                                    onChange={(e) => setApiKeys({ ...apiKeys, NVIDIA_API_KEY: e.target.value })}
                                    placeholder="nvapi-..."
                                    className="w-full bg-[#0a110e] border border-[#264532] rounded-lg px-4 py-3 text-white placeholder:text-gray-600 focus:border-[#38e07b] focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium text-white block mb-2">Gemini API Key</label>
                                <input
                                    type="password"
                                    value={apiKeys.GEMINI_API_KEY}
                                    onChange={(e) => setApiKeys({ ...apiKeys, GEMINI_API_KEY: e.target.value })}
                                    placeholder="AIza..."
                                    className="w-full bg-[#0a110e] border border-[#264532] rounded-lg px-4 py-3 text-white placeholder:text-gray-600 focus:border-[#38e07b] focus:outline-none"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 mt-8">
                            <button
                                onClick={() => setShowSettings(false)}
                                className="flex-1 py-3 rounded-lg border border-white/20 text-white hover:bg-white/5"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSaveSettings}
                                className="flex-1 py-3 rounded-lg bg-[#38e07b] text-[#0a110e] font-bold hover:bg-[#2bc968]"
                            >
                                Save Settings
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
