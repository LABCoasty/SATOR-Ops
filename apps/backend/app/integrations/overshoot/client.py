"""
Overshoot Client - WebSocket/HTTP client to receive Overshoot vision JSON.

Connects to Overshoot AI vision service and processes real-time video analysis.
"""

import asyncio
import json
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any
from pydantic import BaseModel
import httpx

from .models import (
    VisionFrame,
    VisionAnalysis,
    OvershootWebhookPayload,
    EquipmentState,
    OperatorAction,
    SafetyEvent,
)


class OvershootConfig(BaseModel):
    """Configuration for Overshoot client."""
    api_url: str = "https://api.overshoot.ai"
    api_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    session_id: Optional[str] = None


class OvershootClient:
    """
    Client for receiving and processing Overshoot AI vision data.
    
    Handles:
    - Webhook payload validation
    - Vision frame processing
    - Event callbacks for real-time updates
    """
    
    def __init__(self, config: Optional[OvershootConfig] = None):
        """Initialize the Overshoot client."""
        self.config = config or OvershootConfig()
        self._callbacks: List[Callable[[VisionFrame], None]] = []
        self._analysis_callbacks: List[Callable[[VisionAnalysis], None]] = []
        self._latest_frame: Optional[VisionFrame] = None
        self._frame_history: List[VisionFrame] = []
        self._max_history = 100
    
    # ========================================================================
    # Webhook Processing
    # ========================================================================
    
    def process_webhook(self, payload: Dict[str, Any]) -> OvershootWebhookPayload:
        """
        Process incoming webhook payload from Overshoot.
        
        Args:
            payload: Raw webhook JSON payload
            
        Returns:
            Validated OvershootWebhookPayload
        """
        webhook_data = OvershootWebhookPayload(**payload)
        
        if webhook_data.frame:
            self._handle_frame(webhook_data.frame)
        
        if webhook_data.analysis:
            self._handle_analysis(webhook_data.analysis)
        
        return webhook_data
    
    def _handle_frame(self, frame: VisionFrame):
        """Handle incoming vision frame."""
        self._latest_frame = frame
        self._frame_history.append(frame)
        
        # Trim history
        if len(self._frame_history) > self._max_history:
            self._frame_history = self._frame_history[-self._max_history:]
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(frame)
            except Exception as e:
                print(f"Error in vision frame callback: {e}")
    
    def _handle_analysis(self, analysis: VisionAnalysis):
        """Handle incoming vision analysis."""
        for callback in self._analysis_callbacks:
            try:
                callback(analysis)
            except Exception as e:
                print(f"Error in vision analysis callback: {e}")
    
    # ========================================================================
    # Callbacks
    # ========================================================================
    
    def on_frame(self, callback: Callable[[VisionFrame], None]):
        """Register callback for new vision frames."""
        self._callbacks.append(callback)
    
    def on_analysis(self, callback: Callable[[VisionAnalysis], None]):
        """Register callback for vision analysis updates."""
        self._analysis_callbacks.append(callback)
    
    # ========================================================================
    # Data Access
    # ========================================================================
    
    def get_latest_frame(self) -> Optional[VisionFrame]:
        """Get the most recent vision frame."""
        return self._latest_frame
    
    def get_frame_history(self, limit: int = 10) -> List[VisionFrame]:
        """Get recent frame history."""
        return self._frame_history[-limit:]
    
    def get_equipment_states(self) -> List[EquipmentState]:
        """Get current equipment states from latest frame."""
        if self._latest_frame:
            return self._latest_frame.equipment_states
        return []
    
    def get_active_safety_events(self) -> List[SafetyEvent]:
        """Get active safety events from latest frame."""
        if self._latest_frame:
            return [e for e in self._latest_frame.safety_events if not e.resolved]
        return []
    
    # ========================================================================
    # Simulation Support (for demo)
    # ========================================================================
    
    def simulate_frame(self, frame_data: Dict[str, Any]) -> VisionFrame:
        """
        Simulate receiving a vision frame (for demo purposes).
        
        Args:
            frame_data: Frame data dictionary
            
        Returns:
            Processed VisionFrame
        """
        frame = VisionFrame(**frame_data)
        self._handle_frame(frame)
        return frame
    
    def load_simulation_frames(self, filepath: str) -> List[VisionFrame]:
        """
        Load simulation frames from a JSON file.
        
        Args:
            filepath: Path to JSON file with frame data
            
        Returns:
            List of loaded VisionFrames
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        frames = []
        for frame_data in data.get('frames', []):
            frame = VisionFrame(**frame_data)
            frames.append(frame)
        
        return frames


# ============================================================================
# Singleton instance
# ============================================================================

_overshoot_client: Optional[OvershootClient] = None


def get_overshoot_client() -> OvershootClient:
    """Get the singleton OvershootClient instance."""
    global _overshoot_client
    if _overshoot_client is None:
        _overshoot_client = OvershootClient()
    return _overshoot_client
