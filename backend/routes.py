import time
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from prisma import Prisma
import uvicorn
import jwt
import os
from passlib.context import CryptContext


prisma = Prisma()
app = FastAPI()

JWT_SECRET = os.getenv("JWT_secret")   
JWT_ALGORITHM = os.getenv("JWT_algorithm")   

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid: bool = False

        try:
            payload = decodeJWT(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

pwd_context = CryptContext(schemes=[os.getenv("encryption_algorithm")], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

@app.on_event("startup")
async def startup_event():
    await prisma.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await prisma.disconnect()

def signJWT(user_id: str):
    payload = {
        "user_id": user_id,
        "expires": time.time() + 600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token

def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}

@app.get("/")
async def root():
    return JSONResponse({"message":"Api is running !!"}, status_code=200)

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
    
    TokenToSend = signJWT(request.email)
    
    return JSONResponse({"message":"Login successful !!","access_token":TokenToSend}, status_code=200)

@app.get('/protected', dependencies=[Depends(JWTBearer())])
async def protected():
    return JSONResponse({"message":"Only logged in user can see me"}, status_code=200)


if __name__ == "__main__":
    uvicorn.run("routes:app",port=8000, reload=True)
