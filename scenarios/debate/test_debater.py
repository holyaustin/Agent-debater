import asyncio
import aiohttp
import json

async def test_debater(port: int, role: str):
    url = f"http://127.0.0.1:{port}/"
    payload = {
        "jsonrpc": "2.0",
        "method": "execute",
        "params": {"message": f"Hello {role}, what is your position on AI regulation?"},
        "id": 1
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            print(f"\n{role.upper()} RESPONSE:")
            print(json.dumps(result, indent=2))
            return result

async def main():
    # Test both debaters
    await test_debater(9019, "pro")
    await test_debater(9018, "con")

if __name__ == "__main__":
    asyncio.run(main())