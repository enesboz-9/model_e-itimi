"""Vercel CLI olmadan yerelde denemek için:  pip install uvicorn fastapi numpy xgboost-cpu httpx && python yerel.py
Sonra http://localhost:8000 adresini açın."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))
from fastapi.staticfiles import StaticFiles
from index import app

app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "public"), html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", 8000)))
