import argparse
import uvicorn
import asyncio
import logging
import os
import json
import uuid
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debater")

app = FastAPI()

class DebaterAgent:
    """Simple debater agent that takes a position"""
    
    def __init__(self, role: str = "pro"):
        self.role = role
        self.position = "in favor" if role == "pro" else "against"
    
    async def handle_message(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a message from the green agent (judge)"""
        logger.info(f"{self.role} debater handling message: {content}")
        
        # Extract topic and round info from content
        topic = content.get("topic", "Unknown topic")
        round_num = content.get("round", 1)
        previous_args = content.get("previous_arguments", "")
        
        # Generate response text based on role and round
        if self.role == "pro":
            if round_num == 1:
                response_text = f"As the pro debater, I'm {self.position} '{topic}'. Regulation could stifle innovation and slow down beneficial AI advancements. The tech industry should self-regulate with ethical guidelines."
            else:
                response_text = f"Continuing as pro: Self-regulation allows faster adaptation to new risks. The con's argument about safety ignores industry's track record of responsible innovation. We need flexibility, not rigid rules."
        else:
            if round_num == 1:
                response_text = f"As the con debater, I'm {self.position} '{topic}'. Regulation is necessary for safety, bias prevention, and privacy. Without oversight, AI could cause societal harm with unaccountable systems."
            else:
                response_text = f"Continuing as con: The pro's self-regulation argument is naive. Industry profits often override safety. Government oversight ensures accountability and protects public interest over corporate interests."
        
        return {
            "role": self.role,
            "position": self.position,
            "argument": response_text,
            "topic": topic,
            "round": round_num
        }

# Global variables
debater = None
port = None

@app.post("/")
async def handle_jsonrpc(request: Request):
    """Handle JSON-RPC requests following A2A protocol"""
    global debater
    
    try:
        data = await request.json()
        logger.info(f"Received JSON-RPC request from: {request.client.host if request.client else 'unknown'}")
        
        if "jsonrpc" in data and data["jsonrpc"] == "2.0":
            method = data.get("method", "")
            params = data.get("params", {})
            jsonrpc_id = data.get("id", 1)
            
            logger.info(f"Method: {method}, ID: {jsonrpc_id}")
            
            # Handle the standard A2A method
            if method == "message/send":
                # Extract content from params
                if isinstance(params, dict):
                    content = params
                elif isinstance(params, list) and len(params) > 0:
                    content = params[0]
                else:
                    content = {"text": str(params)}
                
                result = await debater.handle_message(content)
                
                # Return simple JSON-RPC response (not complex Task/Message structure)
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": jsonrpc_id
                })
            
            # Method not found
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601, 
                    "message": f"Method '{method}' not found. Supported methods: message/send"
                },
                "id": jsonrpc_id
            })
        
        # Not a JSON-RPC 2.0 request
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid JSON-RPC request"},
            "id": None
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None
        })
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": data.get("id", 1) if 'data' in locals() else None
        })

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/.well-known/agent-card.json")
async def agent_card():
    """Return the agent card for service discovery"""
    global debater, port
    role = debater.role if debater else "unknown"
    
    return {
        "name": f"{role}_debater",
        "description": f"Professional debater ({role} side)",
        "url": f"http://127.0.0.1:{port}/",
        "version": "1.0.0",
        "skills": [
            {
                "name": "argument_generation",
                "description": "Generates persuasive arguments for debate"
            },
            {
                "name": "debate_response",
                "description": "Responds to opposing arguments in debate"
            }
        ],
        "capabilities": {"streaming": False},
        "defaultInputModes": ["JSON_RPC"],
        "defaultOutputModes": ["JSON_RPC"]
    }

@app.get("/")
async def root():
    global debater
    role = debater.role if debater else "unknown"
    
    return {
        "service": f"{role}_debater",
        "status": "running",
        "role": role,
        "endpoint": "POST / (JSON-RPC 2.0)",
        "methods": ["message/send"]
    }

def main():
    global debater, port
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--role", default="pro", choices=["pro", "con"])
    args = parser.parse_args()
    
    port = args.port
    debater = DebaterAgent(args.role)
    
    logger.info(f"🚀 Starting {args.role} debater on http://{args.host}:{args.port}")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()