import mimetypes
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Windows MIME fix — must run before StaticFiles mount
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

app = FastAPI(title="Retailer Launch Cost Model")

# CORS — open in dev, restrict in prod
environment = os.getenv("ENVIRONMENT", "development")
allow_origins = ["*"] if environment == "development" else ["https://cost-of-saying-yes.fly.dev"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API routes will be added here (U2, U4) ---

@app.get("/api/health")
def health():
    return {"status": "ok"}

# StaticFiles MUST be mounted last — it is a catch-all
app.mount("/", StaticFiles(directory="static", html=True), name="static")
