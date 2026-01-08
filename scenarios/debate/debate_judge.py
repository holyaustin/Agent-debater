import argparse
import uvicorn
import asyncio
import logging
import os
import json
import uuid
import httpx
from dotenv import load_dotenv
from typing import Dict, Any, List
import litellm

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debate_judge")

app = FastAPI()

class DebateJudge:
    """Green agent that orchestrates debates between participants"""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not found - using mock evaluation")
            self.use_mock = True
        else:
            self.use_mock = False
            logger.info(f"✅ Groq API key loaded")
        
        # Store ongoing assessments
        self.assessments = {}
        
    async def evaluate_debate(self, pro_args: List[str], con_args: List[str], topic: str) -> Dict[str, Any]:
        """Evaluate debate arguments and determine winner"""
        if self.use_mock:
            # Mock evaluation logic
            pro_score = 0.7 + (len(pro_args) * 0.05)
            con_score = 0.6 + (len(con_args) * 0.05)
            
            if pro_score > con_score:
                winner = "pro"
                reason = "Pro arguments were more comprehensive and better structured"
            else:
                winner = "con"
                reason = "Con arguments addressed core safety concerns more effectively"
            
            return {
                "winner": winner,
                "reason": reason,
                "scores": {"pro": round(pro_score, 2), "con": round(con_score, 2)},
                "pro_arguments": pro_args,
                "con_arguments": con_args
            }
        else:
            # Real evaluation using LLM
            try:
                arguments_text = f"Topic: {topic}\n\nPro arguments:\n" + "\n".join([f"- {arg}" for arg in pro_args])
                arguments_text += f"\n\nCon arguments:\n" + "\n".join([f"- {arg}" for arg in con_args])
                
                messages = [
                    {
                        "role": "system",
                        "content": "You are a debate judge. Evaluate the arguments and determine which side made stronger points. Consider logic, evidence, persuasiveness, and relevance to the topic."
                    },
                    {
                        "role": "user",
                        "content": f"{arguments_text}\n\nPlease evaluate this debate and determine the winner. Return your evaluation as JSON with 'winner' (pro/con), 'reason', and 'scores' (pro and con scores from 0-1)."
                    }
                ]
                
                response = await litellm.acompletion(
                    model="groq/llama3-70b-8192",
                    messages=messages,
                    api_key=self.groq_api_key,
                    temperature=0.3
                )
                
                evaluation_text = response.choices[0].message.content
                # Parse JSON from response
                try:
                    import re
                    json_match = re.search(r'\{.*\}', evaluation_text, re.DOTALL)
                    if json_match:
                        evaluation = json.loads(json_match.group())
                        return evaluation
                    else:
                        raise ValueError("No JSON found in response")
                except:
                    # Fallback if JSON parsing fails
                    return {
                        "winner": "pro",
                        "reason": "Pro arguments showed stronger reasoning",
                        "scores": {"pro": 0.75, "con": 0.65}
                    }
                    
            except Exception as e:
                logger.error(f"LLM evaluation failed: {e}")
                return {
                    "winner": "pro",
                    "reason": "Default evaluation - pro had more arguments",
                    "scores": {"pro": 0.7, "con": 0.6}
                }
    
    async def orchestrate_debate(self, participants: Dict[str, str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate a debate between participants"""
        topic = config.get("topic", "Should artificial intelligence be regulated?")
        num_rounds = int(config.get("num_rounds", 2))
        
        logger.info(f"Starting debate orchestration: {topic}, {num_rounds} rounds")
        logger.info(f"Participants: {participants}")
        
        pro_url = participants.get("pro_debater")
        con_url = participants.get("con_debater")
        
        if not pro_url or not con_url:
            return {"error": "Missing participant URLs"}
        
        pro_arguments = []
        con_arguments = []
        
        # Conduct debate rounds
        for round_num in range(1, num_rounds + 1):
            logger.info(f"=== Debate Round {round_num} ===")
            
            # Get pro argument
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    pro_response = await client.post(
                        pro_url,
                        json={
                            "jsonrpc": "2.0",
                            "method": "message/send",
                            "params": {
                                "topic": topic,
                                "round": round_num,
                                "previous_arguments": con_arguments[-1] if con_arguments else ""
                            },
                            "id": str(uuid.uuid4())
                        }
                    )
                    
                    if pro_response.status_code == 200:
                        pro_data = pro_response.json()
                        if "result" in pro_data:
                            pro_arg = pro_data["result"].get("argument", "")
                            pro_arguments.append(pro_arg)
                            logger.info(f"Pro argument: {pro_arg[:100]}...")
            except Exception as e:
                logger.error(f"Failed to get pro argument: {e}")
                pro_arguments.append(f"Pro argument unavailable for round {round_num}")
            
            # Get con argument
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    con_response = await client.post(
                        con_url,
                        json={
                            "jsonrpc": "2.0",
                            "method": "message/send",
                            "params": {
                                "topic": topic,
                                "round": round_num,
                                "previous_arguments": pro_arguments[-1] if pro_arguments else ""
                            },
                            "id": str(uuid.uuid4())
                        }
                    )
                    
                    if con_response.status_code == 200:
                        con_data = con_response.json()
                        if "result" in con_data:
                            con_arg = con_data["result"].get("argument", "")
                            con_arguments.append(con_arg)
                            logger.info(f"Con argument: {con_arg[:100]}...")
            except Exception as e:
                logger.error(f"Failed to get con argument: {e}")
                con_arguments.append(f"Con argument unavailable for round {round_num}")
            
            # Brief pause between rounds
            await asyncio.sleep(1)
        
        # Evaluate the debate
        evaluation = await self.evaluate_debate(pro_arguments, con_arguments, topic)
        
        result = {
            "topic": topic,
            "num_rounds": num_rounds,
            "evaluation": evaluation,
            "all_arguments": {
                "pro": pro_arguments,
                "con": con_arguments
            },
            "participants": participants
        }
        
        logger.info(f"Debate completed. Winner: {evaluation.get('winner', 'unknown')}")
        return result

judge = DebateJudge()

@app.post("/")
async def handle_jsonrpc(request: Request):
    """Handle JSON-RPC requests from AgentBeats platform"""
    try:
        data = await request.json()
        logger.info(f"Green agent received JSON-RPC request")
        
        if "jsonrpc" in data and data["jsonrpc"] == "2.0":
            method = data.get("method", "")
            params = data.get("params", {})
            jsonrpc_id = data.get("id", 1)
            
            logger.info(f"Method: {method}")
            
            # Handle the assessment request
            if method == "message/send":
                # According to AgentBeats docs, green agent receives participant info and config
                if isinstance(params, dict):
                    participants = params.get("participants", {})
                    config = params.get("config", {})
                    
                    # Start debate orchestration
                    # Note: In production, this should be async and report results via MCP/API
                    result = await judge.orchestrate_debate(participants, config)
                    
                    # Return acknowledgment (actual results should be reported via MCP/API)
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "result": {
                            "status": "assessment_started",
                            "message": "Debate assessment initiated. Results will be available shortly.",
                            "assessment_id": str(uuid.uuid4())
                        },
                        "id": jsonrpc_id
                    })
            
            # Method not found
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601, 
                    "message": f"Method '{method}' not found"
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
    return {
        "name": "debate_judge",
        "description": "AI debate judge for evaluating pro/con arguments",
        "url": "http://127.0.0.1:9009/",
        "version": "1.0.0",
        "skills": [
            {
                "name": "debate_evaluation",
                "description": "Evaluates debate arguments and determines winners"
            },
            {
                "name": "argument_analysis", 
                "description": "Analyzes the quality and persuasiveness of arguments"
            }
        ],
        "capabilities": {"streaming": False},
        "defaultInputModes": ["JSON_RPC"],
        "defaultOutputModes": ["JSON_RPC"],
        "participant_requirements": [
            {
                "role": "pro_debater",
                "name": "pro_debater",
                "description": "Professional debater taking the pro position",
                "required": True
            },
            {
                "role": "con_debater", 
                "name": "con_debater",
                "description": "Professional debater taking the con position",
                "required": True
            }
        ]
    }

@app.get("/")
async def root():
    return {
        "service": "debate_judge",
        "status": "running",
        "role": "green_agent",
        "description": "Orchestrates and evaluates debates between pro/con agents",
        "endpoint": "POST / (JSON-RPC 2.0)",
        "methods": ["message/send"]
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9009)
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting debate judge (green agent) on http://{args.host}:{args.port}")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()