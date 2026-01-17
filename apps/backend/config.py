"""
SATOR Ops Configuration

Centralized configuration with feature flags for sponsor integrations.
All sponsor integrations are optional sidecars that do not gate core functionality.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class SATORConfig(BaseSettings):
    """Configuration settings for SATOR Ops"""
    
    # Core settings
    data_dir: str = Field(default="./app/data", description="Directory for JSON file persistence")
    simulation_seed: int = Field(default=42, description="Seed for deterministic simulations")
    
    # Simulation settings
    default_sample_rate: float = Field(default=1.0, description="Samples per second")
    default_duration_sec: int = Field(default=300, description="Default scenario duration in seconds")
    
    # Trust layer thresholds
    trust_degraded_threshold: float = Field(default=0.7, description="Score below which sensor is 'Degraded'")
    trust_untrusted_threshold: float = Field(default=0.4, description="Score below which sensor is 'Untrusted'")
    trust_quarantine_threshold: float = Field(default=0.2, description="Score below which sensor is 'Quarantined'")
    
    # Sponsor integration flags (all optional)
    enable_leanmcp: bool = Field(default=True, description="Enable LeanMCP tool registry (Primary sponsor)")
    enable_kairo: bool = Field(default=True, description="Enable Kairo on-chain anchoring (Primary sponsor)")
    enable_arize: bool = Field(default=False, description="Enable Arize observability (Secondary sponsor)")
    enable_browserbase: bool = Field(default=False, description="Enable Browserbase evidence fetch (Secondary sponsor)")
    
    # Kairo settings (only used if enable_kairo=True)
    kairo_api_key: str | None = Field(default=None, description="Kairo API key for Solana anchoring")
    solana_rpc_url: str = Field(default="https://api.devnet.solana.com", description="Solana RPC endpoint")
    
    # Arize settings (only used if enable_arize=True)
    arize_api_key: str | None = Field(default=None, description="Arize API key")
    arize_space_key: str | None = Field(default=None, description="Arize space key")
    
    # Browserbase settings (only used if enable_browserbase=True)
    browserbase_api_key: str | None = Field(default=None, description="Browserbase API key")
    
    # MongoDB Atlas settings
    mongodb_uri: str | None = Field(default=None, description="MongoDB Atlas connection URI")
    mongodb_database: str = Field(default="sator_ops", description="MongoDB database name")
    enable_mongodb: bool = Field(default=False, description="Enable MongoDB persistence")
    
    model_config = {
        "env_prefix": "SATOR_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
    
    def get_data_path(self, subdir: str) -> Path:
        """Get path to a data subdirectory, creating if needed"""
        path = Path(self.data_dir) / subdir
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global config instance
config = SATORConfig()
