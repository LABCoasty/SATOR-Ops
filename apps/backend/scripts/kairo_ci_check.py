#!/usr/bin/env python3
"""
Kairo CI/CD Pre-Deployment Check Script

This script runs before deployment to validate smart contracts with Kairo AI.
It should be called from CI/CD pipelines (GitHub Actions, etc.)

Usage:
    python scripts/kairo_ci_check.py [--contract CONTRACT_NAME] [--network NETWORK]
"""

import sys
import asyncio
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.integrations.kairo.contract_manager import get_contract_manager, KairoContractManager
from config import config


async def main():
    parser = argparse.ArgumentParser(description="Kairo Pre-Deployment Security Check")
    parser.add_argument(
        "--contract",
        default="sator_anchor",
        help="Contract name to check (default: sator_anchor)"
    )
    parser.add_argument(
        "--network",
        default="devnet",
        choices=["devnet", "testnet", "mainnet"],
        help="Target network (default: devnet)"
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Fail CI if Kairo returns WARN (default: only fail on BLOCK)"
    )
    parser.add_argument(
        "--output",
        default="kairo-security-report.json",
        help="Output file for security report (default: kairo-security-report.json)"
    )
    
    args = parser.parse_args()
    
    # Network mapping
    network_map = {
        "devnet": {"chain_id": 103, "name": "devnet"},
        "testnet": {"chain_id": 102, "name": "testnet"},
        "mainnet": {"chain_id": 101, "name": "mainnet"}
    }
    
    network_info = network_map[args.network]
    
    print("=" * 70)
    print("🔒 Kairo Pre-Deployment Security Check")
    print("=" * 70)
    print(f"Contract: {args.contract}")
    print(f"Network: {args.network} (chain_id: {network_info['chain_id']})")
    print(f"Kairo Enabled: {config.enable_kairo}")
    print(f"API Key Set: {bool(config.kairo_api_key)}")
    print("=" * 70)
    
    if not config.enable_kairo or not config.kairo_api_key:
        print("⚠️  WARNING: Kairo integration is disabled or API key not set")
        print("   Skipping security check...")
        sys.exit(0)
    
    manager = get_contract_manager()
    
    # Run pre-deployment check
    print(f"\n🔍 Running pre-deployment check for {args.contract}...")
    gate = await manager.pre_deployment_check(
        contract_name=args.contract,
        version="latest",
        network=network_info
    )
    
    # Print results
    print("\n" + "=" * 70)
    print("📊 Security Check Results")
    print("=" * 70)
    print(f"Decision: {gate.decision.value}")
    print(f"Risk Score: {gate.risk_score:.2f}")
    print(f"Can Deploy: {'✅ YES' if gate.can_deploy else '❌ NO'}")
    
    if gate.warnings:
        print(f"\n⚠️  Warnings ({len(gate.warnings)}):")
        for warning in gate.warnings:
            print(f"   - {warning}")
    
    if gate.recommendations:
        print(f"\n💡 Recommendations ({len(gate.recommendations)}):")
        for rec in gate.recommendations:
            print(f"   - {rec}")
    
    print("=" * 70)
    
    # Save report
    report = {
        "contract": args.contract,
        "network": args.network,
        "timestamp": asyncio.get_event_loop().time(),
        "decision": gate.decision.value,
        "risk_score": gate.risk_score,
        "can_deploy": gate.can_deploy,
        "warnings": gate.warnings,
        "recommendations": gate.recommendations,
        "passed": gate.passed
    }
    
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {args.output}")
    
    # Determine exit code
    if not gate.can_deploy:
        print("\n❌ DEPLOYMENT BLOCKED by Kairo security check")
        sys.exit(1)
    elif args.fail_on_warn and gate.decision.value == "WARN":
        print("\n⚠️  DEPLOYMENT BLOCKED: WARN decision with --fail-on-warn flag")
        sys.exit(1)
    else:
        print("\n✅ Pre-deployment check PASSED")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
