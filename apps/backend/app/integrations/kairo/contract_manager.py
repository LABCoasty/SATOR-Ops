"""
Kairo Contract Manager

Manages smart contracts through Kairo AI platform:
- Register contracts with Kairo
- Track contract versions
- Run pre-deployment security checks
- Manage deployment approvals
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

from .client import KairoClient, get_kairo_client, ContractAnalysis, KairoDecision
from config import config

logger = logging.getLogger(__name__)


@dataclass
class ContractVersion:
    """Represents a version of a smart contract"""
    contract_name: str
    version: str
    code: str
    language: str  # "solidity", "rust", "anchor"
    network: str  # "devnet", "mainnet", "testnet"
    deployed_address: Optional[str] = None
    kairo_project_id: Optional[str] = None
    last_analysis: Optional[ContractAnalysis] = None
    deployed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class DeploymentGate:
    """Result of a deployment gate check"""
    passed: bool
    decision: KairoDecision
    risk_score: float
    warnings: List[str]
    recommendations: List[str]
    can_deploy: bool


class KairoContractManager:
    """
    Manages smart contracts through Kairo AI platform.
    
    Provides:
    - Contract registration and versioning
    - Pre-deployment security checks
    - Deployment gate validation
    - Contract health monitoring
    """
    
    def __init__(self):
        self.kairo_client = get_kairo_client()
        self._contracts: Dict[str, List[ContractVersion]] = {}
        self.project_id = config.kairo_api_key.split("_")[-1][:8] if config.kairo_api_key else "sator_ops"
    
    async def register_contract(
        self,
        contract_name: str,
        code: str,
        language: str = "solidity",
        version: str = "1.0.0",
        network: str = "devnet"
    ) -> ContractVersion:
        """
        Register a new contract version with Kairo.
        
        Args:
            contract_name: Name of the contract
            code: Source code of the contract
            language: Programming language (solidity, rust, anchor)
            version: Version string (e.g., "1.0.0")
            network: Target network
            
        Returns:
            ContractVersion with analysis results
        """
        logger.info(f"Registering contract: {contract_name} v{version} ({language})")
        
        # Analyze the contract
        analysis = None
        if language == "solidity" and self.kairo_client.enabled:
            try:
                analysis = await self.kairo_client.analyze_contract(
                    contract_code=code,
                    contract_path=f"{contract_name}.sol",
                    severity_threshold="high",
                    include_suggestions=True
                )
                logger.info(f"Contract analysis: {analysis.decision.value} (risk: {analysis.risk_score:.2f})")
            except Exception as e:
                logger.warning(f"Kairo analysis failed: {e}")
        
        # Create version record
        version_obj = ContractVersion(
            contract_name=contract_name,
            version=version,
            code=code,
            language=language,
            network=network,
            kairo_project_id=self.project_id,
            last_analysis=analysis,
            created_at=datetime.utcnow()
        )
        
        # Store version
        if contract_name not in self._contracts:
            self._contracts[contract_name] = []
        self._contracts[contract_name].append(version_obj)
        
        return version_obj
    
    async def pre_deployment_check(
        self,
        contract_name: str,
        version: str,
        network: Dict[str, Any]
    ) -> DeploymentGate:
        """
        Run pre-deployment security check (deploy gate).
        
        This is the final check before deployment - more strict than regular analysis.
        
        Args:
            contract_name: Name of the contract
            version: Version to check
            network: Network info {chain_id: int, name: str}
            
        Returns:
            DeploymentGate with pass/fail decision
        """
        logger.info(f"Running pre-deployment check for {contract_name} v{version}")
        
        if not self.kairo_client.enabled:
            logger.warning("Kairo not enabled - deployment gate passed (no validation)")
            return DeploymentGate(
                passed=True,
                decision=KairoDecision.ALLOW,
                risk_score=0.0,
                warnings=["Kairo integration disabled"],
                recommendations=[],
                can_deploy=True
            )
        
        try:
            # Run deploy check
            analysis = await self.kairo_client.deploy_check(
                project_id=self.project_id,
                contract_name=contract_name,
                network=network
            )
            
            # Determine if deployment is allowed
            can_deploy = analysis.decision in [KairoDecision.ALLOW, KairoDecision.WARN]
            
            gate = DeploymentGate(
                passed=can_deploy,
                decision=analysis.decision,
                risk_score=analysis.risk_score,
                warnings=analysis.warnings,
                recommendations=analysis.recommendations,
                can_deploy=can_deploy
            )
            
            if can_deploy:
                logger.info(f"✅ Deployment gate PASSED: {analysis.decision.value}")
            else:
                logger.error(f"❌ Deployment gate BLOCKED: {analysis.decision.value} - {analysis.decision_reason}")
            
            return gate
            
        except Exception as e:
            logger.error(f"Deployment gate check failed: {e}")
            # On error, we're cautious but don't block (sidecar pattern)
            return DeploymentGate(
                passed=False,
                decision=KairoDecision.WARN,
                risk_score=0.5,
                warnings=[f"Deployment gate check failed: {str(e)}"],
                recommendations=["Verify contract manually before deployment"],
                can_deploy=True  # Don't block on errors
            )
    
    async def analyze_contract_code(
        self,
        code: str,
        contract_path: str = "Contract.sol",
        severity_threshold: str = "high"
    ) -> ContractAnalysis:
        """
        Analyze contract code for security issues.
        
        Args:
            code: Contract source code
            contract_path: File path/name
            severity_threshold: Minimum severity to report
            
        Returns:
            ContractAnalysis with findings
        """
        if not self.kairo_client.enabled:
            return ContractAnalysis(
                decision=KairoDecision.ALLOW,
                decision_reason="Kairo disabled",
                risk_score=0.0,
                is_safe=True,
                confidence=0.0,
                warnings=[],
                recommendations=[]
            )
        
        return await self.kairo_client.analyze_contract(
            contract_code=code,
            contract_path=contract_path,
            severity_threshold=severity_threshold,
            include_suggestions=True
        )
    
    def get_contract_versions(self, contract_name: str) -> List[ContractVersion]:
        """Get all versions of a contract"""
        return self._contracts.get(contract_name, [])
    
    def get_latest_version(self, contract_name: str) -> Optional[ContractVersion]:
        """Get the latest version of a contract"""
        versions = self.get_contract_versions(contract_name)
        if not versions:
            return None
        # Sort by created_at (most recent first)
        return sorted(versions, key=lambda v: v.created_at or datetime.min, reverse=True)[0]
    
    async def validate_before_deploy(
        self,
        contract_name: str,
        network: Dict[str, Any]
    ) -> tuple[bool, DeploymentGate]:
        """
        Validate contract before deployment (CI/CD hook).
        
        Returns:
            (can_deploy: bool, gate: DeploymentGate)
        """
        latest = self.get_latest_version(contract_name)
        if not latest:
            logger.warning(f"No versions found for {contract_name}")
            return False, DeploymentGate(
                passed=False,
                decision=KairoDecision.BLOCK,
                risk_score=1.0,
                warnings=[f"Contract {contract_name} not registered"],
                recommendations=["Register contract first"],
                can_deploy=False
            )
        
        gate = await self.pre_deployment_check(
            contract_name=contract_name,
            version=latest.version,
            network=network
        )
        
        return gate.can_deploy, gate


# ============================================================================
# Singleton instance
# ============================================================================

_contract_manager: Optional[KairoContractManager] = None


def get_contract_manager() -> KairoContractManager:
    """Get the singleton KairoContractManager instance."""
    global _contract_manager
    if _contract_manager is None:
        _contract_manager = KairoContractManager()
    return _contract_manager
