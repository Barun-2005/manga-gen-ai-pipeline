"use client";

import React, { useState, useRef, useEffect } from "react";
import Draggable, { DraggableData, DraggableEvent } from "react-draggable";

export interface BubbleData {
    id: string;
    text: string;
    x: number;  // Percentage (0-100)
    y: number;  // Percentage (0-100)
    style: "speech" | "thought" | "shout" | "narrator";
    character?: string;
    fontSize?: number;
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

const BUBBLE_STYLES = {
    speech: {
        bg: "bg-white",
        border: "border-2 border-black",
        tail: "after:absolute after:bottom-0 after:left-4 after:w-3 after:h-3 after:bg-white after:border-r-2 after:border-b-2 after:border-black after:transform after:rotate-45 after:translate-y-1/2",
        textColor: "text-black",
    },
    thought: {
        bg: "bg-white",
        border: "border-2 border-black border-dashed",
        tail: "",
        textColor: "text-black",
    },
    shout: {
        bg: "bg-yellow-100",
        border: "border-3 border-black",
        tail: "",
        textColor: "text-black font-bold",
    },
    narrator: {
        bg: "bg-black/80",
        border: "border border-white/20",
        tail: "",
        textColor: "text-white italic",
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

    const style = BUBBLE_STYLES[bubble.style];

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
                    ${style.bg} ${style.border} ${style.tail}
                    rounded-xl px-3 py-2 min-w-[60px] max-w-[200px]
                    shadow-lg transition-shadow
                    ${isSelected ? "ring-2 ring-[#38e07b] ring-offset-2 ring-offset-transparent" : ""}
                    ${isEditing ? "cursor-text" : ""}
                `}
                style={{
                    zIndex: isSelected ? 50 : 10,
                    fontSize: bubble.fontSize || 12,
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
