"""
Bot Control API - Start/Stop/Status endpoints for RiskFusion pipeline
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime
import subprocess
import threading
import os
import signal

router = APIRouter(prefix="/bot", tags=["bot"])

# Global state for bot process
class BotState:
    process: Optional[subprocess.Popen] = None
    status: Literal["stopped", "starting", "running", "stopping", "error"] = "stopped"
    started_at: Optional[datetime] = None
    last_run_output: str = ""
    mode: Literal["paper", "live"] = "paper"
    error_message: Optional[str] = None

bot_state = BotState()
output_lock = threading.Lock()


class BotStatusResponse(BaseModel):
    status: str
    mode: str
    started_at: Optional[str]
    uptime_seconds: Optional[int]
    last_output: str
    error_message: Optional[str]


class StartBotRequest(BaseModel):
    mode: Literal["paper", "live"] = "paper"
    tickers: Optional[list[str]] = None


@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status():
    """Get current bot status"""
    uptime = None
    if bot_state.started_at and bot_state.status == "running":
        uptime = int((datetime.utcnow() - bot_state.started_at).total_seconds())
    
    return BotStatusResponse(
        status=bot_state.status,
        mode=bot_state.mode,
        started_at=bot_state.started_at.isoformat() if bot_state.started_at else None,
        uptime_seconds=uptime,
        last_output=bot_state.last_run_output[-2000:],  # Last 2000 chars
        error_message=bot_state.error_message,
    )


def run_bot_process(mode: str):
    """Background task to run the bot"""
    global bot_state
    
    try:
        # Path to RiskFusion
        riskfusion_path = os.environ.get(
            "RISKFUSION_PATH", 
            r"C:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha"
        )
        
        # Build command (use run_daily)
        cmd = [
            "python", "-u", "-m", "riskfusion.cli", "run_daily"
        ]
        
        # Set execution mode via env var
        env = os.environ.copy()
        env["EXECUTION_MODE"] = mode.upper()  # PAPER or LIVE
        
        bot_state.status = "starting"
        bot_state.started_at = datetime.utcnow()
        bot_state.mode = mode
        bot_state.error_message = None
        bot_state.last_run_output = "--- NEW RUN INITIATED ---\n"
        
        # Start process
        bot_state.process = subprocess.Popen(
            cmd,
            cwd=riskfusion_path,
            env=env,  # Pass modified env
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        bot_state.status = "running"
        
        # Read output
        for line in bot_state.process.stdout:
            print(f"BOT LOG: {line.strip()}") # Debug to API console
            with output_lock:
                bot_state.last_run_output += line
                # Keep reasonably sized
                if len(bot_state.last_run_output) > 50000:
                   bot_state.last_run_output = bot_state.last_run_output[-50000:]
        
        # Process finished
        returncode = bot_state.process.wait()
        if returncode != 0:
            bot_state.status = "error"
            bot_state.error_message = f"Process exited with code {returncode}"
        else:
            bot_state.status = "stopped"
            
    except Exception as e:
        bot_state.status = "error"
        bot_state.error_message = str(e)
    finally:
        bot_state.process = None


@router.post("/start")
async def start_bot(request: StartBotRequest, background_tasks: BackgroundTasks):
    """Start the RiskFusion bot"""
    if bot_state.status in ["running", "starting"]:
        raise HTTPException(status_code=400, detail="Bot is already running")
    
    if request.mode == "live":
        # Extra safety check for live mode
        if not os.environ.get("ALLOW_LIVE_TRADING"):
            raise HTTPException(
                status_code=403, 
                detail="Live trading not enabled. Set ALLOW_LIVE_TRADING=1"
            )
    
    # Start bot in background
    background_tasks.add_task(run_bot_process, request.mode)
    
    return {
        "message": f"Bot starting in {request.mode} mode",
        "status": "starting",
    }


@router.post("/stop")
async def stop_bot():
    """Stop the running bot"""
    if bot_state.status not in ["running", "starting"]:
        raise HTTPException(status_code=400, detail="Bot is not running")
    
    bot_state.status = "stopping"
    
    if bot_state.process:
        try:
            # Try graceful shutdown first
            bot_state.process.terminate()
            try:
                bot_state.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill
                bot_state.process.kill()
        except Exception as e:
            bot_state.error_message = f"Error stopping: {e}"
    
    bot_state.status = "stopped"
    bot_state.process = None
    
    return {"message": "Bot stopped", "status": "stopped"}


@router.post("/run-once")
async def run_once(request: StartBotRequest, background_tasks: BackgroundTasks):
    """Run a single pipeline iteration (non-continuous)"""
    if bot_state.status in ["running", "starting"]:
        raise HTTPException(status_code=400, detail="Bot is already running")
    
    # For single run, we just execute the pipeline once
    background_tasks.add_task(run_bot_process, request.mode)
    
    return {
        "message": f"Running single pipeline in {request.mode} mode",
        "status": "starting",
    }
