"""Minimal startup — test if Railway can run anything at all."""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
logger = logging.getLogger("start")

port = int(os.environ.get("PORT", "8000"))
logger.info(f"Python {sys.version}")
logger.info(f"PORT={port}")

# Minimal app — no imports from our codebase
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "minimal"}

@app.get("/")
async def root():
    return {"app": "oldnews", "status": "starting"}

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Launching uvicorn on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
