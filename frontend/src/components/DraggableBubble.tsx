"use client";

import React, { useState, useRef, useEffect } from "react";
import Draggable, { DraggableData, DraggableEvent } from "react-draggable";

export interface BubbleData {
    id: string;
    text: string;
    x: number;  // Percentage (0-100)
    y: number;  // Percentage (0-100)
    style: "speech" | "thought" | "shout" | "narrator" | "scream" | "whisper" | "impact" | "radio";
    character?: string;
    fontSize?: number;
    fontFamily?: string;
    tailDirection?: "bottom" | "top" | "left" | "right";  // Arrow direction
    speakerPosition?: "left" | "right" | "center" | "none";  // V4.8: LLM-specified speaker position
}

interface DraggableBubbleProps {
    bubble: BubbleData;
    containerRef: React.RefObject<HTMLDivElement | null>;
    isSelected: boolean;
    onSelect: () => void;
    onUpdate: (updated: BubbleData) => void;
    onDelete: () => void;
    disabled?: boolean;
}

// MANGA-AUTHENTIC BUBBLE STYLES
const BUBBLE_STYLES: Record<string, { bg: string, border: string, tail: string, textColor: string, shape?: string }> = {
    speech: {
        bg: "bg-white",
        border: "border-2 border-black rounded-[50%]", // Ellipse shape
        tail: "after:absolute after:bottom-[-8px] after:left-6 after:w-0 after:h-0 after:border-l-[8px] after:border-l-transparent after:border-r-[8px] after:border-r-transparent after:border-t-[10px] after:border-t-black before:absolute before:bottom-[-5px] before:left-[26px] before:w-0 before:h-0 before:border-l-[6px] before:border-l-transparent before:border-r-[6px] before:border-r-transparent before:border-t-[8px] before:border-t-white before:z-10",
        textColor: "text-black",
    },
    thought: {
        bg: "bg-white",
        border: "border-2 border-black rounded-full", // Cloud-like
        tail: "after:absolute after:bottom-[-12px] after:left-4 after:w-2 after:h-2 after:bg-white after:border-2 after:border-black after:rounded-full before:absolute before:bottom-[-20px] before:left-2 before:w-1.5 before:h-1.5 before:bg-white before:border-2 before:border-black before:rounded-full",
        textColor: "text-gray-700 italic",
    },
    shout: {
        bg: "bg-white",
        border: "border-[4px] border-black", // Thicker border for impact
        tail: "",
        textColor: "text-black font-black uppercase tracking-wider text-shadow",
        // JJK-style aggressive spikes - deeper and more chaotic
        shape: "polygon(5% 25%, 0% 10%, 12% 20%, 20% 0%, 25% 18%, 40% 5%, 50% 15%, 60% 5%, 75% 18%, 80% 0%, 88% 20%, 100% 10%, 95% 25%, 100% 45%, 95% 55%, 100% 75%, 95% 85%, 88% 80%, 80% 100%, 75% 82%, 60% 95%, 50% 85%, 40% 95%, 25% 82%, 20% 100%, 12% 80%, 5% 85%, 0% 75%, 5% 55%, 0% 45%)",
    },
    narrator: {
        // Manga caption box style - rectangular, positioned at edges
        bg: "bg-gradient-to-b from-gray-900 to-black",
        border: "border-l-4 border-l-white/30 rounded-sm",  // Left accent like manga captions
        tail: "",
        textColor: "text-white text-[11px] leading-snug font-serif italic",
    },
    scream: {
        bg: "bg-white",
        border: "border-4 border-black",
        tail: "",
        textColor: "text-black font-black text-lg uppercase",
        shape: "polygon(10% 0%, 30% 5%, 50% 0%, 70% 5%, 90% 0%, 95% 20%, 100% 50%, 95% 80%, 90% 100%, 70% 95%, 50% 100%, 30% 95%, 10% 100%, 5% 80%, 0% 50%, 5% 20%)", // Jagged
    },
    whisper: {
        bg: "bg-gray-50",
        border: "border border-gray-400 border-dashed rounded-full",
        tail: "",
        textColor: "text-gray-500 text-[10px] italic",
    },
    impact: {
        bg: "bg-white",
        border: "border-4 border-black",
        tail: "",
        textColor: "text-black font-black text-xl tracking-tighter",
        shape: "polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)", // Star burst
    },
    radio: {
        bg: "bg-gray-100",
        border: "border-2 border-gray-600 rounded-lg",
        tail: "after:absolute after:-left-2 after:top-1/2 after:-translate-y-1/2 after:w-1 after:h-4 after:bg-gray-600",
        textColor: "text-gray-800 font-mono text-sm",
    },
};

export default function DraggableBubble({
    bubble,
    containerRef,
    isSelected,
    onSelect,
    onUpdate,
    onDelete,
    disabled = false,
}: DraggableBubbleProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [editText, setEditText] = useState(bubble.text);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const nodeRef = useRef<HTMLDivElement>(null);

    const style = BUBBLE_STYLES[bubble.style] || BUBBLE_STYLES.speech;

    // Get tail classes based on direction
    const getTailClasses = (): string => {
        // V4.3/V4.8: Derive tailDirection from speakerPosition if not explicitly set
        let direction = bubble.tailDirection;
        if (!direction && bubble.speakerPosition) {
            // If speaker is on left, point tail left; if right, point right
            switch (bubble.speakerPosition) {
                case "left":
                    direction = "left";
                    break;
                case "right":
                    direction = "right";
                    break;
                case "center":
                    direction = "bottom";
                    break;
                default:
                    direction = "bottom";
            }
        }
        direction = direction || "bottom";

        // Speech and thought bubbles have tails, others don't
        if (!["speech", "thought"].includes(bubble.style)) {
            return "";
        }

        if (bubble.style === "thought") {
            // Thought bubble uses dots
            switch (direction) {
                case "top":
                    return "after:absolute after:top-[-12px] after:left-4 after:w-2 after:h-2 after:bg-white after:border-2 after:border-black after:rounded-full before:absolute before:top-[-20px] before:left-6 before:w-1.5 before:h-1.5 before:bg-white before:border-2 before:border-black before:rounded-full";
                case "left":
                    return "after:absolute after:left-[-12px] after:top-4 after:w-2 after:h-2 after:bg-white after:border-2 after:border-black after:rounded-full before:absolute before:left-[-20px] before:top-2 before:w-1.5 before:h-1.5 before:bg-white before:border-2 before:border-black before:rounded-full";
                case "right":
                    return "after:absolute after:right-[-12px] after:top-4 after:w-2 after:h-2 after:bg-white after:border-2 after:border-black after:rounded-full before:absolute before:right-[-20px] before:top-2 before:w-1.5 before:h-1.5 before:bg-white before:border-2 before:border-black before:rounded-full";
                default: // bottom
                    return style.tail;
            }
        }

        // Speech bubble triangular tails
        switch (direction) {
            case "top":
                return "after:absolute after:top-[-8px] after:left-6 after:w-0 after:h-0 after:border-l-[8px] after:border-l-transparent after:border-r-[8px] after:border-r-transparent after:border-b-[10px] after:border-b-black before:absolute before:top-[-5px] before:left-[26px] before:w-0 before:h-0 before:border-l-[6px] before:border-l-transparent before:border-r-[6px] before:border-r-transparent before:border-b-[8px] before:border-b-white before:z-10";
            case "left":
                return "after:absolute after:left-[-8px] after:top-4 after:w-0 after:h-0 after:border-t-[8px] after:border-t-transparent after:border-b-[8px] after:border-b-transparent after:border-r-[10px] after:border-r-black before:absolute before:left-[-5px] before:top-[18px] before:w-0 before:h-0 before:border-t-[6px] before:border-t-transparent before:border-b-[6px] before:border-b-transparent before:border-r-[8px] before:border-r-white before:z-10";
            case "right":
                return "after:absolute after:right-[-8px] after:top-4 after:w-0 after:h-0 after:border-t-[8px] after:border-t-transparent after:border-b-[8px] after:border-b-transparent after:border-l-[10px] after:border-l-black before:absolute before:right-[-5px] before:top-[18px] before:w-0 before:h-0 before:border-t-[6px] before:border-t-transparent before:border-b-[6px] before:border-b-transparent before:border-l-[8px] before:border-l-white before:z-10";
            default: // bottom
                return style.tail;
        }
    };

    // Convert percentage to pixels based on container size
    const getPixelPosition = () => {
        if (!containerRef.current) return { x: 0, y: 0 };
        const rect = containerRef.current.getBoundingClientRect();
        return {
            x: (bubble.x / 100) * rect.width,
            y: (bubble.y / 100) * rect.height,
        };
    };

    // Convert pixels back to percentage
    const updatePosition = (e: DraggableEvent, data: DraggableData) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const newX = (data.x / rect.width) * 100;
        const newY = (data.y / rect.height) * 100;
        onUpdate({ ...bubble, x: newX, y: newY });
    };

    // Handle double-click to edit
    const handleDoubleClick = () => {
        setIsEditing(true);
        setEditText(bubble.text);
    };

    // Save edited text
    const saveEdit = () => {
        setIsEditing(false);
        onUpdate({ ...bubble, text: editText });
    };

    // Focus textarea when editing starts
    useEffect(() => {
        if (isEditing && textareaRef.current) {
            textareaRef.current.focus();
            textareaRef.current.select();
        }
    }, [isEditing]);

    const pixelPos = getPixelPosition();

    return (
        <Draggable
            nodeRef={nodeRef}
            position={pixelPos}
            onStop={updatePosition}
            bounds="parent"
            disabled={isEditing || disabled}
        >
            <div
                ref={nodeRef}
                onClick={(e) => {
                    e.stopPropagation();
                    onSelect();
                }}
                onDoubleClick={handleDoubleClick}
                className={`
                    absolute cursor-move select-none
                    ${style.bg} ${style.border} ${getTailClasses()}
                    px-3 py-2 min-w-[60px] max-w-[200px]
                    shadow-lg transition-shadow
                    ${isSelected ? "ring-2 ring-[#38e07b] ring-offset-2 ring-offset-transparent" : ""}
                    ${isEditing ? "cursor-text" : ""}
                `}
                style={{
                    zIndex: isSelected ? 50 : 10,
                    fontSize: bubble.fontSize || 12,
                    fontFamily: bubble.fontFamily || "Comic Sans MS, cursive",
                    clipPath: style.shape || undefined,
                }}
            >
                {isEditing ? (
                    <textarea
                        ref={textareaRef}
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        onBlur={saveEdit}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                saveEdit();
                            }
                            if (e.key === "Escape") {
                                setIsEditing(false);
                                setEditText(bubble.text);
                            }
                        }}
                        className={`
                            w-full bg-transparent resize-none outline-none
                            ${style.textColor}
                        `}
                        rows={2}
                    />
                ) : (
                    <p className={`text-center leading-tight break-words whitespace-pre-wrap overflow-hidden ${style.textColor}`}>
                        {bubble.text}
                    </p>
                )}

                {/* Delete button when selected */}
                {isSelected && !isEditing && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onDelete();
                        }}
                        className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs hover:bg-red-600 transition-colors"
                    >
                        ×
                    </button>
                )}

                {/* Resize handle when selected */}
                {isSelected && !isEditing && (
                    <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-[#38e07b] rounded-sm cursor-se-resize" />
                )}
            </div>
        </Draggable>
    );
}
