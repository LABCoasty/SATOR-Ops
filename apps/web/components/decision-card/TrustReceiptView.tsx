"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  CheckCircle,
  Copy,
  ExternalLink,
  FileCheck,
  Hash,
  Shield,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";

// ============================================================================
// Types
// ============================================================================

interface TrustReceipt {
  receipt_id: string;
  incident_id: string;
  generated_at: string;
  overall_trust_score: number;
  trust_level: "high" | "moderate" | "low" | "critical";
  sensor_scores: Record<string, number>;
  reason_codes: string[];
  contradictions_count: number;
  evidence_sources: string[];
  vision_validated: boolean;
  questions_asked: number;
  questions_answered: number;
  operator_trust_adjustments: number;
  content_hash: string;
  previous_receipt_hash?: string;
}

interface TrustReceiptViewProps {
  receipt: TrustReceipt;
  receiptHistory?: TrustReceipt[];
  onChainAnchor?: {
    tx_hash: string;
    verification_url: string;
    chain: string;
  };
  onCopyHash?: (hash: string) => void;
}

// ============================================================================
// Helper Components
// ============================================================================

const TrustLevelBadge = ({ level }: { level: string }) => {
  const config = {
    high: { variant: "default" as const, color: "bg-green-500" },
    moderate: { variant: "secondary" as const, color: "bg-yellow-500" },
    low: { variant: "outline" as const, color: "bg-orange-500" },
    critical: { variant: "destructive" as const, color: "bg-red-500" },
  };
  
  const { variant, color } = config[level as keyof typeof config] || config.moderate;
  
  return (
    <Badge variant={variant} className="gap-1">
      <div className={`w-2 h-2 rounded-full ${color}`} />
      {level.toUpperCase()} TRUST
    </Badge>
  );
};

const SensorTrustBar = ({
  sensorId,
  score,
}: {
  sensorId: string;
  score: number;
}) => {
  const percentage = Math.round(score * 100);
  const getColor = () => {
    if (percentage >= 80) return "bg-green-500";
    if (percentage >= 50) return "bg-yellow-500";
    if (percentage >= 30) return "bg-orange-500";
    return "bg-red-500";
  };
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="font-mono">{sensorId}</span>
        <span>{percentage}%</span>
      </div>
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full ${getColor()} transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export function TrustReceiptView({
  receipt,
  receiptHistory = [],
  onChainAnchor,
  onCopyHash,
}: TrustReceiptViewProps) {
  const trustPercentage = Math.round(receipt.overall_trust_score * 100);
  
  const handleCopyHash = () => {
    navigator.clipboard.writeText(receipt.content_hash);
    onCopyHash?.(receipt.content_hash);
  };
  
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <FileCheck className="h-5 w-5 text-primary" />
              Trust Receipt
            </CardTitle>
            <CardDescription>
              Generated: {new Date(receipt.generated_at).toLocaleString()}
            </CardDescription>
          </div>
          <TrustLevelBadge level={receipt.trust_level} />
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Overall Trust Score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Overall Trust Score</span>
            <span className="text-2xl font-bold">{trustPercentage}%</span>
          </div>
          <Progress value={trustPercentage} className="h-3" />
          
          {receipt.operator_trust_adjustments !== 0 && (
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              {receipt.operator_trust_adjustments > 0 ? (
                <>
                  <TrendingUp className="h-3 w-3 text-green-500" />
                  Operator input increased trust by{" "}
                  {Math.round(receipt.operator_trust_adjustments * 100)}%
                </>
              ) : (
                <>
                  <TrendingDown className="h-3 w-3 text-red-500" />
                  Operator input decreased trust by{" "}
                  {Math.abs(Math.round(receipt.operator_trust_adjustments * 100))}%
                </>
              )}
            </p>
          )}
        </div>
        
        <Separator />
        
        {/* Sensor Trust Scores */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Sensor Trust Scores</h4>
          <div className="space-y-2">
            {Object.entries(receipt.sensor_scores).map(([sensorId, score]) => (
              <SensorTrustBar key={sensorId} sensorId={sensorId} score={score} />
            ))}
          </div>
        </div>
        
        <Separator />
        
        {/* Reason Codes */}
        {receipt.reason_codes.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Active Reason Codes</h4>
            <div className="flex flex-wrap gap-1">
              {receipt.reason_codes.map((code) => (
                <Badge key={code} variant="destructive" className="text-xs">
                  {code}
                </Badge>
              ))}
            </div>
          </div>
        )}
        
        {/* Evidence Summary */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="p-3 bg-muted/50 rounded-lg">
            <p className="text-muted-foreground">Contradictions</p>
            <p className="text-lg font-bold">{receipt.contradictions_count}</p>
          </div>
          <div className="p-3 bg-muted/50 rounded-lg">
            <p className="text-muted-foreground">Evidence Sources</p>
            <p className="text-lg font-bold">{receipt.evidence_sources.length}</p>
          </div>
          <div className="p-3 bg-muted/50 rounded-lg">
            <p className="text-muted-foreground">Questions Asked</p>
            <p className="text-lg font-bold">
              {receipt.questions_answered}/{receipt.questions_asked}
            </p>
          </div>
          <div className="p-3 bg-muted/50 rounded-lg">
            <p className="text-muted-foreground">Vision Validated</p>
            <p className="text-lg font-bold flex items-center gap-1">
              {receipt.vision_validated ? (
                <>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Yes
                </>
              ) : (
                "No"
              )}
            </p>
          </div>
        </div>
        
        <Separator />
        
        {/* Cryptographic Verification */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Cryptographic Verification
          </h4>
          
          <div className="p-3 bg-muted/30 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Content Hash</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs"
                onClick={handleCopyHash}
              >
                <Copy className="h-3 w-3 mr-1" />
                Copy
              </Button>
            </div>
            <code className="text-xs font-mono break-all block">
              {receipt.content_hash}
            </code>
          </div>
          
          {receipt.previous_receipt_hash && (
            <div className="p-3 bg-muted/30 rounded-lg space-y-1">
              <span className="text-xs text-muted-foreground">
                Previous Receipt Hash (Chain Link)
              </span>
              <code className="text-xs font-mono break-all block">
                {receipt.previous_receipt_hash}
              </code>
            </div>
          )}
          
          {onChainAnchor && (
            <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-green-600">
                  Anchored On-Chain
                </span>
                <Badge variant="outline" className="text-xs">
                  {onChainAnchor.chain}
                </Badge>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <code className="text-xs font-mono truncate flex-1">
                  {onChainAnchor.tx_hash}
                </code>
                <a
                  href={onChainAnchor.verification_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline text-xs flex items-center gap-1"
                >
                  View <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          )}
        </div>
        
        {/* Receipt History */}
        {receiptHistory.length > 1 && (
          <>
            <Separator />
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Trust History</h4>
              <ScrollArea className="h-32">
                <div className="space-y-1">
                  {receiptHistory.map((r, idx) => (
                    <div
                      key={r.receipt_id}
                      className={`flex items-center justify-between text-xs p-2 rounded ${
                        r.receipt_id === receipt.receipt_id
                          ? "bg-primary/10"
                          : "bg-muted/30"
                      }`}
                    >
                      <span className="text-muted-foreground">
                        {new Date(r.generated_at).toLocaleTimeString()}
                      </span>
                      <span className="font-medium">
                        {Math.round(r.overall_trust_score * 100)}%
                      </span>
                      <TrustLevelBadge level={r.trust_level} />
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default TrustReceiptView;
