from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response,JSONResponse
from pydantic import BaseModel
from prisma import Prisma
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
    return JSONResponse({"message":"Api is running !!"}, status_code=200)

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post('/signup')
async def signup(request: SignupRequest):
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
                'password': request.password
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
    
    if(auth['password']!=request.password):
        return JSONResponse({"message":"Incorrect credentials"}, status_code=400)
    
    return JSONResponse({"message":"Login successful !!"}, status_code=200)

       

if __name__ == "__main__":
    uvicorn.run("routes:app",port=8000, reload=True)