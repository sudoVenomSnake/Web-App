from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from prisma import Prisma

prisma = Prisma()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
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
    res = Response("Api is up and running!!", status_code=200)
    return res

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str

@app.post('/signup')
async def signup(request: SignupRequest):
    _user = prisma.user.create(
        data={
            'name': request.name,
            'email': request.email,
            'password': request.password
        }
    )
    res = Response("Signup Successful", status_code=201)
    return res

