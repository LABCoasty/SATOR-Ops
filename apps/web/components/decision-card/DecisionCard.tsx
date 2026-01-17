"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  FileText,
  MessageSquare,
  Shield,
  TrendingUp,
  XCircle,
} from "lucide-react";

// ============================================================================
// Types
// ============================================================================

interface Prediction {
  prediction_id: string;
  issue_type: string;
  description: string;
  confidence: number;
  time_horizon: string;
  explanation: string;
  recommended_action: string;
}

interface Contradiction {
  contradiction_id: string;
  reason_code: string;
  category: string;
  description: string;
  values: Record<string, any>;
  confidence: number;
  severity: string;
}

interface AllowedAction {
  action_id: string;
  action_type: "act" | "defer" | "escalate";
  label: string;
  description: string;
  risk_level: string;
}

interface OperatorQuestion {
  question_id: string;
  question_type: string;
  question_text: string;
  options?: { option_id: string; label: string; description?: string }[];
  answered: boolean;
  answer?: any;
}

interface DecisionCardProps {
  cardId: string;
  incidentId: string;
  title: string;
  summary: string;
  severity: "info" | "warning" | "critical" | "emergency";
  trustScore: number;
  reasonCodes: string[];
  predictions: Prediction[];
  contradictions: Contradiction[];
  allowedActions: AllowedAction[];
  recommendedActionId: string;
  recommendationRationale: string;
  questions: OperatorQuestion[];
  expiresAt?: string;
  onActionSelect: (actionId: string) => void;
  onQuestionAnswer: (questionId: string, answer: any) => void;
  onViewReceipt: () => void;
  onViewAudit: () => void;
}

// ============================================================================
// Helper Components
// ============================================================================

const SeverityBadge = ({ severity }: { severity: string }) => {
  const config = {
    info: { variant: "secondary" as const, icon: CheckCircle },
    warning: { variant: "outline" as const, icon: AlertTriangle },
    critical: { variant: "destructive" as const, icon: AlertTriangle },
    emergency: { variant: "destructive" as const, icon: XCircle },
  };
  
  const { variant, icon: Icon } = config[severity as keyof typeof config] || config.warning;
  
  return (
    <Badge variant={variant} className="gap-1">
      <Icon className="h-3 w-3" />
      {severity.toUpperCase()}
    </Badge>
  );
};

const TrustIndicator = ({ score }: { score: number }) => {
  const percentage = Math.round(score * 100);
  const getColor = () => {
    if (percentage >= 80) return "bg-green-500";
    if (percentage >= 50) return "bg-yellow-500";
    if (percentage >= 30) return "bg-orange-500";
    return "bg-red-500";
  };
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">Trust Score</span>
        <span className="font-medium">{percentage}%</span>
      </div>
      <Progress value={percentage} className={`h-2 ${getColor()}`} />
    </div>
  );
};

const ReasonCodeBadge = ({ code }: { code: string }) => {
  const descriptions: Record<string, string> = {
    RC10: "Redundancy Conflict",
    RC11: "Physics Violation",
    RC12: "Vision Mismatch",
    RC13: "Calibration Drift",
  };
  
  return (
    <Badge variant="outline" className="text-xs">
      {code}: {descriptions[code] || "Unknown"}
    </Badge>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export function DecisionCard({
  cardId,
  incidentId,
  title,
  summary,
  severity,
  trustScore,
  reasonCodes,
  predictions,
  contradictions,
  allowedActions,
  recommendedActionId,
  recommendationRationale,
  questions,
  expiresAt,
  onActionSelect,
  onQuestionAnswer,
  onViewReceipt,
  onViewAudit,
}: DecisionCardProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  
  const pendingQuestions = questions.filter((q) => !q.answered);
  const recommendedAction = allowedActions.find((a) => a.action_id === recommendedActionId);
  
  const handleActionClick = (actionId: string) => {
    setSelectedAction(actionId);
  };
  
  const handleConfirmAction = () => {
    if (selectedAction) {
      onActionSelect(selectedAction);
    }
  };
  
  return (
    <Card className="w-full border-l-4 border-l-yellow-500 shadow-lg">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <Shield className="h-5 w-5 text-yellow-500" />
              {title}
            </CardTitle>
            <CardDescription>{summary}</CardDescription>
          </div>
          <div className="flex flex-col items-end gap-2">
            <SeverityBadge severity={severity} />
            {expiresAt && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Expires: {new Date(expiresAt).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
        
        <div className="mt-3">
          <TrustIndicator score={trustScore} />
        </div>
        
        {reasonCodes.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {reasonCodes.map((code) => (
              <ReasonCodeBadge key={code} code={code} />
            ))}
          </div>
        )}
      </CardHeader>
      
      <CardContent className="pt-0">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="contradictions" className="relative">
              Contradictions
              {contradictions.length > 0 && (
                <Badge variant="destructive" className="ml-1 h-5 w-5 p-0 text-xs">
                  {contradictions.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="predictions">Predictions</TabsTrigger>
            <TabsTrigger value="questions" className="relative">
              Questions
              {pendingQuestions.length > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 text-xs">
                  {pendingQuestions.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="mt-4 space-y-4">
            {recommendedAction && (
              <div className="p-3 bg-muted/50 rounded-lg border">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  AI Recommendation
                </h4>
                <p className="text-sm text-muted-foreground mt-1">
                  {recommendationRationale}
                </p>
              </div>
            )}
            
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Available Actions</h4>
              <div className="grid gap-2">
                {allowedActions.map((action) => (
                  <button
                    key={action.action_id}
                    onClick={() => handleActionClick(action.action_id)}
                    className={`w-full p-3 text-left rounded-lg border transition-colors ${
                      selectedAction === action.action_id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    } ${
                      action.action_id === recommendedActionId
                        ? "ring-2 ring-green-500/20"
                        : ""
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{action.label}</span>
                      <div className="flex items-center gap-2">
                        {action.action_id === recommendedActionId && (
                          <Badge variant="secondary" className="text-xs">
                            Recommended
                          </Badge>
                        )}
                        <Badge
                          variant={
                            action.risk_level === "low"
                              ? "outline"
                              : action.risk_level === "high"
                              ? "destructive"
                              : "secondary"
                          }
                          className="text-xs"
                        >
                          {action.risk_level} risk
                        </Badge>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {action.description}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="contradictions" className="mt-4">
            {contradictions.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No contradictions detected
              </p>
            ) : (
              <div className="space-y-3">
                {contradictions.map((c) => (
                  <div
                    key={c.contradiction_id}
                    className="p-3 rounded-lg border border-destructive/20 bg-destructive/5"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <Badge variant="destructive" className="text-xs">
                          {c.reason_code}
                        </Badge>
                        <p className="text-sm font-medium mt-1">{c.description}</p>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {Math.round(c.confidence * 100)}% confidence
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      Values: {JSON.stringify(c.values)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="predictions" className="mt-4">
            {predictions.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No predictions available
              </p>
            ) : (
              <div className="space-y-3">
                {predictions.map((p) => (
                  <div
                    key={p.prediction_id}
                    className="p-3 rounded-lg border bg-muted/30"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <Badge variant="outline" className="text-xs">
                          {p.issue_type}
                        </Badge>
                        <p className="text-sm font-medium mt-1">{p.description}</p>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {Math.round(p.confidence * 100)}% confidence
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      {p.explanation}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="secondary" className="text-xs">
                        {p.time_horizon}
                      </Badge>
                      <span className="text-xs">
                        Suggested: {p.recommended_action}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="questions" className="mt-4">
            {questions.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No questions to answer
              </p>
            ) : (
              <div className="space-y-4">
                {questions.map((q) => (
                  <div
                    key={q.question_id}
                    className={`p-3 rounded-lg border ${
                      q.answered ? "bg-muted/30" : "bg-background"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <MessageSquare className="h-4 w-4 mt-0.5 text-muted-foreground" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{q.question_text}</p>
                        
                        {q.answered ? (
                          <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" />
                            Answered: {String(q.answer)}
                          </p>
                        ) : (
                          <div className="mt-2">
                            {q.question_type === "multiple_choice" && q.options && (
                              <div className="space-y-1">
                                {q.options.map((opt) => (
                                  <button
                                    key={opt.option_id}
                                    onClick={() =>
                                      onQuestionAnswer(q.question_id, opt.option_id)
                                    }
                                    className="w-full text-left p-2 text-sm rounded border hover:bg-muted/50 transition-colors"
                                  >
                                    {opt.label}
                                    {opt.description && (
                                      <span className="text-xs text-muted-foreground block">
                                        {opt.description}
                                      </span>
                                    )}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
      
      <Separator />
      
      <CardFooter className="pt-4 flex justify-between">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onViewReceipt}>
            <Eye className="h-4 w-4 mr-1" />
            Trust Receipt
          </Button>
          <Button variant="outline" size="sm" onClick={onViewAudit}>
            <FileText className="h-4 w-4 mr-1" />
            Audit Trail
          </Button>
        </div>
        
        <Button
          onClick={handleConfirmAction}
          disabled={!selectedAction}
          className="min-w-[120px]"
        >
          Confirm Action
        </Button>
      </CardFooter>
    </Card>
  );
}

export default DecisionCard;
