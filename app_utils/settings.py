"""
Production Stability Settings
Provides environment-based configuration with safe defaults.
"""
import os

# AI Kill-Switch: Default FALSE for production safety
# Only enable AI when you explicitly set ORCHID_AI_ENABLED=true in environment
ORCHID_AI_ENABLED = os.getenv("ORCHID_AI_ENABLED", "false").lower() == "true"

# OpenAI API Key (required if AI is enabled)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Log AI status at startup
if ORCHID_AI_ENABLED:
    if OPENAI_API_KEY:
        print("✅ AI ENABLED - OpenAI integration active")
    else:
        print("⚠️  AI ENABLED but no API key found - will fail on AI requests")
else:
    print("🔒 AI DISABLED - All OpenAI calls will return placeholder responses")
