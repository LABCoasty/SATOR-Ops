#!/usr/bin/env python3
"""
Simple Kairo test - tests the client directly without full app dependencies.
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Simple Kairo client test
import httpx


async def test_kairo_direct():
    """Test Kairo API directly."""
    print("=" * 60)
    print("🔍 TESTING KAIRO API DIRECTLY")
    print("=" * 60)
    
    api_key = os.getenv("SATOR_KAIRO_API_KEY")
    
    if not api_key:
        print("❌ SATOR_KAIRO_API_KEY not found in environment")
        print("   Make sure your .env file has the key set")
        return
    
    print(f"✅ API Key found: {api_key[:20]}...")
    print()
    
    base_url = "https://api.kairoaisec.com/v1"
    
    # Test contract
    test_contract = """
pragma solidity ^0.8.0;

contract SimpleToken {
    uint256 public totalSupply;
    
    constructor(uint256 _initialSupply) {
        totalSupply = _initialSupply;
    }
    
    function transfer(address to, uint256 amount) public {
        totalSupply -= amount;
    }
}
"""
    
    print("📄 Test Contract: SimpleToken.sol")
    print("-" * 60)
    print(test_contract.strip())
    print("-" * 60)
    print()
    
    payload = {
        "source": {
            "type": "inline",
            "files": [{
                "path": "SimpleToken.sol",
                "content": test_contract
            }]
        },
        "config": {
            "severity_threshold": "high",
            "include_suggestions": True
        }
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    print(f"📡 Calling Kairo API: {base_url}/analyze")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("🚀 Sending request...")
            response = await client.post(
                f"{base_url}/analyze",
                json=payload,
                headers=headers
            )
            
            print(f"📥 Response Status: {response.status_code}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                
                print("=" * 60)
                print("📊 KAIRO ANALYSIS RESULTS")
                print("=" * 60)
                print(f"✅ Decision: {data.get('decision', 'N/A')}")
                print(f"📈 Risk Score: {data.get('risk_score', 0):.2f}")
                print(f"💬 Reason: {data.get('decision_reason', 'N/A')}")
                print()
                
                summary = data.get('summary', {})
                if summary:
                    print("📋 Summary:")
                    for key, value in summary.items():
                        print(f"   {key}: {value}")
                    print()
                
                findings = data.get('findings', [])
                if findings:
                    print(f"⚠️  Findings ({len(findings)}):")
                    for i, finding in enumerate(findings, 1):
                        severity = finding.get('severity', 'unknown')
                        message = finding.get('message', '')
                        print(f"   {i}. [{severity.upper()}] {message}")
                    print()
                else:
                    print("✅ No security issues found!")
                    print()
                
                ci_annotation = data.get('ci_annotation', {})
                if ci_annotation:
                    print("🔧 CI Annotation:")
                    print(f"   Status: {ci_annotation.get('status', 'N/A')}")
                    print(f"   Title: {ci_annotation.get('title', 'N/A')}")
                    print()
                
                print("=" * 60)
                print("✅ Test completed successfully!")
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text[:500]}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("🚀 Kairo Direct API Test")
    print()
    
    try:
        asyncio.run(test_kairo_direct())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
