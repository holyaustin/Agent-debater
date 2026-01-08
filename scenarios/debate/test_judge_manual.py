import asyncio
import json
import sys
import os

# Add project to path
sys.path.insert(0, os.path.expanduser("~/Dapps-Empty/2025/Dec2025/agentbeat-tutorial"))

from agentbeats.tool_provider import ToolProvider

async def test_judge_manual():
    """Test the judge agent manually"""
    
    tool_provider = ToolProvider()
    
    # Test participants
    participants = {
        "pro_debater": "http://127.0.0.1:9019/",
        "con_debater": "http://127.0.0.1:9018/"
    }
    
    topic = "Should artificial intelligence be regulated?"
    
    print("🧪 Testing judge manually...")
    print(f"Topic: {topic}")
    print(f"Participants: {participants}")
    
    # Test talking to pro debater
    try:
        print("\n1. Testing pro debater...")
        pro_response = await tool_provider.talk_to_agent(
            f"Debate Topic: {topic}. Present your opening argument.",
            participants["pro_debater"],
            new_conversation=True
        )
        print(f"✅ Pro response: {pro_response[:100]}...")
    except Exception as e:
        print(f"❌ Error with pro debater: {e}")
    
    # Test talking to con debater
    try:
        print("\n2. Testing con debater...")
        con_response = await tool_provider.talk_to_agent(
            f"Debate Topic: {topic}. Present your opening argument.",
            participants["con_debater"],
            new_conversation=True
        )
        print(f"✅ Con response: {con_response[:100]}...")
    except Exception as e:
        print(f"❌ Error with con debater: {e}")
    
    print("\n✅ Manual test completed!")

if __name__ == "__main__":
    asyncio.run(test_judge_manual())