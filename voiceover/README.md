# SATOR Virtual Supervisor - Voice Call

AI-powered virtual supervisor that operators can call for real-time voice guidance.

## Setup

1. Install dependencies:
```bash
cd voiceover
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export LIVEKIT_API_KEY=your_api_key
export LIVEKIT_API_SECRET=your_api_secret
export LIVEKIT_URL=wss://your-project.livekit.cloud
```

3. Run the agent:
```bash
python supervisor_agent.py dev
```

## How It Works

1. Operator clicks "Call Supervisor for Help" in the dashboard
2. Frontend creates a LiveKit room and connects
3. This agent joins the room and starts the voice conversation
4. AI supervisor speaks with the operator using voice generation
5. Operator can end the call anytime

## Configuration

Edit `supervisor_agent.py` to customize:
- `SUPERVISOR_PROMPT` - The AI persona and knowledge
- Voice settings (interruption handling, silence detection)
