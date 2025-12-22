"use client";

import { useEffect, useState } from "react";

interface Character {
    name: string;
    character_id?: string;
    appearance: string;
    personality?: string;
    role?: string;
    visual_prompt?: string;
    arc_state?: string;
}

interface PanelData {
    panel_id?: string;
    panel_number: number;
    description?: string;
    shot_type?: string;
    characters_present?: string[];
    dialogue?: {
        type: string;
        character?: string;
        text: string;
    }[];
}

interface PageData {
    page_id?: string;
    page_number: number;
    page_summary?: string;
    emotional_beat?: string;
    panels?: PanelData[];
}

interface StoryState {
    story_context?: {
        original_prompt: string;
        llm_interpretation?: string;
    };
    characters: Character[];
    chapters?: {
        chapter_id: string;
        title: string;
        summary?: string;
    }[];
    pages: PageData[];
    continuation_state?: {
        cliffhanger?: string;
        next_chapter_hook?: string;
    };
}

interface StoryViewerProps {
    jobId: string;
    currentPage: number;
    selectedPanel: number | null;
    onSelectPage?: (pageNum: number) => void;
}

export default function StoryViewer({ jobId, currentPage, selectedPanel, onSelectPage }: StoryViewerProps) {
    const [story, setStory] = useState<StoryState | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<"story" | "characters" | "current">("story");

    useEffect(() => {
        const fetchStory = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/projects/${jobId}/story`);
                if (response.ok) {
                    const data = await response.json();
                    setStory(data.story);
                } else {
                    setError("Story data not found");
                }
            } catch (err) {
                setError("Failed to load story");
            } finally {
                setLoading(false);
            }
        };
        fetchStory();
    }, [jobId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full text-gray-400">
                <span className="material-symbols-outlined animate-spin mr-2">autorenew</span>
                Loading story...
            </div>
        );
    }

    if (error || !story) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-400 p-4">
                <span className="material-symbols-outlined text-3xl mb-2">menu_book</span>
                <p className="text-sm text-center">{error || "No story data available"}</p>
                <p className="text-xs text-gray-500 mt-2">Generate a new manga to see story context here</p>
            </div>
        );
    }

    // Get current page data
    const currentPageData = story.pages?.find(p => p.page_number === currentPage);
    const currentPanelData = selectedPanel !== null
        ? currentPageData?.panels?.find(p => p.panel_number === selectedPanel)
        : null;

    return (
        <div className="h-full flex flex-col bg-[#0d1a14]">
            {/* Tabs */}
            <div className="flex border-b border-[#264532]">
                <button
                    onClick={() => setActiveTab("story")}
                    className={`flex-1 py-2 px-3 text-xs font-medium transition-colors ${activeTab === "story"
                            ? "text-[#38e07b] border-b-2 border-[#38e07b] bg-[#16261e]"
                            : "text-gray-400 hover:text-white"
                        }`}
                >
                    <span className="material-symbols-outlined text-sm mr-1 align-middle">menu_book</span>
                    Story
                </button>
                <button
                    onClick={() => setActiveTab("characters")}
                    className={`flex-1 py-2 px-3 text-xs font-medium transition-colors ${activeTab === "characters"
                            ? "text-[#38e07b] border-b-2 border-[#38e07b] bg-[#16261e]"
                            : "text-gray-400 hover:text-white"
                        }`}
                >
                    <span className="material-symbols-outlined text-sm mr-1 align-middle">group</span>
                    Characters
                </button>
                <button
                    onClick={() => setActiveTab("current")}
                    className={`flex-1 py-2 px-3 text-xs font-medium transition-colors ${activeTab === "current"
                            ? "text-[#38e07b] border-b-2 border-[#38e07b] bg-[#16261e]"
                            : "text-gray-400 hover:text-white"
                        }`}
                >
                    <span className="material-symbols-outlined text-sm mr-1 align-middle">crop_free</span>
                    Panel
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-3 text-sm">
                {activeTab === "story" && (
                    <div className="space-y-4">
                        {/* Original Prompt */}
                        {story.story_context?.original_prompt && (
                            <div>
                                <h4 className="text-[#38e07b] font-medium mb-1 flex items-center gap-1">
                                    <span className="material-symbols-outlined text-sm">lightbulb</span>
                                    Story Prompt
                                </h4>
                                <p className="text-gray-300 text-xs leading-relaxed bg-[#16261e] rounded-lg p-2 border border-[#264532]">
                                    {story.story_context.original_prompt}
                                </p>
                            </div>
                        )}

                        {/* Chapter Summary */}
                        {story.story_context?.llm_interpretation && (
                            <div>
                                <h4 className="text-[#38e07b] font-medium mb-1 flex items-center gap-1">
                                    <span className="material-symbols-outlined text-sm">summarize</span>
                                    Chapter Summary
                                </h4>
                                <p className="text-gray-300 text-xs leading-relaxed">
                                    {story.story_context.llm_interpretation}
                                </p>
                            </div>
                        )}

                        {/* Page Breakdown */}
                        <div>
                            <h4 className="text-[#38e07b] font-medium mb-2 flex items-center gap-1">
                                <span className="material-symbols-outlined text-sm">pages</span>
                                Pages ({story.pages?.length || 0})
                            </h4>
                            <div className="space-y-2">
                                {story.pages?.map((page, idx) => (
                                    <div
                                        key={idx}
                                        onClick={() => onSelectPage?.(page.page_number)}
                                        className={`p-2 rounded-lg border cursor-pointer transition-all ${page.page_number === currentPage
                                                ? "border-[#38e07b] bg-[#38e07b]/10"
                                                : "border-[#264532] bg-[#16261e] hover:border-[#38e07b]/50"
                                            }`}
                                    >
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-white font-medium text-xs">Page {page.page_number}</span>
                                            {page.emotional_beat && (
                                                <span className="text-[#38e07b] text-[10px] px-2 py-0.5 rounded-full bg-[#38e07b]/10">
                                                    {page.emotional_beat}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-gray-400 text-[11px]">{page.page_summary}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Continuation */}
                        {story.continuation_state?.cliffhanger && (
                            <div>
                                <h4 className="text-orange-400 font-medium mb-1 flex items-center gap-1">
                                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                                    Cliffhanger
                                </h4>
                                <p className="text-gray-300 text-xs italic">{story.continuation_state.cliffhanger}</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === "characters" && (
                    <div className="space-y-3">
                        {story.characters?.map((char, idx) => (
                            <div key={idx} className="p-3 bg-[#16261e] rounded-lg border border-[#264532]">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-[#38e07b] font-medium">{char.name}</span>
                                    {char.role && (
                                        <span className="text-[10px] text-gray-400 px-2 py-0.5 rounded-full bg-[#264532] capitalize">
                                            {char.role}
                                        </span>
                                    )}
                                </div>
                                <p className="text-gray-400 text-xs mb-1">{char.appearance}</p>
                                {char.personality && (
                                    <p className="text-gray-500 text-[11px]">
                                        <span className="text-gray-400">Personality:</span> {char.personality}
                                    </p>
                                )}
                                {char.arc_state && (
                                    <p className="text-[#38e07b]/70 text-[11px] mt-1 italic">
                                        State: {char.arc_state}
                                    </p>
                                )}
                                {char.visual_prompt && (
                                    <div className="mt-2 pt-2 border-t border-[#264532]">
                                        <span className="text-[10px] text-gray-500">Visual Prompt:</span>
                                        <p className="text-[10px] text-gray-400 font-mono">{char.visual_prompt}</p>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === "current" && (
                    <div className="space-y-3">
                        {currentPageData ? (
                            <>
                                <div className="bg-[#16261e] rounded-lg p-3 border border-[#264532]">
                                    <h4 className="text-[#38e07b] font-medium mb-1">
                                        Page {currentPageData.page_number}
                                    </h4>
                                    <p className="text-gray-300 text-xs">{currentPageData.page_summary}</p>
                                    {currentPageData.emotional_beat && (
                                        <span className="inline-block mt-2 text-[10px] text-[#38e07b] px-2 py-0.5 rounded-full bg-[#38e07b]/10">
                                            {currentPageData.emotional_beat}
                                        </span>
                                    )}
                                </div>

                                {currentPanelData ? (
                                    <div className="bg-[#1a2f24] rounded-lg p-3 border border-[#38e07b]/30">
                                        <h4 className="text-white font-medium mb-2 flex items-center gap-2">
                                            <span className="material-symbols-outlined text-sm text-[#38e07b]">crop_free</span>
                                            Panel {currentPanelData.panel_number}
                                        </h4>
                                        {currentPanelData.shot_type && (
                                            <p className="text-[10px] text-gray-400 mb-2">
                                                Shot: <span className="text-gray-300">{currentPanelData.shot_type}</span>
                                            </p>
                                        )}
                                        <p className="text-gray-300 text-xs mb-2">{currentPanelData.description}</p>

                                        {currentPanelData.characters_present && currentPanelData.characters_present.length > 0 && (
                                            <div className="mb-2">
                                                <span className="text-[10px] text-gray-500">Characters:</span>
                                                <div className="flex flex-wrap gap-1 mt-1">
                                                    {currentPanelData.characters_present.map((c, i) => (
                                                        <span key={i} className="text-[10px] bg-[#264532] text-[#38e07b] px-2 py-0.5 rounded">
                                                            {c}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {currentPanelData.dialogue && currentPanelData.dialogue.length > 0 && (
                                            <div>
                                                <span className="text-[10px] text-gray-500">Dialogue:</span>
                                                <div className="space-y-1 mt-1">
                                                    {currentPanelData.dialogue.map((dlg, i) => (
                                                        <div key={i} className="text-xs bg-[#0d1a14] rounded p-2">
                                                            <span className="text-[#38e07b]">{dlg.character || "Narrator"}</span>
                                                            <span className="text-gray-500 mx-1">({dlg.type}):</span>
                                                            <span className="text-gray-300">"{dlg.text}"</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="text-center text-gray-400 py-4">
                                        <span className="material-symbols-outlined text-2xl mb-2 block">touch_app</span>
                                        <p className="text-xs">Click a panel to see its context</p>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="text-center text-gray-400 py-4">
                                <span className="material-symbols-outlined text-2xl mb-2 block">pages</span>
                                <p className="text-xs">No page data available</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
