import argparse
import uvicorn
import logging
import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Load env
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG)  # DEBUG level for more info
logger = logging.getLogger("debug_debater")

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    logger.info(f"→ {request.method} {request.url}")
    logger.info(f"  Headers: {dict(request.headers)}")
    
    try:
        body = await request.body()
        if body:
            logger.info(f"  Body: {body.decode()}")
    except:
        pass
    
    response = await call_next(request)
    
    logger.info(f"← {response.status_code}")
    return response

@app.post("/")
async def handle_jsonrpc(request: Request):
    """Handle JSON-RPC and plain JSON"""
    try:
        # Try to parse body
        body_bytes = await request.body()
        body_str = body_bytes.decode()
        logger.info(f"Raw body: {body_str}")
        
        # Try to parse as JSON
        try:
            data = json.loads(body_str)
        except json.JSONDecodeError:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error - not valid JSON"},
                "id": None
            })
        
        logger.info(f"Parsed JSON: {json.dumps(data, indent=2)}")
        
        # Check if it's JSON-RPC
        is_jsonrpc = data.get("jsonrpc") == "2.0"
        
        if is_jsonrpc:
            method = data.get("method", "")
            params = data.get("params", {})
            jsonrpc_id = data.get("id", 1)
            
            logger.info(f"JSON-RPC: method={method}, id={jsonrpc_id}")
            
            if method == "execute":
                # Extract message
                message = ""
                if isinstance(params, dict):
                    message = params.get("message", "")
                    if not message and "data" in params:
                        message = params["data"].get("message", "")
                elif isinstance(params, str):
                    message = params
                
                logger.info(f"Extracted message: {message}")
                
                # Simple response
                response_text = f"DEBUG: I received '{message[:50]}...' as {method}"
                
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "result": {
                        "response": response_text,
                        "status": "success"
                    },
                    "id": jsonrpc_id
                })
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method '{method}' not found"},
                    "id": jsonrpc_id
                })
        else:
            # Plain JSON
            message = data.get("message", "")
            logger.info(f"Plain JSON message: {message}")
            
            return JSONResponse({
                "response": f"DEBUG: Plain message received: '{message}'",
                "status": "success"
            })
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": None
        }, status_code=500)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "debug_debater"}

@app.get("/")
async def root():
    return {
        "service": "debug_debater",
        "status": "running",
        "endpoints": {
            "POST /": "Handle JSON-RPC or plain JSON",
            "GET /health": "Health check"
        }
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9019)
    parser.add_argument("--role", default="debug")
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting debug debater on http://{args.host}:{args.port}")
    logger.info(f"📡 Listening for JSON-RPC and plain JSON requests")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()