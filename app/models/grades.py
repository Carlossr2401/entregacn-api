from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError
from typing import Optional
from datetime import datetime
import uuid

# --- Modelo para Creación (POST) ---
# Ahora espera AlumnoNombre y ClaseNombre

class GradeCreateModel(BaseModel):
    ClaseNombre: str = Field(..., min_length=1, max_length=100)  # <--- CORREGIDO
    AlumnoNombre: str = Field(..., min_length=1, max_length=100) # <--- CORREGIDO
    Nota: int = Field(..., ge=0, le=10) # Nota debe estar entre 0 y 10
    Fecha: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @field_validator('Fecha')
    def validate_iso_date(cls, v):
        if v is None:
            return None
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, TypeError):
            raise ValueError("La fecha debe estar en formato ISO")

    class Config:
        json_schema_extra = {
            "example": {
                "ClaseNombre": "Programación",    # <--- CORREGIDO
                "AlumnoNombre": "Carlos Gómez", # <--- CORREGIDO
                "Nota": 7
            }
        }


# --- Modelo para Actualización (PUT) ---
# Ahora actualiza AlumnoNombre y ClaseNombre

class UpdateGradeModel(BaseModel):
    # Permite a Pydantic leer desde atributos de objeto (ORM)
    model_config = ConfigDict(from_attributes=True) 
    
    ClaseNombre: Optional[str] = Field(None, min_length=1, max_length=100)  # <--- CORREGIDO
    AlumnoNombre: Optional[str] = Field(None, min_length=1, max_length=100) # <--- CORREGIDO
    Nota: Optional[int] = Field(None, ge=0, le=10)
    Fecha: Optional[str] = None

    @field_validator('Fecha')
    def validate_iso_date_optional(cls, v):
        if v is None:
            return None
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, TypeError):
            raise ValueError("La fecha debe estar en formato ISO")


# --- Modelo Principal / de Respuesta (GET) ---
# Alineado con el modelo de BBDD GradeDB (que usa noteId)

class GradeModel(BaseModel):
    # Permite a Pydantic leer desde atributos de objeto (ORM)
    model_config = ConfigDict(from_attributes=True) 

    # Campos gestionados por la BBDD
    NoteID: uuid.UUID       # <--- CORREGIDO (de 'id' a 'noteId')
    created_at: datetime
    updated_at: datetime
    
    # Campos del usuario
    ClaseNombre: str  # <--- CORREGIDO
    AlumnoNombre: str # <--- CORREGIDO
    Nota: int
    Fecha: datetime # La BBDD devolverá un objeto datetime