"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { API_URL } from "@/config";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [isRegister, setIsRegister] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
            const response = await fetch(`${API_URL}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Save token to localStorage
                localStorage.setItem("mangagen_token", data.token);
                localStorage.setItem("mangagen_user", JSON.stringify(data.user));
                router.push("/dashboard");
            } else {
                setError(data.detail || "Authentication failed");
            }
        } catch (err) {
            setError("Connection failed. Is the server running?");
        } finally {
            setLoading(false);
        }
    };

    // Quick demo mode - no auth required
    const handleDemoMode = () => {
        localStorage.setItem("mangagen_demo", "true");
        router.push("/dashboard");
    };

    return (
        <div className="min-h-screen bg-[#0a110e] flex items-center justify-center p-4">
            {/* Background effects */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-[#38e07b]/10 rounded-full blur-[150px]"></div>
                <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[120px]"></div>
            </div>

            <div className="w-full max-w-md z-10">
                {/* Logo */}
                <div className="text-center mb-8">
                    <Link href="/" className="inline-flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-[#38e07b] flex items-center justify-center shadow-[0_0_30px_-5px_rgba(56,224,123,0.4)]">
                            <span className="material-symbols-outlined text-2xl text-[#0a110e]">auto_stories</span>
                        </div>
                        <div className="text-left">
                            <h1 className="text-white text-2xl font-bold">MangaGen</h1>
                            <p className="text-[#38e07b]/80 text-xs uppercase tracking-wider">AI Studio</p>
                        </div>
                    </Link>
                </div>

                {/* Login Card */}
                <div className="bg-[#16261e]/60 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                    <h2 className="text-2xl font-bold text-white mb-2 text-center">
                        {isRegister ? "Create Account" : "Welcome Back"}
                    </h2>
                    <p className="text-gray-400 text-center mb-8">
                        {isRegister
                            ? "Start creating amazing manga with AI"
                            : "Continue your manga creation journey"}
                    </p>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-white/70">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 bg-[#0a110e] border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[#38e07b]/50 focus:ring-1 focus:ring-[#38e07b]/50 transition-all"
                                placeholder="you@example.com"
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-white/70">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 bg-[#0a110e] border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[#38e07b]/50 focus:ring-1 focus:ring-[#38e07b]/50 transition-all"
                                placeholder="••••••••"
                                required
                            />
                        </div>

                        {error && (
                            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 text-red-400 text-sm text-center">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 rounded-full bg-[#38e07b] hover:bg-[#2bc968] text-[#0a110e] font-bold transition-all shadow-[0_0_20px_-5px_rgba(56,224,123,0.4)] hover:shadow-[0_0_30px_-5px_rgba(56,224,123,0.6)] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <span className="animate-spin">⏳</span>
                                    {isRegister ? "Creating..." : "Signing in..."}
                                </span>
                            ) : (
                                isRegister ? "Create Account" : "Sign In"
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <button
                            onClick={() => setIsRegister(!isRegister)}
                            className="text-gray-400 hover:text-white text-sm transition-colors"
                        >
                            {isRegister ? "Already have an account? Sign in" : "Don't have an account? Register"}
                        </button>
                    </div>

                    <div className="relative mt-8">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-white/10"></div>
                        </div>
                        <div className="relative flex justify-center text-xs">
                            <span className="px-3 bg-[#16261e] text-gray-500">or</span>
                        </div>
                    </div>

                    {/* Demo Mode */}
                    <button
                        onClick={handleDemoMode}
                        className="mt-6 w-full py-3 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium transition-all flex items-center justify-center gap-2"
                    >
                        <span className="material-symbols-outlined text-lg">play_arrow</span>
                        Continue as Guest
                    </button>
                </div>

                {/* Footer */}
                <p className="text-center text-gray-500 text-xs mt-6">
                    By continuing, you agree to our Terms of Service
                </p>
            </div>
        </div>
    );
}
