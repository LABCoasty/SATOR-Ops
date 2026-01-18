# Overshoot.ai Video Disaster Ingest

Disaster scenario driven by **live video** via [Overshoot.ai](https://docs.overshoot.ai/). Overshoot runs AI on a rolling window of video and returns structured JSON. This backend converts that JSON into SATOR telemetry and events CSV for ingest.

**For Scenario 2 workflow** (video → Overshoot → LeanMCP → Decision Cards), see [SCENARIO_WORKFLOWS.md](./SCENARIO_WORKFLOWS.md#scenario-2-live-video--overshoot--leanmcp--decision-cards).

## Flow

1. **Start the video_disaster scenario**  
   `POST /simulation/start` with `{"scenario_id": "video_disaster"}`.

2. **Get the outputSchema**  
   `GET /ingest/overshoot/schema` returns the JSON schema to use as `outputSchema` in Overshoot’s RealtimeVision.

3. **Run Overshoot in the frontend**  
   - Point a video source (camera, file, stream) at Overshoot.  
   - Use a disaster-detection prompt, e.g.:  
     *"Detect: person count, water level (0–100), fire, smoke level (none/light/medium/dense), structural damage (none/moderate/severe), injured persons."*  
   - Set `outputSchema` to the object returned by `GET /ingest/overshoot/schema`.  
   - In `onResult`, POST each `result.result` (or batched) to the ingest API.

4. **Ingest Overshoot JSON**  
   `POST /ingest/overshoot` with a single JSON object or an array of objects. Each object must match `OvershootDisasterRecord` (see schema). The backend appends rows to:

   - `{data_dir}/generated/video_disaster_telemetry.csv`
   - `{data_dir}/generated/video_disaster_events.csv`
   - `{data_dir}/generated/video_disaster_sensors.csv` (written once on start)

5. **Use simulation and replay**  
   - `GET /simulation/telemetry`, `GET /simulation/telemetry/range`, `POST /simulation/advance` work as for other scenarios, using the ingested video-derived telemetry.  
   - `GET /simulation/timeline` returns events from the events CSV.

## Example: Overshoot RealtimeVision (JavaScript)

```javascript
import { RealtimeVision } from 'overshoot';  // or your Overshoot SDK import

const schemaRes = await fetch('http://localhost:8000/ingest/overshoot/schema');
const { outputSchema } = await schemaRes.json();

const vision = new RealtimeVision({
  apiUrl: 'https://cluster1.overshoot.ai/api/v0.2',
  apiKey: process.env.OVERSHOOT_API_KEY,
  prompt: 'Detect disaster: person count, water level 0-100, fire, smoke (none/light/medium/dense), structural damage (none/moderate/severe), injured.',
  outputSchema,
  onResult: async (result) => {
    const data = JSON.parse(result.result);
    data.timestamp_ms = data.timestamp_ms ?? Date.now();
    await fetch('http://localhost:8000/ingest/overshoot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
});
vision.start();
```

## CSV formats

- **Telemetry**: `timestamp,tag_id,sensor_name,value,unit,quality,time_sec,redundancy_group`  
  Virtual tags: `video_person_count`, `video_water_level`, `video_fire_detected`, `video_smoke_level`, `video_structural_damage`, `video_injured_detected`.

- **Events**: `timestamp,time_sec,event_type,severity,tag_id,reason_code,description,action_required`  
  Events are emitted when e.g. fire or injured is first detected, smoke/damage escalate, or water level crosses a threshold.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ingest/overshoot/schema` | `outputSchema` for Overshoot |
| POST | `/ingest/overshoot` | Ingest one or more Overshoot JSON records |
| GET | `/ingest/video/status` | `{ running, time_sec, has_data }` |
