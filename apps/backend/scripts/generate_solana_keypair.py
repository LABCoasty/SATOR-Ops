#!/usr/bin/env python3
"""
Generate a Solana Devnet keypair for SATOR Ops.

This script generates a new Solana keypair and outputs it in Base58 format
for use in the SATOR_SOLANA_PRIVATE_KEY environment variable.

Note: Solana Devnet is completely FREE - a testing environment with no real value.
Test SOL can be obtained for free from faucets (rate-limited, typically 1-2 SOL per request).
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import base58
    from solders.keypair import Keypair
except ImportError as e:
    print(f"❌ Error: Missing required libraries: {e}")
    print("\nInstall with:")
    print("  pip install base58 solders")
    sys.exit(1)

def main():
    print("=" * 60)
    print("SATOR Ops - Solana Devnet Keypair Generator")
    print("=" * 60)
    
    # Generate a new keypair
    try:
        keypair = Keypair()
    except Exception as e:
        print(f"❌ Error generating keypair: {e}")
        sys.exit(1)
    
    # Get the private key as base58
    try:
        private_key_bytes = bytes(keypair)
        private_key_b58 = base58.b58encode(private_key_bytes).decode()
    except Exception as e:
        print(f"❌ Error encoding private key: {e}")
        sys.exit(1)
    
    print(f"\n✅ Generated Solana Devnet Wallet")
    print(f"\n📍 Public Key: {keypair.pubkey()}")
    print(f"\n🔑 Private Key (Base58 - add to .env as SATOR_SOLANA_PRIVATE_KEY):")
    print(f"   {private_key_b58}")
    print(f"\n💰 Get FREE test SOL (no real value) from faucet:")
    print(f"   https://faucet.solana.com/?address={keypair.pubkey()}")
    print(f"\n   Or use CLI:")
    print(f"   solana airdrop 1 {keypair.pubkey()} --url devnet")
    print(f"\n   Note: Devnet is FREE - faucets are rate-limited (typically 1-2 SOL per request)")
    print("\n" + "=" * 60)
    print("\n💡 Add this to your .env file:")
    print(f"   SATOR_SOLANA_PRIVATE_KEY={private_key_b58}")
    print("=" * 60)

if __name__ == "__main__":
    main()
