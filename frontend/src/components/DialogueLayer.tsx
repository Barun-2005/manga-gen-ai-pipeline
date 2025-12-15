"use client";

import React, { useState, useRef } from "react";
import DraggableBubble, { BubbleData } from "./DraggableBubble";

interface DialogueLayerProps {
    panelId: string;
    dialogues: BubbleData[];
    onDialoguesChange: (panelId: string, dialogues: BubbleData[]) => void;
    containerRef: React.RefObject<HTMLDivElement | null>;
    isActive?: boolean; // Controls if editing is enabled
    onBubbleSelect?: (bubbleId: string | null) => void; // Sync selection to parent
}

export default function DialogueLayer({
    panelId,
    dialogues,
    onDialoguesChange,
    containerRef,
    isActive = false,
    onBubbleSelect,
}: DialogueLayerProps) {
    const [selectedBubbleId, setSelectedBubbleId] = useState<string | null>(null);

    // Select bubble and notify parent
    const selectBubble = (id: string | null) => {
        setSelectedBubbleId(id);
        if (onBubbleSelect) onBubbleSelect(id);
    };

    // Update a single bubble
    const handleUpdateBubble = (updated: BubbleData) => {
        const newDialogues = dialogues.map((d) =>
            d.id === updated.id ? updated : d
        );
        onDialoguesChange(panelId, newDialogues);
    };

    // Delete a bubble
    const handleDeleteBubble = (id: string) => {
        const newDialogues = dialogues.filter((d) => d.id !== id);
        onDialoguesChange(panelId, newDialogues);
        setSelectedBubbleId(null);
    };

    // Add a new bubble at click position
    const handleAddBubble = (e: React.MouseEvent) => {
        if (!containerRef.current) return;

        const rect = containerRef.current.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;

        const newBubble: BubbleData = {
            id: `bubble-${Date.now()}`,
            text: "New dialogue",
            x: Math.min(Math.max(x, 5), 85), // Keep within bounds
            y: Math.min(Math.max(y, 5), 85),
            style: "speech",
            fontSize: 12,
        };

        onDialoguesChange(panelId, [...dialogues, newBubble]);
        setSelectedBubbleId(newBubble.id);
    };

    // Deselect when clicking empty space
    const handleBackgroundClick = () => {
        selectBubble(null);
    };

    return (
        <div
            className="absolute inset-0"
            onClick={isActive ? handleBackgroundClick : undefined}
            style={{ pointerEvents: isActive ? 'auto' : 'none' }}
        >
            {/* Bubbles - always visible, draggable only when active */}
            {dialogues.map((bubble) => (
                <DraggableBubble
                    key={bubble.id}
                    bubble={bubble}
                    containerRef={containerRef}
                    isSelected={isActive && selectedBubbleId === bubble.id}
                    onSelect={() => isActive && selectBubble(bubble.id)}
                    onUpdate={isActive ? handleUpdateBubble : () => { }}
                    onDelete={() => isActive && handleDeleteBubble(bubble.id)}
                    disabled={!isActive}
                />
            ))}

            {/* Add bubble button - only show when active */}
            {isActive && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        // Add at center if clicked on button
                        if (containerRef.current) {
                            const rect = containerRef.current.getBoundingClientRect();
                            const fakeEvent = {
                                clientX: rect.left + rect.width / 2,
                                clientY: rect.top + rect.height / 2,
                            } as React.MouseEvent;
                            handleAddBubble(fakeEvent);
                        }
                    }}
                    className="absolute bottom-2 right-2 w-8 h-8 bg-[#38e07b] hover:bg-[#2bc065] rounded-full flex items-center justify-center text-black font-bold text-xl shadow-lg transition-colors z-50"
                    title="Add dialogue bubble"
                >
                    +
                </button>
            )}
        </div>
    );
}

// Export the bubble data type for use elsewhere
export type { BubbleData };
