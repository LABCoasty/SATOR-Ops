#!/usr/bin/env python3
"""
Register a smart contract with Kairo AI

Usage:
    python scripts/register_contract.py --name sator_anchor --file path/to/contract.sol
    python scripts/register_contract.py --name sator_anchor --code "pragma solidity..."
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.integrations.kairo.contract_manager import get_contract_manager


async def main():
    parser = argparse.ArgumentParser(description="Register contract with Kairo")
    parser.add_argument(
        "--name",
        required=True,
        help="Contract name (e.g., sator_anchor)"
    )
    parser.add_argument(
        "--file",
        help="Path to contract file"
    )
    parser.add_argument(
        "--code",
        help="Contract code as string"
    )
    parser.add_argument(
        "--language",
        default="solidity",
        choices=["solidity", "rust", "anchor"],
        help="Programming language (default: solidity)"
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Version string (default: 1.0.0)"
    )
    parser.add_argument(
        "--network",
        default="devnet",
        choices=["devnet", "testnet", "mainnet"],
        help="Target network (default: devnet)"
    )
    
    args = parser.parse_args()
    
    # Get contract code
    if args.file:
        # Handle both relative and absolute paths
        file_path = Path(args.file)
        if not file_path.is_absolute():
            # Try relative to script directory, then repo root
            script_dir = Path(__file__).parent.parent.parent  # Go up to repo root
            file_path = script_dir / args.file
            if not file_path.exists():
                # Try relative to current working directory
                file_path = Path(args.file)
        
        if not file_path.exists():
            print(f"❌ Error: File not found: {args.file}")
            print(f"   Tried: {file_path}")
            sys.exit(1)
        
        code = file_path.read_text()
        print(f"📄 Reading contract from: {file_path}")
    elif args.code:
        code = args.code
        print("📝 Using provided contract code")
    else:
        print("❌ Error: Must provide either --file or --code")
        sys.exit(1)
    
    print("=" * 70)
    print("🔐 Registering Contract with Kairo AI")
    print("=" * 70)
    print(f"Contract Name: {args.name}")
    print(f"Language: {args.language}")
    print(f"Version: {args.version}")
    print(f"Network: {args.network}")
    print(f"Code Length: {len(code)} characters")
    print("=" * 70)
    
    manager = get_contract_manager()
    
    try:
        print("\n📡 Registering contract...")
        version = await manager.register_contract(
            contract_name=args.name,
            code=code,
            language=args.language,
            version=args.version,
            network=args.network
        )
        
        print("\n✅ Contract registered successfully!")
        print(f"   Version: {version.version}")
        print(f"   Created: {version.created_at}")
        
        if version.last_analysis:
            analysis = version.last_analysis
            print("\n📊 Security Analysis Results:")
            print(f"   Decision: {analysis.decision.value}")
            print(f"   Risk Score: {analysis.risk_score:.2f}")
            print(f"   Is Safe: {'✅ Yes' if analysis.is_safe else '❌ No'}")
            
            if analysis.warnings:
                print(f"\n⚠️  Warnings ({len(analysis.warnings)}):")
                for warning in analysis.warnings:
                    print(f"   - {warning}")
            
            if analysis.recommendations:
                print(f"\n💡 Recommendations ({len(analysis.recommendations)}):")
                for rec in analysis.recommendations:
                    print(f"   - {rec}")
        else:
            print("\n⚠️  No security analysis available (Kairo may not support this language)")
        
        print("\n" + "=" * 70)
        print("✅ Registration complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error registering contract: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
