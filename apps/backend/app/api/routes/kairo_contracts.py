"""
Kairo Contract Management API

Endpoints for managing smart contracts through Kairo AI:
- Register contracts
- View contract versions
- Run security analysis
- Pre-deployment checks
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from ...integrations.kairo.contract_manager import (
    get_contract_manager,
    ContractVersion,
    DeploymentGate
)

router = APIRouter(prefix="/kairo/contracts", tags=["kairo-contracts"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RegisterContractRequest(BaseModel):
    """Request to register a new contract version"""
    contract_name: str
    code: str
    language: str = "solidity"
    version: str = "1.0.0"
    network: str = "devnet"


class PreDeployCheckRequest(BaseModel):
    """Request for pre-deployment check"""
    contract_name: str
    version: str = "latest"
    network: Dict[str, Any] = {"chain_id": 103, "name": "devnet"}


class AnalyzeContractRequest(BaseModel):
    """Request to analyze contract code"""
    code: str
    contract_path: str = "Contract.sol"
    severity_threshold: str = "high"


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/register", response_model=Dict[str, Any])
async def register_contract(request: RegisterContractRequest):
    """
    Register a new contract version with Kairo.
    
    This stores the contract and runs initial security analysis.
    """
    manager = get_contract_manager()
    
    try:
        version = await manager.register_contract(
            contract_name=request.contract_name,
            code=request.code,
            language=request.language,
            version=request.version,
            network=request.network
        )
        
        analysis_result = None
        if version.last_analysis:
            analysis_result = {
                "decision": version.last_analysis.decision.value,
                "risk_score": version.last_analysis.risk_score,
                "is_safe": version.last_analysis.is_safe,
                "warnings": version.last_analysis.warnings,
                "recommendations": version.last_analysis.recommendations
            }
        
        return {
            "success": True,
            "contract_name": version.contract_name,
            "version": version.version,
            "language": version.language,
            "network": version.network,
            "analysis": analysis_result,
            "created_at": version.created_at.isoformat() if version.created_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register contract: {str(e)}")


@router.post("/pre-deploy-check", response_model=Dict[str, Any])
async def pre_deploy_check(request: PreDeployCheckRequest):
    """
    Run pre-deployment security check (deploy gate).
    
    This is the final check before deployment - more strict than regular analysis.
    Use this in CI/CD pipelines.
    """
    manager = get_contract_manager()
    
    try:
        gate = await manager.pre_deployment_check(
            contract_name=request.contract_name,
            version=request.version,
            network=request.network
        )
        
        return {
            "passed": gate.passed,
            "can_deploy": gate.can_deploy,
            "decision": gate.decision.value,
            "risk_score": gate.risk_score,
            "warnings": gate.warnings,
            "recommendations": gate.recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pre-deployment check failed: {str(e)}")


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_contract(request: AnalyzeContractRequest):
    """
    Analyze contract code for security issues.
    
    This is a general analysis - use pre-deploy-check for deployment gates.
    """
    manager = get_contract_manager()
    
    try:
        analysis = await manager.analyze_contract_code(
            code=request.code,
            contract_path=request.contract_path,
            severity_threshold=request.severity_threshold
        )
        
        return {
            "decision": analysis.decision.value,
            "decision_reason": analysis.decision_reason,
            "risk_score": analysis.risk_score,
            "is_safe": analysis.is_safe,
            "confidence": analysis.confidence,
            "warnings": analysis.warnings,
            "recommendations": analysis.recommendations,
            "findings": analysis.findings,
            "summary": analysis.summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{contract_name}/versions", response_model=List[Dict[str, Any]])
async def get_contract_versions(contract_name: str):
    """Get all versions of a contract"""
    manager = get_contract_manager()
    versions = manager.get_contract_versions(contract_name)
    
    return [
        {
            "contract_name": v.contract_name,
            "version": v.version,
            "language": v.language,
            "network": v.network,
            "deployed_address": v.deployed_address,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "deployed_at": v.deployed_at.isoformat() if v.deployed_at else None,
            "last_analysis": {
                "decision": v.last_analysis.decision.value,
                "risk_score": v.last_analysis.risk_score
            } if v.last_analysis else None
        }
        for v in versions
    ]


@router.get("/{contract_name}/latest", response_model=Dict[str, Any])
async def get_latest_version(contract_name: str):
    """Get the latest version of a contract"""
    manager = get_contract_manager()
    version = manager.get_latest_version(contract_name)
    
    if not version:
        raise HTTPException(status_code=404, detail=f"Contract '{contract_name}' not found")
    
    return {
        "contract_name": version.contract_name,
        "version": version.version,
        "language": version.language,
        "network": version.network,
        "deployed_address": version.deployed_address,
        "created_at": version.created_at.isoformat() if version.created_at else None,
        "last_analysis": {
            "decision": version.last_analysis.decision.value,
            "risk_score": version.last_analysis.risk_score,
            "warnings": version.last_analysis.warnings,
            "recommendations": version.last_analysis.recommendations
        } if version.last_analysis else None
    }
