from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exception_handlers import http_exception_handler
from jose import JWTError
from bson import ObjectId
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

# Helper function to add CORS headers
def add_cors_headers(response: Response):
    """Add CORS headers to any response"""
    response.headers["Access-Control-Allow-Origin"] = "https://a3dcf5d2-f7d5-441b-b7fd-c28745e3f454.preview.emergentagent.com"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Custom exception handler for CORS
async def cors_exception_handler(request, exc):
    """Handle HTTPException with CORS headers"""
    response = await http_exception_handler(request, exc)
    
    # Add CORS headers to error responses
    response.headers["Access-Control-Allow-Origin"] = "https://a3dcf5d2-f7d5-441b-b7fd-c28745e3f454.preview.emergentagent.com"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Security
security = HTTPBearer()

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str  # Required
    country: str  # Required
    company: Optional[str] = None
    role: str = "client"

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    company: Optional[str] = None
    is_active: Optional[bool] = None
    discount_percentage: Optional[float] = None
    email: Optional[EmailStr] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    country: str
    company: Optional[str] = None
    role: str = "client"  # client or admin
    discount_percentage: float = 0.0  # 0 to 30% discount
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class ServiceCreate(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    is_active: bool = True

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: float
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FileVersion(BaseModel):
    file_id: str
    filename: str
    version_type: str  # "original", "v1", "v2", "v3", "sav"
    uploaded_by: str  # user_id
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: Optional[str] = None
    user_id: str
    service_id: str
    service_name: str
    price: float
    status: str = "pending"  # pending, processing, completed, cancelled
    payment_status: str = "unpaid"  # paid, unpaid
    immatriculation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    client_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    files: List[FileVersion] = []

class OrderCreate(BaseModel):
    service_id: str

class OrderStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None

class PaymentStatusUpdate(BaseModel):
    payment_status: str  # paid, unpaid

class UserStatusUpdate(BaseModel):
    is_active: bool

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "new_order", "sav_request", "file_uploaded"
    title: str
    message: str
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # The client user this message thread belongs to
    sender_id: str
    sender_role: str  # "admin" or "client"
    message: str
    is_read: bool = False
    file_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Token(BaseModel):
    access_token: str
    token_type: str

# Initialize default services
DEFAULT_SERVICES = [
    {"name": "Stage 1", "price": 150.0, "description": "Optimisation cartographie Stage 1"},
    {"name": "Stage 1 + EGR", "price": 200.0, "description": "Stage 1 avec suppression EGR"},
    {"name": "Stage 2", "price": 250.0, "description": "Optimisation cartographie Stage 2"},
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

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        user = await db.users.find_one({"id": user_id})
        if user is None:
            return None
        return User(**user)
    except (jwt.PyJWTError, Exception):
        return None

# Initialize database
async def init_db():
    # Create admin user if not exists
    admin_exists = await db.users.find_one({"email": "admin@test.com"})
    if not admin_exists:
        admin_user = User(
            email="admin@test.com",
            first_name="Admin",
            last_name="DMR",
            phone="0000000000",
            country="France",
            role="admin"
        )
        admin_dict = admin_user.dict()
        admin_dict["password"] = hash_password("admin123")
        await db.users.insert_one(admin_dict)
    
    # Create default services if not exist (only 3 services)
    services_count = await db.services.count_documents({})
    if services_count == 0:
        for service_data in DEFAULT_SERVICES:
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
    # Store user with password in database
    user_db_dict = new_user.dict()
    user_db_dict["password"] = user_dict["password"]
    await db.users.insert_one(user_db_dict)
    
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
    
    # Check if user is active
    if not db_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
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
    
    # Generate order number
    new_order.order_number = f"DMR-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    await db.orders.insert_one(new_order.dict())
    
    return new_order

@api_router.post("/orders/combined", response_model=Order)
async def create_combined_order(
    service_name: str = Form(...),
    price: float = Form(...),
    combined_services: str = Form(...),  # JSON string of services
    current_user: User = Depends(get_current_user)
):
    import json
    
    # Parse combined services
    try:
        services_list = json.loads(combined_services)
    except:
        services_list = []
    
    # Create combined order
    new_order = Order(
        user_id=current_user.id,
        service_id="combined",
        service_name=service_name,
        price=price
    )
    
    # Generate order number
    new_order.order_number = f"DMR-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    # Add combined services info to order
    order_dict = new_order.dict()
    order_dict["combined_services"] = services_list
    
    await db.orders.insert_one(order_dict)
    
    # Create notification for new order
    notification = Notification(
        type="new_order",
        title="Nouvelle commande",
        message=f"Nouvelle commande de {current_user.first_name} {current_user.last_name}: {service_name}",
        order_id=new_order.id,
        user_id=current_user.id
    )
    
    await db.notifications.insert_one(notification.dict())
    
    return new_order

@api_router.get("/orders", response_model=List[Order])
async def get_user_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find({"user_id": current_user.id}).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.post("/orders/{order_id}/upload")
async def upload_file(
    order_id: str, 
    file: UploadFile = File(...), 
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
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
    
    # Create file version
    file_version = FileVersion(
        file_id=str(file_id),
        filename=file.filename,
        version_type="original",
        uploaded_by=current_user.id,
        notes=notes
    )
    
    # Extract immatriculation from notes
    immatriculation = None
    if notes:
        # Look for immatriculation pattern in notes
        import re
        # Pattern to find "Immatriculation: XX-XXX-XX" or similar
        immat_match = re.search(r'Immatriculation[:\s]*([A-Z0-9\-]+)', notes, re.IGNORECASE)
        if immat_match:
            immatriculation = immat_match.group(1)
    
    # Update order with file info, notes, and immatriculation
    update_data = {
        "client_notes": notes,
        "status": "processing"
    }
    if immatriculation:
        update_data["immatriculation"] = immatriculation
    
    await db.orders.update_one(
        {"id": order_id},
        {
            "$set": update_data,
            "$push": {
                "files": file_version.dict()
            }
        }
    )
    
    return {
        "message": "File uploaded successfully", 
        "file_id": str(file_id),
        "notes": notes
    }

@api_router.get("/orders/{order_id}/download/{file_id}")
async def download_file(
    order_id: str, 
    file_id: str,
    response: Response,
    token: Optional[str] = Query(None),  # Allow token in query params for direct links
    current_user: User = Depends(get_current_user_optional)  # Make user optional for query token
):
    # Add CORS headers to response
    add_cors_headers(response)
    
    # If no user from header and token in query, try to decode token
    if not current_user and token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                user_doc = await db.users.find_one({"id": user_id})
                if user_doc:
                    current_user = User(**user_doc)
        except JWTError:
            pass
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check if order belongs to user
    order = await db.orders.find_one({"id": order_id, "user_id": current_user.id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    try:
        # Get file from GridFS
        file_data = fs.get(ObjectId(file_id))
        
        # Get filename from order files
        filename = "download.bin"
        if "files" in order:
            for file_info in order["files"]:
                if file_info.get("file_id") == file_id:
                    filename = file_info.get("filename", "download.bin")
                    break
        
        return StreamingResponse(
            io.BytesIO(file_data.read()),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Allow-Origin": "https://a3dcf5d2-f7d5-441b-b7fd-c28745e3f454.preview.emergentagent.com",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

# Admin routes
@api_router.get("/admin/users", response_model=List[User])
async def get_all_users(admin_user: User = Depends(get_admin_user)):
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.post("/admin/users", response_model=User)
async def create_user(user: UserCreate, admin_user: User = Depends(get_admin_user)):
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
    user_db_dict = new_user.dict()
    user_db_dict["password"] = user_dict["password"]
    await db.users.insert_one(user_db_dict)
    
    return new_user

@api_router.put("/admin/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, admin_user: User = Depends(get_admin_user)):
    # Find user
    existing_user = await db.users.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prepare update data
    update_data = {}
    for key, value in user_update.dict(exclude_unset=True).items():
        if value is not None:
            update_data[key] = value
    
    if update_data:
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
    
    # Return updated user
    updated_user = await db.users.find_one({"id": user_id})
    return User(**updated_user)

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin_user: User = Depends(get_admin_user)):
    # Check if user exists
    existing_user = await db.users.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting admin user
    if existing_user.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin user"
        )
    
    # Delete user
    await db.users.delete_one({"id": user_id})
    return {"message": "User deleted successfully"}

@api_router.get("/admin/orders", response_model=List[Order])
async def get_all_orders(admin_user: User = Depends(get_admin_user)):
    orders = await db.orders.find().to_list(1000)
    return [Order(**order) for order in orders]

@api_router.put("/admin/orders/{order_id}/status")
async def update_order_status(
    order_id: str, 
    status_update: OrderStatusUpdate, 
    admin_user: User = Depends(get_admin_user)
):
    update_data = {
        "status": status_update.status,
        "completed_at": datetime.utcnow() if status_update.status == "completed" else None
    }
    
    if status_update.admin_notes:
        update_data["admin_notes"] = status_update.admin_notes
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return {"message": "Order status updated"}

@api_router.put("/admin/orders/{order_id}/price")
async def update_order_price(
    order_id: str,
    price_data: dict,
    admin_user: User = Depends(get_admin_user)
):
    price = price_data.get("price")
    if price is None or price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid price is required"
        )
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": {"price": float(price)}}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return {"message": "Order price updated"}

@api_router.get("/admin/orders/{order_id}/download/{file_id}")
async def admin_download_file(
    order_id: str, 
    file_id: str,
    response: Response,
    admin_user: User = Depends(get_admin_user)
):
    # Add CORS headers to response
    add_cors_headers(response)
    
    # Check if order exists
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    try:
        # Get file from GridFS
        file_data = fs.get(ObjectId(file_id))
        
        # Get filename from order files
        filename = "download.bin"
        if "files" in order:
            for file_info in order["files"]:
                if file_info.get("file_id") == file_id:
                    filename = file_info.get("filename", "download.bin")
                    break
        
        return StreamingResponse(
            io.BytesIO(file_data.read()),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Allow-Origin": "https://a3dcf5d2-f7d5-441b-b7fd-c28745e3f454.preview.emergentagent.com",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

@api_router.post("/admin/orders/{order_id}/upload")
async def admin_upload_file(
    order_id: str,
    file: UploadFile = File(...),
    version_type: str = Form("v1"),  # v1, v2, v3, sav
    notes: Optional[str] = Form(None),
    admin_user: User = Depends(get_admin_user)
):
    # Check if order exists
    order = await db.orders.find_one({"id": order_id})
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
    
    # Create file version
    file_version = FileVersion(
        file_id=str(file_id),
        filename=file.filename,
        version_type=version_type,
        uploaded_by=admin_user.id,
        notes=notes
    )
    
    # Update order with new file version
    await db.orders.update_one(
        {"id": order_id},
        {
            "$push": {
                "files": file_version.dict()
            },
            "$set": {
                "status": "completed" if version_type in ["v1", "v2", "v3"] else "processing"
            }
        }
    )
    
    # Create notification for CLIENT ONLY about new file
    immatriculation = order.get("immatriculation", "")
    service_info = f"{immatriculation} - {order.get('service_name', '')}" if immatriculation else order.get('service_name', '')
    
    version_text = "Nouvelle version" if version_type in ["v1", "v2", "v3"] else "SAV"
    notification = Notification(
        type="new_file",
        title="Nouveau fichier disponible",
        message=f"{version_text} disponible pour {service_info}",
        order_id=order_id,
        user_id=order.get("user_id")  # ONLY for the client, not admin
    )
    
    await db.notifications.insert_one(notification.dict())
    
    return {
        "message": "File uploaded successfully", 
        "file_id": str(file_id),
        "version_type": version_type,
        "notes": notes
    }

# Service management routes
@api_router.get("/admin/services", response_model=List[Service])
async def get_all_services(admin_user: User = Depends(get_admin_user)):
    services = await db.services.find().to_list(1000)
    return [Service(**service) for service in services]

@api_router.post("/admin/services", response_model=Service)
async def create_service(service: ServiceCreate, admin_user: User = Depends(get_admin_user)):
    new_service = Service(**service.dict())
    await db.services.insert_one(new_service.dict())
    return new_service

@api_router.put("/admin/services/{service_id}", response_model=Service)
async def update_service(service_id: str, service_update: ServiceUpdate, admin_user: User = Depends(get_admin_user)):
    # Find service
    existing_service = await db.services.find_one({"id": service_id})
    if not existing_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Prepare update data
    update_data = {}
    for key, value in service_update.dict(exclude_unset=True).items():
        if value is not None:
            update_data[key] = value
    
    if update_data:
        await db.services.update_one(
            {"id": service_id},
            {"$set": update_data}
        )
    
    # Return updated service
    updated_service = await db.services.find_one({"id": service_id})
    return Service(**updated_service)

@api_router.delete("/admin/services/{service_id}")
async def delete_service(service_id: str, admin_user: User = Depends(get_admin_user)):
    result = await db.services.delete_one({"id": service_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return {"message": "Service deleted"}

# New Admin Endpoints for enhanced functionality

@api_router.put("/admin/orders/{order_id}/payment")
async def update_order_payment_status(
    order_id: str,
    payment_update: PaymentStatusUpdate,
    admin_user: User = Depends(get_admin_user)
):
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": {"payment_status": payment_update.payment_status}}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return {"message": "Payment status updated"}

@api_router.put("/admin/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    admin_user: User = Depends(get_admin_user)
):
    update_data = {
        "status": "cancelled",
        "cancelled_at": datetime.utcnow(),
        "price": 0.0  # Set price to 0 when cancelled
    }
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return {"message": "Order cancelled"}

@api_router.get("/admin/orders/by-client")
async def get_orders_by_client(admin_user: User = Depends(get_admin_user)):
    # Get all orders and group by user
    orders = await db.orders.find({}).to_list(1000)
    users = await db.users.find({}).to_list(1000)
    
    # Create user lookup
    user_lookup = {user["id"]: user for user in users}
    
    # Group orders by user
    orders_by_client = {}
    for order in orders:
        user_id = order["user_id"]
        if user_id not in orders_by_client:
            user_info = user_lookup.get(user_id, {})
            orders_by_client[user_id] = {
                "user": {
                    "id": user_id,
                    "email": user_info.get("email", "Unknown"),
                    "first_name": user_info.get("first_name", ""),
                    "last_name": user_info.get("last_name", ""),
                    "is_active": user_info.get("is_active", True)
                },
                "orders": [],
                "total_unpaid": 0.0
            }
        
        # Calculate unpaid total
        if order.get("payment_status", "unpaid") == "unpaid" and order.get("status") != "cancelled":
            orders_by_client[user_id]["total_unpaid"] += order.get("price", 0.0)
        
        orders_by_client[user_id]["orders"].append(Order(**order))
    
    return list(orders_by_client.values())

@api_router.get("/admin/orders/pending")
async def get_pending_orders(admin_user: User = Depends(get_admin_user)):
    # Get all orders that are not completed or cancelled
    orders = await db.orders.find({
        "status": {"$nin": ["completed", "cancelled"]}
    }).to_list(1000)
    
    users = await db.users.find({}).to_list(1000)
    user_lookup = {user["id"]: user for user in users}
    
    # Add user info to orders
    enriched_orders = []
    for order in orders:
        user_info = user_lookup.get(order["user_id"], {})
        order_data = Order(**order)
        order_dict = order_data.dict()
        order_dict["user"] = {
            "id": order["user_id"],
            "email": user_info.get("email", "Unknown"),
            "first_name": user_info.get("first_name", ""),
            "last_name": user_info.get("last_name", ""),
            "is_active": user_info.get("is_active", True)
        }
        enriched_orders.append(order_dict)
    
    # Sort by created_at descending (newest first)
    enriched_orders.sort(key=lambda x: x["created_at"], reverse=True)
    
    return enriched_orders

@api_router.put("/admin/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    status_update: UserStatusUpdate,
    admin_user: User = Depends(get_admin_user)
):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": status_update.is_active}}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User status updated"}

@api_router.get("/client/balance")
async def get_client_balance(current_user: User = Depends(get_current_user)):
    # Calculate unpaid orders total for current user
    orders = await db.orders.find({
        "user_id": current_user.id,
        "payment_status": "unpaid",
        "status": {"$ne": "cancelled"}
    }).to_list(1000)
    
    total_unpaid = sum(order.get("price", 0.0) for order in orders)
    return {"balance": total_unpaid}

@api_router.post("/orders/{order_id}/sav-request")
async def create_sav_request(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check if order exists and belongs to user
    order = await db.orders.find_one({"id": order_id, "user_id": current_user.id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Create notification for ADMIN ONLY with immatriculation if available
    immatriculation = order.get("immatriculation", "")
    service_info = f"{immatriculation} - {order.get('service_name', '')}" if immatriculation else order.get('service_name', '')
    
    # NOTE: This creates a notification WITHOUT user_id, so it's for admins only
    notification = Notification(
        type="sav_request",
        title="Nouvelle demande de SAV",
        message=f"Demande de SAV pour {service_info} de {current_user.first_name} {current_user.last_name}",
        order_id=order_id
        # NO user_id = notification for admins only
    )
    
    await db.notifications.insert_one(notification.dict())
    
    return {"message": "Demande de SAV créée avec succès"}

@api_router.get("/admin/notifications")
async def get_admin_notifications(admin_user: User = Depends(get_admin_user)):
    notifications = await db.notifications.find({}).sort("created_at", -1).to_list(50)
    return [Notification(**notif) for notif in notifications]

@api_router.put("/admin/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    admin_user: User = Depends(get_admin_user)
):
    await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"is_read": True}}
    )
    return {"message": "Notification marked as read"}

@api_router.delete("/admin/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    admin_user: User = Depends(get_admin_user)
):
    result = await db.notifications.delete_one({"id": notification_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return {"message": "Notification deleted"}

@api_router.delete("/admin/notifications")
async def delete_all_notifications(
    admin_user: User = Depends(get_admin_user)
):
    # Admin can delete ALL notifications (not just their own)
    result = await db.notifications.delete_many({})
    return {"message": f"Deleted {result.deleted_count} notifications"}

# Chat endpoints
@api_router.get("/admin/chat/conversations")
async def get_admin_conversations(admin_user: User = Depends(get_admin_user)):
    # Get all client users
    users = await db.users.find({"role": "client"}).to_list(1000)
    
    # Get all messages to find last messages and unread counts
    messages = await db.messages.find({}).to_list(1000)
    
    # Create conversations for all clients
    conversations = {}
    for user in users:
        user_id = user["id"]
        conversations[user_id] = {
            "user": {
                "id": user_id,
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "email": user.get("email", "")
            },
            "last_message": None,
            "unread_count": 0
        }
    
    # Update with message data
    for message in messages:
        user_id = message.get("user_id")
        if user_id in conversations:
            # Convert message to serializable format
            message_data = {
                "id": message.get("id"),
                "user_id": message.get("user_id"),
                "sender_id": message.get("sender_id"),
                "sender_role": message.get("sender_role"),
                "message": message.get("message"),
                "is_read": message.get("is_read", False),
                "created_at": message.get("created_at")
            }
            
            # Update last message if this one is newer
            current_last = conversations[user_id]["last_message"]
            if (current_last is None or 
                message.get("created_at", datetime.min) > current_last.get("created_at", datetime.min)):
                conversations[user_id]["last_message"] = message_data
            
            # Count unread messages from client
            if not message.get("is_read", False) and message.get("sender_role") == "client":
                conversations[user_id]["unread_count"] += 1
    
    # Sort by last message time (most recent first), then by name
    conversation_list = list(conversations.values())
    conversation_list.sort(key=lambda x: (
        x["last_message"]["created_at"] if x["last_message"] else datetime.min,
        x["user"]["first_name"]
    ), reverse=True)
    
    return conversation_list

@api_router.get("/admin/chat/{user_id}/messages")
async def get_chat_messages(user_id: str, admin_user: User = Depends(get_admin_user)):
    messages = await db.messages.find({"user_id": user_id}).sort("created_at", 1).to_list(1000)
    
    # Mark admin messages as read
    await db.messages.update_many(
        {"user_id": user_id, "sender_role": "client"},
        {"$set": {"is_read": True}}
    )
    
    return [Message(**msg) for msg in messages]

@api_router.post("/admin/chat/{user_id}/messages")
async def send_admin_message(
    user_id: str,
    message_data: dict,
    admin_user: User = Depends(get_admin_user)
):
    message = Message(
        user_id=user_id,
        sender_id=admin_user.id,
        sender_role="admin",
        message=message_data.get("message", "")
    )
    
    await db.messages.insert_one(message.dict())
    return message

@api_router.get("/client/chat/messages")
async def get_client_messages(current_user: User = Depends(get_current_user)):
    messages = await db.messages.find({"user_id": current_user.id}).sort("created_at", 1).to_list(1000)
    
    # Mark admin messages as read
    await db.messages.update_many(
        {"user_id": current_user.id, "sender_role": "admin"},
        {"$set": {"is_read": True}}
    )
    
    return [Message(**msg) for msg in messages]

@api_router.post("/client/chat/messages")
async def send_client_message(
    message_data: dict,
    current_user: User = Depends(get_current_user)
):
    message = Message(
        user_id=current_user.id,
        sender_id=current_user.id,
        sender_role="client",
        message=message_data.get("message", "")
    )
    
    await db.messages.insert_one(message.dict())
    
    # Create notification for admin about new message
    notification = Notification(
        type="new_message",
        title="Nouveau message",
        message=f"Nouveau message de {current_user.first_name} {current_user.last_name}: {message_data.get('message', '')[:50]}...",
        user_id=current_user.id
    )
    
    await db.notifications.insert_one(notification.dict())
    
    return message

@api_router.get("/client/chat/unread-count")
async def get_client_unread_count(current_user: User = Depends(get_current_user)):
    count = await db.messages.count_documents({
        "user_id": current_user.id,
        "sender_role": "admin",
        "is_read": False
    })
    return {"unread_count": count}

@api_router.get("/client/notifications")
async def get_client_notifications(current_user: User = Depends(get_current_user)):
    notifications = await db.notifications.find({
        "user_id": current_user.id
    }).sort("created_at", -1).to_list(50)
    return [Notification(**notif) for notif in notifications]

@api_router.delete("/client/notifications/{notification_id}")
async def delete_client_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    result = await db.notifications.delete_one({
        "id": notification_id, 
        "user_id": current_user.id
    })
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return {"message": "Notification deleted"}

@api_router.delete("/client/notifications")
async def delete_all_client_notifications(
    current_user: User = Depends(get_current_user)
):
    result = await db.notifications.delete_many({
        "user_id": current_user.id
    })
    return {"message": f"Deleted {result.deleted_count} notifications"}

# Include the router in the main app
app.include_router(api_router)

# Add custom exception handler for CORS
app.add_exception_handler(HTTPException, cors_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://engine-tune-portal.emergent.host",
        "http://localhost:3000",
        "https://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type", "Content-Length"]
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