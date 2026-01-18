"""
Overshoot.ai video disaster integration.

Converts Overshoot RealtimeVision JSON (outputSchema) into SATOR telemetry and
events CSV for ingest. Use with POST /ingest/overshoot.

Frontend: use Overshoot SDK (https://docs.overshoot.ai/) with outputSchema
matching app.models.overshoot.OvershootDisasterRecord, then POST each
result (or batch) to /ingest/overshoot.
"""

from .converter import (
    get_video_sensor_csv_rows,
    overshoot_to_event_rows,
    overshoot_to_telemetry_rows,
)
from .video_manager import VideoDisasterManager

__all__ = [
    "VideoDisasterManager",
    "get_video_sensor_csv_rows",
    "overshoot_to_event_rows",
    "overshoot_to_telemetry_rows",
]
