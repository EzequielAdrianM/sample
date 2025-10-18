from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=100)
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    nombre: str
    email: str
    activo: bool
    profile_picture: bool
    
    class Config:
        from_attributes = True

class FotoPerfilResponse(BaseModel):
    user_id: int
    profile_picture: bool
    s3_key: str
    mensaje: str