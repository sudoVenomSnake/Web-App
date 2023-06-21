from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def startup_event():
    await prisma.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await prisma.disconnect()

@app.get("/")
async def root():
    res = Response("Welcome to Api", status_code=200)
    return res

