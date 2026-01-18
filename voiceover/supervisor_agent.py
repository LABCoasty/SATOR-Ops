"""
SATOR Virtual Supervisor - Production-Ready LiveKit Voice Agent

Based on LiveKit Workshop: Building Production-Ready Voice Agents
Features implemented:
1. Semantic Turn Detection - prevents awkward interruptions
2. Fallback Adapters - survives provider outages
3. Metrics Collection - tracks latency and usage
4. Preemptive Generation - reduces response delay
5. Function Tools - SATOR-specific actions
6. Consent Collection - compliance workflow
7. Escalation to Real Supervisor - human handoff
"""

import logging
import aiohttp

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    AgentTask,
    AgentStateChangedEvent,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RunContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
    get_job_context,
    llm,
    metrics,
    stt,
    tts,
)
from livekit.agents.llm import function_tool
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("sator-supervisor")
load_dotenv(".env.local")


# =============================================================================
# SATOR Supervisor Instructions
# =============================================================================

SUPERVISOR_INSTRUCTIONS = """You are a SENIOR SATOR SUPERVISOR speaking on a live voice call with an operator who needs help with the SATOR decision infrastructure dashboard.

# Your Role
You are a calm, professional supervisor helping operators understand and navigate the SATOR system - a decision infrastructure for physical systems that manages sensor trust, contradictions, and decision recording.

# SATOR System Knowledge
- Trust Scores: Range from zero to one. Below point five is concerning, below point two is quarantine territory.
- Trust States: trusted, degraded, untrusted, quarantined
- Postures: monitor (all clear), verify (check sensors), escalate (call physical site), contain (isolate zone), defer (wait for more info)
- Reason Codes:
  - RC ten: Redundant sensors that should agree are showing conflicting readings
  - RC eleven: Physical laws are being violated - sensor readings are impossible
- Contradictions: When sensors disagree or physics is violated

# Output Rules
- Respond in plain text only. Never use JSON, markdown, or lists.
- Keep replies brief: one to three sentences. Ask one question at a time.
- Spell out numbers clearly (say "point five" not "0.5").
- Speak like a real supervisor on a phone call - professional but personable.

# Conversation Flow
1. Greet: "This is Supervisor Control, how can I help you today?"
2. Understand: Ask what they're seeing or what they need help with
3. Guide: Give clear, actionable steps
4. Confirm: Check if they understood before moving on

# Available Tools
- lookup_incident: Get details about a specific incident
- check_sensor_status: Check the current status of a sensor
- escalate_to_human: Transfer to a real human supervisor if needed

# Guardrails
- Stay focused on SATOR dashboard help
- If you don't know something specific about their data, ask them to describe what they see
- For serious safety situations, always recommend physical site escalation
- If the user asks for a real person, use the escalate_to_human tool"""


# =============================================================================
# Consent Collection Task
# =============================================================================

class CollectConsent(AgentTask[bool]):
    """Collects recording consent before the main conversation."""
    
    def __init__(self, chat_ctx=None):
        super().__init__(
            instructions="""
            Ask for recording consent and get a clear yes or no answer.
            Be polite and professional. This is a SATOR supervisor call.
            """,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="""
            Briefly introduce yourself as SATOR Supervisor Control, 
            then ask for permission to record the call for quality assurance 
            and training purposes. Make it clear that they can decline.
            """
        )

    @function_tool
    async def consent_given(self) -> None:
        """Use this when the user gives consent to record."""
        self.complete(True)

    @function_tool
    async def consent_denied(self) -> None:
        """Use this when the user denies consent to record."""
        self.complete(False)


# =============================================================================
# Human Supervisor Agent (for escalation)
# =============================================================================

class HumanSupervisor(Agent):
    """Placeholder agent when escalating to a real human supervisor."""
    
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=(
                "You are a senior human supervisor for SATOR operations. "
                "Handle escalations professionally. Let the caller know you're "
                "reviewing the situation and will provide guidance."
            ),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="Introduce yourself as the senior supervisor and ask how you can help with this escalated situation.",
            allow_interruptions=True,
        )


# =============================================================================
# Main SATOR Supervisor Agent
# =============================================================================

class SATORSupervisor(Agent):
    """Virtual Supervisor that helps operators with SATOR dashboard."""
    
    def __init__(self) -> None:
        super().__init__(instructions=SUPERVISOR_INSTRUCTIONS)

    async def on_enter(self) -> None:
        """Called when operator connects. Runs consent flow first."""
        # Collect consent before proceeding
        consent = await CollectConsent(chat_ctx=self.chat_ctx).run(self.session)
        
        if consent:
            await self.session.generate_reply(
                instructions="Thank them for consent and offer your assistance as SATOR Supervisor Control.",
                allow_interruptions=True,
            )
        else:
            await self.session.generate_reply(
                instructions="Inform them you understand and will proceed without recording. Then offer your assistance.",
                allow_interruptions=True,
            )

    # =========================================================================
    # Function Tools
    # =========================================================================

    @function_tool
    async def lookup_incident(self, context: RunContext, incident_id: str) -> str:
        """Look up details about a specific SATOR incident."""
        logger.info("Looking up incident: %s", incident_id)
        
        try:
            # Call SATOR backend API
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:8000/api/replay/state-at",
                    params={"t": "2026-01-14T10:01:00"}  # Example timestamp
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        trust_state = data.get("trust_snapshot", {}).get("zone_trust_state", "unknown")
                        posture = data.get("posture", "unknown")
                        claim = data.get("claim", "No claim available")
                        return f"Incident shows {trust_state} trust state with {posture} posture. Current claim: {claim}"
                    
                    return "Unable to retrieve incident details at this time."
        except Exception as exc:
            logger.error("Error fetching incident: %s", exc)
            return "The incident lookup service is temporarily unavailable."

    @function_tool
    async def check_sensor_status(self, context: RunContext, sensor_id: str) -> str:
        """Check the current trust status of a specific sensor."""
        logger.info("Checking sensor status: %s", sensor_id)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:8000/api/temporal/trust-evolution/{sensor_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        score = data.get("end_score", "unknown")
                        degradation = data.get("total_degradation", 0)
                        time_to_quarantine = data.get("time_to_quarantine")
                        
                        result = f"Sensor {sensor_id} has a trust score of {score}."
                        if degradation > 0:
                            result += f" It has degraded by {degradation}."
                        if time_to_quarantine:
                            result += f" Time to quarantine was {time_to_quarantine} seconds."
                        return result
                    
                    return f"Unable to find sensor {sensor_id} in the system."
        except Exception as exc:
            logger.error("Error checking sensor: %s", exc)
            return "The sensor status service is temporarily unavailable."

    @function_tool
    async def get_active_contradictions(self, context: RunContext) -> str:
        """Get the list of currently active contradictions."""
        logger.info("Fetching active contradictions")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/temporal/contradiction-patterns"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data:
                            return "No active contradictions detected."
                        
                        patterns = []
                        for p in data[:3]:  # Top 3
                            code = p.get("reason_code", "unknown")
                            count = p.get("count", 0)
                            sensors = ", ".join(p.get("affected_sensors", [])[:2])
                            patterns.append(f"{code} affecting {sensors} with {count} occurrences")
                        
                        return "Active contradictions: " + "; ".join(patterns)
                    
                    return "Unable to retrieve contradiction data."
        except Exception as exc:
            logger.error("Error fetching contradictions: %s", exc)
            return "The contradiction service is temporarily unavailable."

    @function_tool
    async def escalate_to_human(self, context: RunContext) -> tuple:
        """Escalate the call to a real human supervisor."""
        logger.info("Escalating to human supervisor")
        return HumanSupervisor(chat_ctx=self.chat_ctx), "Connecting you to a senior supervisor now. One moment please."


# =============================================================================
# Agent Server Setup
# =============================================================================

def prewarm(proc: JobProcess):
    """Prewarm VAD for faster startup."""
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Entry point when an operator starts a supervisor call."""
    
    # Load VAD from prewarmed process
    vad = ctx.proc.userdata["vad"]
    
    # Metrics collection
    usage_collector = metrics.UsageCollector()
    last_eou_metrics: metrics.EOUMetrics | None = None
    
    # Create session with ALL production features
    session = AgentSession(
        # Fallback adapters for resilience
        llm=llm.FallbackAdapter([
            "openai/gpt-4.1-mini",
            "google/gemini-2.5-flash",
        ]),
        stt=stt.FallbackAdapter([
            "deepgram/nova-3",
            "assemblyai/universal-streaming",
        ]),
        tts=tts.FallbackAdapter([
            "cartesia/sonic-2:a167e0f3-df7e-4d52-a9c3-f949145efdab",
            "openai/tts-1",
        ]),
        
        # Voice activity detection
        vad=vad,
        
        # Semantic turn detection - prevents awkward interruptions
        turn_detection=MultilingualModel(),
        
        # Preemptive generation - reduces response delay
        preemptive_generation=True,
    )
    
    # =========================================================================
    # Metrics Collection
    # =========================================================================
    
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        nonlocal last_eou_metrics
        if ev.metrics.type == "eou_metrics":
            last_eou_metrics = ev.metrics
        
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)
    
    @session.on("agent_state_changed")
    def _on_agent_state_changed(ev: AgentStateChangedEvent):
        if (
            ev.new_state == "speaking"
            and last_eou_metrics
            and session.current_speech
            and last_eou_metrics.speech_id == session.current_speech.id
        ):
            delta = ev.created_at - last_eou_metrics.last_speaking_time
            logger.info("⚡ Time to first audio: %.0fms", delta.total_seconds() * 1000)
    
    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info("📊 Usage summary: %s", summary)
    
    ctx.add_shutdown_callback(log_usage)
    
    # =========================================================================
    # Start the Agent
    # =========================================================================
    
    await session.start(
        agent=SATORSupervisor(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    await ctx.connect()
    logger.info("🎙️ SATOR Supervisor connected to room: %s", ctx.room.name)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
