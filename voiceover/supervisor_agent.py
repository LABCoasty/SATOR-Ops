"""
SATOR Virtual Supervisor - LiveKit Agent

This agent provides a voice-based virtual supervisor that operators can call
for help. Uses LiveKit Agents for real-time voice conversation.
"""

import asyncio
import logging
from typing import Optional

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import silero

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("supervisor-agent")


# Supervisor persona prompt
SUPERVISOR_PROMPT = """
You are a SENIOR SATOR SUPERVISOR speaking on a live voice call with an operator.

VOICE STYLE:
- Professional, calm, and authoritative
- Speak in short sentences (conversational, not lecture-style)
- Address the operator directly as "you"
- Give direct guidance, not just information
- Keep responses under 30 seconds of speech

SATOR SYSTEM KNOWLEDGE:
- Trust scores range from 0.0 to 1.0 (below 0.5 is concerning)
- Trust states: trusted, degraded, untrusted, quarantined
- Postures: monitor, verify, escalate, contain, defer
- Reason codes:
  * RC10: Redundant sensors that should agree are in conflict
  * RC11: Physical laws are being violated by sensor readings

YOUR ROLE ON THIS CALL:
1. Greet the operator professionally
2. If you have context, acknowledge what you see on their dashboard
3. Ask what specific help they need
4. Provide clear, actionable guidance
5. If situation is critical, recommend escalation to physical site check

EXAMPLE RESPONSES:
- "I see RC10 is active - that's a redundancy conflict. Have you checked if both sensors are physically connected?"
- "With a trust score below 0.5, I'd recommend deferring any actions until we verify the sensor readings."
- "Let me walk you through the next steps for this situation."
- "Based on what I'm seeing, I recommend we escalate this to the on-site team."
"""


async def get_initial_context(room: rtc.Room) -> Optional[dict]:
    """
    Get dashboard context from the frontend via data channel.
    Returns None if no context is available.
    """
    # Context will be sent by frontend when call starts
    # For now, return None (will implement data channel later)
    return None


def build_system_prompt(context: Optional[dict] = None) -> str:
    """Build the system prompt with optional dashboard context."""
    base_prompt = SUPERVISOR_PROMPT
    
    if context:
        context_section = f"""

CURRENT OPERATOR SITUATION:
- Page: {context.get('currentPage', 'Unknown')}
- Incident: {context.get('incidentId', 'None')}
- Trust Score: {context.get('trustScore', 'Unknown')}
- Trust State: {context.get('trustState', 'Unknown')}
- Active Contradictions: {', '.join(context.get('contradictions', [])) or 'None'}
- Recommended Posture: {context.get('posture', 'Unknown')}

Start by acknowledging what you see on their dashboard before asking how you can help.
"""
        return base_prompt + context_section
    
    return base_prompt + "\n\nNo dashboard context available. Start by greeting and asking how you can help."


async def entrypoint(ctx: JobContext):
    """
    LiveKit Agent entrypoint.
    Called when an operator starts a supervisor call.
    """
    logger.info(f"Supervisor call started in room: {ctx.room.name}")
    
    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Get dashboard context (if available)
    context = await get_initial_context(ctx.room)
    system_prompt = build_system_prompt(context)
    
    # Create the voice assistant with LiveKit's built-in pipeline
    assistant = VoiceAssistant(
        vad=silero.VAD.load(),  # Voice Activity Detection
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=system_prompt
        ),
        # Enable natural conversation
        allow_interruptions=True,
        interrupt_speech_duration=0.5,
        # Prevent long silences
        min_endpointing_delay=0.5,
    )
    
    # Start the assistant
    assistant.start(ctx.room)
    
    # Initial greeting
    if context:
        greeting = f"Hello, this is Supervisor Control. I can see you're on the {context.get('currentPage', 'dashboard')}. How can I help you today?"
    else:
        greeting = "Hello, this is Supervisor Control. How can I help you today?"
    
    await assistant.say(greeting, allow_interruptions=True)
    
    logger.info("Supervisor assistant started and greeting sent")


def prewarm(proc: JobProcess):
    """Prewarm the agent process for faster startup."""
    proc.userdata["vad"] = silero.VAD.load()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
