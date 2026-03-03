"""OldNews startup wrapper with error handling."""
import os
import sys
import logging
import traceback

logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
logger = logging.getLogger("start")

port = int(os.environ.get("PORT", "8000"))
logger.info(f"Python {sys.version}")
logger.info(f"PORT={port}")

try:
    logger.info("Importing main app...")
    from main import app
    logger.info("Main app imported successfully")
except Exception as e:
    logger.error(f"Failed to import main app: {e}")
    traceback.print_exc()
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/health")
    async def health():
        return {"status": "degraded", "error": str(e)}
    @app.get("/")
    async def root():
        return {"status": "degraded", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Launching uvicorn on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
