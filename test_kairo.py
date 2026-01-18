#!/usr/bin/env python3
"""
Quick test script to see Kairo AI in action.

Run this to test Kairo integration:
    python test_kairo.py

Make sure your server is running first, or this will test the client directly.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "backend"))

from app.integrations.kairo import get_kairo_client


async def test_kairo_analysis():
    """Test Kairo contract analysis."""
    print("=" * 60)
    print("🔍 TESTING KAIRO CONTRACT ANALYSIS")
    print("=" * 60)
    
    client = get_kairo_client()
    
    if not client.enabled:
        print("❌ Kairo is not enabled!")
        print("   Make sure SATOR_KAIRO_API_KEY is set in your .env file")
        return
    
    print(f"✅ Kairo enabled")
    print(f"   API URL: {client.base_url}")
    print(f"   API Key: {client.api_key[:20]}..." if client.api_key else "   API Key: Not set")
    print()
    
    # Test with a simple contract
    test_contract = """
pragma solidity ^0.8.0;

contract SimpleToken {
    uint256 public totalSupply;
    mapping(address => uint256) public balances;
    
    constructor(uint256 _initialSupply) {
        totalSupply = _initialSupply;
        balances[msg.sender] = _initialSupply;
    }
    
    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}
"""
    
    print("📄 Analyzing contract: SimpleToken.sol")
    print("-" * 60)
    
    try:
        analysis = await client.analyze_contract(
            contract_code=test_contract,
            contract_path="SimpleToken.sol",
            severity_threshold="high",
            include_suggestions=True
        )
        
        print()
        print("📊 ANALYSIS RESULTS")
        print("-" * 60)
        print(f"Decision: {analysis.decision.value}")
        print(f"Risk Score: {analysis.risk_score:.2f}")
        print(f"Confidence: {analysis.confidence:.2%}")
        print(f"Reason: {analysis.decision_reason}")
        print()
        
        if analysis.warnings:
            print(f"⚠️  Warnings ({len(analysis.warnings)}):")
            for i, warning in enumerate(analysis.warnings, 1):
                print(f"   {i}. {warning}")
            print()
        
        if analysis.recommendations:
            print(f"💡 Recommendations ({len(analysis.recommendations)}):")
            for i, rec in enumerate(analysis.recommendations, 1):
                print(f"   {i}. {rec}")
            print()
        
        if analysis.summary:
            print(f"📋 Summary: {analysis.summary}")
        
        print("=" * 60)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_kairo_health():
    """Test Kairo health check."""
    print("=" * 60)
    print("🏥 TESTING KAIRO HEALTH CHECK")
    print("=" * 60)
    
    client = get_kairo_client()
    health = await client.health_check()
    
    print(f"Status: {health.get('status', 'unknown')}")
    print(f"API URL: {health.get('api_url', 'N/A')}")
    print(f"API Key Configured: {health.get('api_key_configured', False)}")
    print(f"Features: {health.get('features', [])}")
    print("=" * 60)


if __name__ == "__main__":
    print()
    print("🚀 Kairo Integration Test")
    print()
    
    # Test health first
    asyncio.run(test_kairo_health())
    print()
    
    # Test analysis
    asyncio.run(test_kairo_analysis())
    print()
    print("💡 Tip: Check server logs when anchoring artifacts to see Kairo in action!")
    print()
