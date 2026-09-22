"""
Schemas (contratos de la API) para el recurso Tarea.

Mismo patrón que app/schemas/user.py (Create / Update / Public):

- `TaskCreate`       -> lo que el cliente envía al crear una tarea.
- `TaskUpdate`       -> campos opcionales para una actualización parcial.
- `TaskPublic`       -> lo que la API devuelve.
- `TaskListResponse` -> colección paginada de tareas.

El `user_id` nunca se recibe del cliente: siempre se toma del usuario
autenticado, para que nadie pueda crear tareas a nombre de otro.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskPriority


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Título de la tarea.")
    description: Optional[str] = Field(
        None, max_length=1000, description="Descripción opcional de la tarea."
    )
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Prioridad de la tarea.")
    due_date: Optional[datetime] = Field(None, description="Fecha límite opcional.")


class TaskUpdate(BaseModel):
    """Todos los campos son opcionales: soporta PUT parcial."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[TaskPriority] = None
    is_done: Optional[bool] = None
    due_date: Optional[datetime] = None


class TaskPublic(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    priority: TaskPriority
    is_done: bool
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Permite construir el schema directamente desde el objeto ORM.
    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Envoltorio con metadatos de paginación (buena práctica REST)."""

    items: list[TaskPublic]
    total: int
    page: int
    page_size: int
