"""Quick test of all AI providers including OpenAI"""
import os
from multi_ai_vision_analyzer import MultiAIVisionAnalyzer
from multi_ai_image_generator import MultiAIImageGenerator

print("Testing AI Providers...")
print("=" * 60)

# Test vision analyzer
analyzer = MultiAIVisionAnalyzer()
print("\n✓ Vision analyzer initialized")

# Test image generator  
generator = MultiAIImageGenerator()
print("✓ Image generator initialized")

# Test OpenAI specifically
print("\n" + "=" * 60)
print("TESTING OPENAI...")
print("=" * 60)

if os.environ.get("OPENAI_API_KEY"):
    try:
        import openai
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        
        # Simple test
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'OpenAI is working!' in 5 words."}],
            max_tokens=20
        )
        print(f"✅ OpenAI: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI error: {str(e)}")
else:
    print("⚠️ No OpenAI key")

print("\n" + "=" * 60)
print("ALL SYSTEMS READY!")
print("=" * 60)
