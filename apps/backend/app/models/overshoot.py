"""
Overshoot.ai disaster detection models.

Structured JSON schema for Overshoot RealtimeVision outputSchema when
analyzing live video for disaster scenarios (flood, fire, earthquake, etc.).
See: https://docs.overshoot.ai/
"""

from typing import Any

from pydantic import BaseModel, Field


# --- Ordinal mappings for CSV value columns ---
SMOKE_LEVEL_MAP = {"none": 0.0, "light": 1.0, "medium": 2.0, "dense": 3.0}
STRUCTURAL_DAMAGE_MAP = {"none": 0.0, "moderate": 1.0, "severe": 2.0}


class OvershootDisasterRecord(BaseModel):
    """
    One window's structured output from Overshoot.ai RealtimeVision.

    Use this as outputSchema when configuring Overshoot, e.g.:

        outputSchema: {
          type: 'object',
          properties: {
            timestamp_ms: { type: 'integer' },
            person_count: { type: 'number' },
            water_level: { type: 'number' },
            fire_detected: { type: 'boolean' },
            smoke_level: { type: 'string', enum: ['none','light','medium','dense'] },
            structural_damage: { type: 'string', enum: ['none','moderate','severe'] },
            injured_detected: { type: 'boolean' },
            objects: { type: 'array', items: { type: 'object', properties: { label: {}, confidence: {} } } }
          },
          required: ['timestamp_ms', 'person_count', 'fire_detected']
        }
    """

    timestamp_ms: int = Field(..., description="Window timestamp in milliseconds (epoch)")
    person_count: int = Field(default=0, ge=0, description="Number of people in frame")
    water_level: float = Field(default=0.0, ge=0.0, le=100.0, description="0-100 or 0-1 scale")
    fire_detected: bool = Field(default=False, description="Flame/fire visible")
    smoke_level: str = Field(
        default="none",
        description="none | light | medium | dense",
    )
    structural_damage: str = Field(
        default="none",
        description="none | moderate | severe",
    )
    injured_detected: bool = Field(default=False, description="Person(s) in distress/injured")
    disaster_type: str | None = Field(default=None, description="flood | fire | earthquake | generic")
    location_id: str | None = Field(default=None, description="Zone or camera ID")
    objects: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detected objects: [{label, confidence, bbox?}]",
    )
    notes: str | None = Field(default=None, description="Free-form model notes")
