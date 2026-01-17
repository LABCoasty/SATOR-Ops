"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { DecisionCard } from "./DecisionCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Layers } from "lucide-react";

// ============================================================================
// Types
// ============================================================================

interface DecisionCardData {
  cardId: string;
  incidentId: string;
  title: string;
  summary: string;
  severity: "info" | "warning" | "critical" | "emergency";
  trustScore: number;
  reasonCodes: string[];
  predictions: any[];
  contradictions: any[];
  allowedActions: any[];
  recommendedActionId: string;
  recommendationRationale: string;
  questions: any[];
  expiresAt?: string;
}

interface DecisionCardStackProps {
  cards: DecisionCardData[];
  onActionSelect: (cardId: string, actionId: string) => void;
  onQuestionAnswer: (cardId: string, questionId: string, answer: any) => void;
  onViewReceipt: (cardId: string) => void;
  onViewAudit: (cardId: string) => void;
}

// ============================================================================
// Component
// ============================================================================

export function DecisionCardStack({
  cards,
  onActionSelect,
  onQuestionAnswer,
  onViewReceipt,
  onViewAudit,
}: DecisionCardStackProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  if (cards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center border-2 border-dashed rounded-lg">
        <Layers className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-medium">No Pending Decisions</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Decision cards will appear here when issues require operator attention.
        </p>
      </div>
    );
  }
  
  const currentCard = cards[currentIndex];
  
  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : prev));
  };
  
  const handleNext = () => {
    setCurrentIndex((prev) => (prev < cards.length - 1 ? prev + 1 : prev));
  };
  
  const handleCardAction = (actionId: string) => {
    onActionSelect(currentCard.cardId, actionId);
    // Move to next card after action
    if (currentIndex < cards.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };
  
  return (
    <div className="space-y-4">
      {/* Stack indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <Layers className="h-3 w-3" />
            {cards.length} pending
          </Badge>
          <span className="text-sm text-muted-foreground">
            Viewing {currentIndex + 1} of {cards.length}
          </span>
        </div>
        
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            onClick={handlePrevious}
            disabled={currentIndex === 0}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          {/* Pagination dots */}
          <div className="flex items-center gap-1 px-2">
            {cards.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentIndex(idx)}
                className={`w-2 h-2 rounded-full transition-colors ${
                  idx === currentIndex
                    ? "bg-primary"
                    : "bg-muted-foreground/30 hover:bg-muted-foreground/50"
                }`}
              />
            ))}
          </div>
          
          <Button
            variant="outline"
            size="icon"
            onClick={handleNext}
            disabled={currentIndex === cards.length - 1}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      {/* Card stack visualization */}
      <div className="relative">
        {/* Background cards (stacked effect) */}
        {cards.slice(currentIndex + 1, currentIndex + 3).map((_, idx) => (
          <div
            key={idx}
            className="absolute inset-0 bg-card border rounded-lg shadow"
            style={{
              transform: `translateY(${(idx + 1) * 8}px) scale(${1 - (idx + 1) * 0.02})`,
              opacity: 1 - (idx + 1) * 0.3,
              zIndex: -idx - 1,
            }}
          />
        ))}
        
        {/* Current card with animation */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentCard.cardId}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.2 }}
          >
            <DecisionCard
              {...currentCard}
              onActionSelect={handleCardAction}
              onQuestionAnswer={(questionId, answer) =>
                onQuestionAnswer(currentCard.cardId, questionId, answer)
              }
              onViewReceipt={() => onViewReceipt(currentCard.cardId)}
              onViewAudit={() => onViewAudit(currentCard.cardId)}
            />
          </motion.div>
        </AnimatePresence>
      </div>
      
      {/* Severity summary */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">By severity:</span>
        {["emergency", "critical", "warning", "info"].map((sev) => {
          const count = cards.filter((c) => c.severity === sev).length;
          if (count === 0) return null;
          return (
            <Badge
              key={sev}
              variant={
                sev === "emergency" || sev === "critical"
                  ? "destructive"
                  : sev === "warning"
                  ? "outline"
                  : "secondary"
              }
              className="text-xs"
            >
              {count} {sev}
            </Badge>
          );
        })}
      </div>
    </div>
  );
}

export default DecisionCardStack;
