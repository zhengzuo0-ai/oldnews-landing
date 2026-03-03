"""Startup wrapper with error handling and logging."""
import sys
import os
import logging
import traceback

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("startup")

port = int(os.environ.get("PORT", "8000"))
logger.info(f"Python {sys.version}")
logger.info(f"Starting on port {port}")
logger.info(f"Environment vars: {[k for k in os.environ.keys()]}")

try:
    logger.info("Importing main...")
    from main import app
    logger.info("Import OK, launching uvicorn...")
except Exception as e:
    logger.error(f"Import failed: {e}")
    traceback.print_exc()
    # Create minimal fallback app
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/health")
    async def health():
        return {"status": "error", "detail": str(e)}
    logger.info("Fallback app created")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
