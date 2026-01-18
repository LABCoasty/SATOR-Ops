"""
Overshoot AI Vision Integration.

Integrates with Overshoot (https://overshoot.ai/) for real-time AI vision
processing of video feeds to detect equipment states, operator actions,
and safety events.
"""

from .models import (
    VisionFrame,
    EquipmentState,
    OperatorAction,
    SafetyEvent,
    VisionAnalysis,
    EquipmentType,
    ActionType as VisionActionType,
    SafetyEventType,
    OvershootWebhookPayload,
)
from .client import OvershootClient, get_overshoot_client

__all__ = [
    "VisionFrame",
    "EquipmentState",
    "OperatorAction",
    "SafetyEvent",
    "VisionAnalysis",
    "EquipmentType",
    "VisionActionType",
    "SafetyEventType",
    "OvershootWebhookPayload",
    "OvershootClient",
    "get_overshoot_client",
]
