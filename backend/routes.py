from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prisma import Prisma
from passlib.context import CryptContext
from pydantic import BaseModel
import jwt
import uvicorn

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

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

@app.post('/signup')
async def signup(user: UserCreate):
    hashed_password = get_password_hash(user.password)
    try:
        created_user =await prisma.user.create(
            data={
                'name': user.name,
                'email': user.email,
                'password': hashed_password
            }
        )
    except Exception as e:
        return Response(e, status_code=500)
          
    res = Response("Signup Successful", status_code=201)
    return res

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str):
    return pwd_context.hash(password)

if __name__ == "__main__":
    uvicorn.run("routes:app",port=8000, reload=True)