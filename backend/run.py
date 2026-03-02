from dotenv import load_dotenv
load_dotenv()
import uvicorn
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
