from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
import gridfs
from pymongo import MongoClient
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# GridFS for file storage
sync_client = MongoClient(mongo_url)
sync_db = sync_client[os.environ['DB_NAME']]
fs = gridfs.GridFS(sync_db)

# JWT settings
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-this')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    company: Optional[str] = None
    role: str = "client"  # client or admin
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: float
    description: Optional[str] = None
    is_active: bool = True

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    service_id: str
    service_name: str
    price: float
    status: str = "pending"  # pending, processing, completed, delivered
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    file_id: Optional[str] = None
    original_filename: Optional[str] = None

class OrderCreate(BaseModel):
    service_id: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Initialize default services
DEFAULT_SERVICES = [
    {"name": "Stage 1", "price": 70.0, "description": "Optimisation Stage 1"},
    {"name": "Stage 2", "price": 90.0, "description": "Optimisation Stage 2"},
    {"name": "Stage 3", "price": 200.0, "description": "Optimisation Stage 3"},
    {"name": "Solution EGR", "price": 20.0, "description": "Suppression EGR"},
    {"name": "Solution FAP", "price": 20.0, "description": "Suppression FAP"},
    {"name": "Solution AdBlue", "price": 30.0, "description": "Suppression AdBlue"},
    {"name": "Flexfuel", "price": 70.0, "description": "Conversion Flexfuel"},
    {"name": "Stage 1 + Flexfuel", "price": 130.0, "description": "Stage 1 + Flexfuel combiné"},
]

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Initialize database
async def init_db():
    # Create admin user if not exists
    admin_exists = await db.users.find_one({"email": "admin@cartomapping.com"})
    if not admin_exists:
        admin_user = User(
            email="admin@cartomapping.com",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        admin_dict = admin_user.dict()
        admin_dict["password"] = hash_password("admin123")
        await db.users.insert_one(admin_dict)
    
    # Create default services
    for service_data in DEFAULT_SERVICES:
        existing_service = await db.services.find_one({"name": service_data["name"]})
        if not existing_service:
            service = Service(**service_data)
            await db.services.insert_one(service.dict())

# Routes
@api_router.post("/auth/register", response_model=User)
async def register(user: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    new_user = User(**user_dict)
    await db.users.insert_one(new_user.dict())
    
    return new_user

@api_router.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    # Find user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user["id"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/services", response_model=List[Service])
async def get_services():
    services = await db.services.find({"is_active": True}).to_list(1000)
    return [Service(**service) for service in services]

@api_router.post("/orders", response_model=Order)
async def create_order(order: OrderCreate, current_user: User = Depends(get_current_user)):
    # Get service details
    service = await db.services.find_one({"id": order.service_id})
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Create order
    new_order = Order(
        user_id=current_user.id,
        service_id=service["id"],
        service_name=service["name"],
        price=service["price"]
    )
    await db.orders.insert_one(new_order.dict())
    
    return new_order

@api_router.get("/orders", response_model=List[Order])
async def get_user_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find({"user_id": current_user.id}).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.post("/orders/{order_id}/upload")
async def upload_file(order_id: str, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    # Check if order exists and belongs to user
    order = await db.orders.find_one({"id": order_id, "user_id": current_user.id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check file size (10MB limit)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10MB"
        )
    
    # Store file in GridFS
    file_id = fs.put(file_content, filename=file.filename, content_type=file.content_type)
    
    # Update order with file info
    await db.orders.update_one(
        {"id": order_id},
        {
            "$set": {
                "file_id": str(file_id),
                "original_filename": file.filename,
                "status": "processing"
            }
        }
    )
    
    return {"message": "File uploaded successfully", "file_id": str(file_id)}

@api_router.get("/orders/{order_id}/download")
async def download_file(order_id: str, current_user: User = Depends(get_current_user)):
    # Check if order exists and belongs to user
    order = await db.orders.find_one({"id": order_id, "user_id": current_user.id})
    if not order or not order.get("file_id"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Get file from GridFS
    try:
        file_doc = fs.get(order["file_id"])
        file_stream = io.BytesIO(file_doc.read())
        
        return StreamingResponse(
            io.BytesIO(file_stream.getvalue()),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={order['original_filename']}"}
        )
    except gridfs.errors.NoFile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage"
        )

# Admin routes
@api_router.get("/admin/users", response_model=List[User])
async def get_all_users(admin_user: User = Depends(get_admin_user)):
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.get("/admin/orders", response_model=List[Order])
async def get_all_orders(admin_user: User = Depends(get_admin_user)):
    orders = await db.orders.find().to_list(1000)
    return [Order(**order) for order in orders]

@api_router.put("/admin/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, admin_user: User = Depends(get_admin_user)):
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": {"status": status, "completed_at": datetime.utcnow() if status == "completed" else None}}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return {"message": "Order status updated"}

@api_router.post("/admin/services", response_model=Service)
async def create_service(service: Service, admin_user: User = Depends(get_admin_user)):
    await db.services.insert_one(service.dict())
    return service

@api_router.put("/admin/services/{service_id}")
async def update_service(service_id: str, service: Service, admin_user: User = Depends(get_admin_user)):
    result = await db.services.update_one(
        {"id": service_id},
        {"$set": service.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return {"message": "Service updated"}

@api_router.delete("/admin/services/{service_id}")
async def delete_service(service_id: str, admin_user: User = Depends(get_admin_user)):
    result = await db.services.delete_one({"id": service_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return {"message": "Service deleted"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()