# Kairo Quick Start 🚀

## 1. Get Your API Key

```bash
# Sign up at https://app.kairoaisec.com
# Add to .env:
SATOR_KAIRO_API_KEY=kairo_sk_live_xxxxx
SATOR_ENABLE_KAIRO=true
```

## 2. Register Your Contract

```bash
# Via API
curl -X POST http://localhost:8000/api/kairo/contracts/register \
  -H "Content-Type: application/json" \
  -d '{
    "contract_name": "sator_anchor",
    "code": "pragma solidity ^0.8.0; contract MyContract { ... }",
    "language": "solidity",
    "version": "1.0.0"
  }'
```

## 3. Run Pre-Deployment Check

```bash
# Via API
curl -X POST http://localhost:8000/api/kairo/contracts/pre-deploy-check \
  -H "Content-Type: application/json" \
  -d '{
    "contract_name": "sator_anchor",
    "network": {"chain_id": 103, "name": "devnet"}
  }'
```

## 4. CI/CD Check (Before Deploy)

```bash
cd apps/backend
python scripts/kairo_ci_check.py --contract sator_anchor --network devnet
```

## 5. GitHub Actions (Automatic)

The workflow `.github/workflows/kairo-pre-deploy.yml` runs automatically on:
- Push to `main` or `develop`
- Pull requests
- Contract file changes

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/kairo/contracts/register` | POST | Register new contract version |
| `/api/kairo/contracts/pre-deploy-check` | POST | Run deployment gate |
| `/api/kairo/contracts/analyze` | POST | Analyze contract code |
| `/api/kairo/contracts/{name}/versions` | GET | List all versions |
| `/api/kairo/contracts/{name}/latest` | GET | Get latest version |

## Python Usage

```python
from app.integrations.kairo.contract_manager import get_contract_manager

manager = get_contract_manager()

# Register
version = await manager.register_contract(
    contract_name="MyToken",
    code=contract_code,
    language="solidity"
)

# Pre-deploy check
gate = await manager.pre_deployment_check(
    contract_name="MyToken",
    version="latest",
    network={"chain_id": 103, "name": "devnet"}
)

if gate.can_deploy:
    print("✅ Safe to deploy")
```

## Decision Meanings

- **ALLOW** ✅ - Safe to deploy
- **WARN** ⚠️ - Deploy with caution (review warnings)
- **BLOCK** ❌ - Do not deploy (security issues found)
- **ESCALATE** 🔴 - Requires manual review

## Need Help?

See [KAIRO_SETUP_GUIDE.md](./KAIRO_SETUP_GUIDE.md) for detailed documentation.
