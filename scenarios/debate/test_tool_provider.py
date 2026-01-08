import asyncio
import aiohttp
import json

async def test_tool_provider():
    """Test if ToolProvider.talk_to_agent would work"""
    
    async with aiohttp.ClientSession() as session:
        # Test pro debater
        url = "http://127.0.0.1:9019/"
        message = "Debate Topic: Should AI be regulated? Present your opening argument."
        
        print(f"Testing pro debater at {url}")
        print(f"Message: {message}")
        
        # Send request (format ToolProvider uses)
        payload = {"message": message}
        
        try:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Success!")
                    print(f"Response: {json.dumps(result, indent=2)}")
                    
                    # Check format
                    if result.get("status") == "completed" and "response" in result:
                        print("✅ Format matches ToolProvider expectations!")
                        return result["response"]
                    else:
                        print("❌ Format does NOT match expectations")
                else:
                    text = await response.text()
                    print(f"❌ Error {response.status}: {text}")
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return None

if __name__ == "__main__":
    response = asyncio.run(test_tool_provider())
    if response:
        print(f"\nDebater response: {response[:200]}...")