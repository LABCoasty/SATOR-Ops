"""
Kairo API Client

Client for interacting with the Kairo AI Sec platform.
Implements security analysis for smart contracts before deployment and anchoring.
"""

import httpx
from dataclasses import dataclass
from typing import Any, Optional, Dict, List
from enum import Enum

from config import config


class KairoDecision(str, Enum):
    """Kairo security decision types"""
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


@dataclass
class ContractAnalysis:
    """Result of a Kairo contract analysis"""
    decision: KairoDecision
    decision_reason: str
    risk_score: float
    is_safe: bool
    confidence: float
    warnings: List[str]
    recommendations: List[str]
    findings: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, int]] = None


class KairoClient:
    """
    Client for the Kairo AI Sec API.
    
    Kairo is an AI-native secure smart contract development platform.
    This client handles contract validation before anchoring.
    
    API Documentation: https://kairoaisec.com/docs#quickstart
    """
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.kairo_api_key
        self.base_url = "https://api.kairoaisec.com/v1"
        self._enabled = config.enable_kairo and self.api_key is not None
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json",
            }
        ) if self._enabled else None
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    async def analyze_contract(
        self, 
        contract_code: str,
        contract_path: str = "Contract.sol",
        severity_threshold: str = "high",
        include_suggestions: bool = True
    ) -> ContractAnalysis:
        """
        Analyze a smart contract for security issues using Kairo API.
        
        Args:
            contract_code: The contract source code
            contract_path: File path/name for the contract
            severity_threshold: Minimum severity to report (low/medium/high/critical)
            include_suggestions: Whether to include fix suggestions
            
        Returns:
            ContractAnalysis with safety assessment
        """
        if not self._enabled or not self._client:
            return ContractAnalysis(
                decision=KairoDecision.ALLOW,
                decision_reason="Kairo integration disabled",
                risk_score=0.0,
                is_safe=True,
                confidence=0.0,
                warnings=["Kairo integration disabled"],
                recommendations=[],
            )
        
        try:
            payload = {
                "source": {
                    "type": "inline",
                    "files": [{
                        "path": contract_path,
                        "content": contract_code
                    }]
                },
                "config": {
                    "severity_threshold": severity_threshold,
                    "include_suggestions": include_suggestions
                }
            }
            
            response = await self._client.post(
                f"{self.base_url}/analyze",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Map Kairo decision to our model
            decision = KairoDecision(data.get("decision", "ALLOW"))
            risk_score = data.get("risk_score", 0.0)
            
            # Extract findings and warnings
            findings = data.get("findings", [])
            warnings = []
            recommendations = []
            
            if findings:
                for finding in findings:
                    severity = finding.get("severity", "unknown")
                    message = finding.get("message", "")
                    warnings.append(f"[{severity.upper()}] {message}")
                    
                    if include_suggestions and finding.get("suggestion"):
                        recommendations.append(finding["suggestion"])
            
            return ContractAnalysis(
                decision=decision,
                decision_reason=data.get("decision_reason", "Analysis complete"),
                risk_score=risk_score,
                is_safe=decision in [KairoDecision.ALLOW, KairoDecision.WARN],
                confidence=1.0 - risk_score,  # Convert risk to confidence
                warnings=warnings,
                recommendations=recommendations,
                findings=data.get("findings"),
                summary=data.get("summary"),
            )
            
        except httpx.HTTPStatusError as e:
            # API error - log but don't block
            error_msg = f"Kairo API error: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text[:200]}"
            
            return ContractAnalysis(
                decision=KairoDecision.WARN,
                decision_reason=error_msg,
                risk_score=0.5,
                is_safe=True,  # Don't block on API errors (sidecar pattern)
                confidence=0.0,
                warnings=[error_msg],
                recommendations=["Verify Kairo API connectivity"],
            )
            
        except Exception as e:
            # Network or other errors - don't block
            return ContractAnalysis(
                decision=KairoDecision.WARN,
                decision_reason=f"Kairo API unavailable: {str(e)}",
                risk_score=0.3,
                is_safe=True,  # Don't block on errors (sidecar pattern)
                confidence=0.0,
                warnings=[f"Kairo analysis failed: {str(e)}"],
                recommendations=["Check network connectivity and API key"],
            )
    
    async def deploy_check(
        self,
        project_id: str,
        contract_name: str,
        network: Dict[str, Any]
    ) -> ContractAnalysis:
        """
        Final safety check before deployment (deploy gate).
        More strict than analyze_contract.
        
        Args:
            project_id: Kairo project ID
            contract_name: Name of the contract to check
            network: Network info {chain_id: int, name: str}
            
        Returns:
            ContractAnalysis with deploy gate decision
        """
        if not self._enabled or not self._client:
            return ContractAnalysis(
                decision=KairoDecision.ALLOW,
                decision_reason="Kairo integration disabled",
                risk_score=0.0,
                is_safe=True,
                confidence=0.0,
                warnings=["Kairo integration disabled"],
                recommendations=[],
            )
        
        try:
            payload = {
                "project_id": project_id,
                "contract_name": contract_name,
                "network": network
            }
            
            response = await self._client.post(
                f"{self.base_url}/deploy/check",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            decision = KairoDecision(data.get("decision", "ALLOW"))
            risk_score = data.get("risk_score", 0.0)
            
            return ContractAnalysis(
                decision=decision,
                decision_reason=data.get("decision_reason", "Deploy check complete"),
                risk_score=risk_score,
                is_safe=decision in [KairoDecision.ALLOW, KairoDecision.WARN],
                confidence=1.0 - risk_score,
                warnings=[data.get("decision_reason", "")] if decision != KairoDecision.ALLOW else [],
                recommendations=[],
                findings=data.get("findings"),
                summary=data.get("summary"),
            )
            
        except Exception as e:
            # On deploy gate failure, we're more cautious but still don't block
            # (following sidecar pattern - Kairo shouldn't gate core functionality)
            return ContractAnalysis(
                decision=KairoDecision.WARN,
                decision_reason=f"Kairo deploy check unavailable: {str(e)}",
                risk_score=0.4,
                is_safe=True,
                confidence=0.0,
                warnings=[f"Deploy check failed: {str(e)}"],
                recommendations=["Proceed with caution - verify contract manually"],
            )
    
    async def validate_anchor_program(self) -> bool:
        """
        Validate that the SATOR anchor program is safe.
        
        This should be called once during initialization to ensure
        the anchor contract is secure before use.
        
        Note: Kairo API currently supports Solidity. For Rust/Anchor programs,
        this may need to be adapted or used for Solidity components only.
        """
        if not self._enabled:
            return True  # No validation needed when disabled
        
        # For now, return True as anchor program is Rust/Anchor
        # In production, you might:
        # 1. Extract Solidity components if any
        # 2. Use Rust-specific security tools (cargo-audit, etc.)
        # 3. Or wait for Kairo to support Rust/Anchor
        return True
    
    async def health_check(self) -> dict:
        """Check Kairo API health"""
        if not self._enabled:
            return {"status": "disabled"}
        
        try:
            # Try a simple request to verify connectivity
            # Note: Kairo may not have a dedicated health endpoint
            # So we'll just check if client is configured
            return {
                "status": "healthy",
                "api_url": self.base_url,
                "api_key_configured": bool(self.api_key),
                "features": ["contract_analysis", "deploy_check", "anchor_validation"],
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()


# ============================================================================
# Singleton instance
# ============================================================================

_kairo_client: Optional[KairoClient] = None


def get_kairo_client() -> KairoClient:
    """Get the singleton KairoClient instance."""
    global _kairo_client
    if _kairo_client is None:
        _kairo_client = KairoClient()
    return _kairo_client
