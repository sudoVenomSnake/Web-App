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


class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

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

def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

@app.post("/login")
async def login(user: UserLogin):

    stored_user = await prisma.user.find_first(where={"email": user.email})
    if not stored_user or not verify_password(user.password, stored_user.password):
        return {"message": "Invalid credentials"}
    return {"message": "Logged in successfully"}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


if __name__ == "__main__":
    uvicorn.run("routes:app",port=8000, reload=True)