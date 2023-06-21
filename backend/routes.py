from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response,JSONResponse
from pydantic import BaseModel
from prisma import Prisma
import uvicorn
from passlib.context import CryptContext

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
    return JSONResponse({"message":"Api is running !!"}, status_code=200)

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

@app.post('/signup')
async def signup(request: SignupRequest):
    hashed_password = get_password_hash(request.password)
    check = await prisma.user.find_unique(
        where={
            'email': request.email
        }
    )
    if check is not None:
        return JSONResponse({"message": "User already exists"}, status_code=400)
    
    try:
        user = await prisma.user.create(
            data={
                'name': request.name,
                'email': request.email,
                'password': hashed_password
            }
        )
        return JSONResponse({"message":"Signup Successful"}, status_code=201)
    except Exception as e: 
        return JSONResponse({"message":e}, status_code=500)
    
@app.post('/login')
async def login(request: LoginRequest):
    auth = await prisma.user.find_unique(
        where={
            'email': request.email,
        }
    )

    if auth is None: 
       return JSONResponse({"message":"Account not present please signup"}, status_code=400)
    
    if not verify_password(request.password, auth.password):
        return JSONResponse({"message":"Incorrect credentials"}, status_code=400)
    
    return JSONResponse({"message":"Login successful !!"}, status_code=200)


