"""
Router: Tareas (recurso protegido).

Todos los endpoints operan sobre el usuario autenticado: el `user_id`
nunca viaja en la URL ni en el cuerpo, se toma siempre del JWT.

Si la tarea no existe o pertenece a otro usuario se responde 404 (y no
403), para no revelar la existencia de recursos ajenos (OWASP API1:2023
Broken Object Level Authorization).

Este router solo maneja HTTP: valida la entrada con schemas, invoca al
servicio y traduce las excepciones de dominio a `HTTPException`.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_active_user, get_task_service
from app.core.exceptions import TaskNotFoundError
from app.models.task import TaskPriority
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.task import TaskCreate, TaskListResponse, TaskPublic, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=TaskPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una tarea",
)
async def create_task(
    payload: TaskCreate,
    service: Annotated[TaskService, Depends(get_task_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TaskPublic:
    task = await service.create_task(current_user.id, payload)
    return TaskPublic.model_validate(task)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="Listar las tareas del usuario (paginado)",
)
async def list_tasks(
    service: Annotated[TaskService, Depends(get_task_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: Annotated[int, Query(ge=1, description="Número de página (1-indexado)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Tamaño de página (máx. 100)")] = 20,
    is_done: Annotated[Optional[bool], Query(description="Filtrar por estado")] = None,
    priority: Annotated[Optional[TaskPriority], Query(description="Filtrar por prioridad")] = None,
) -> TaskListResponse:
    tasks, total = await service.list_tasks(
        current_user.id,
        page=page,
        page_size=page_size,
        is_done=is_done,
        priority=priority,
    )
    return TaskListResponse(
        items=[TaskPublic.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{task_id}",
    response_model=TaskPublic,
    responses={404: {"model": ErrorResponse}},
    summary="Obtener una tarea por id",
)
async def get_task(
    task_id: int,
    service: Annotated[TaskService, Depends(get_task_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TaskPublic:
    try:
        task = await service.get_task(task_id, current_user.id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TaskPublic.model_validate(task)


@router.put(
    "/{task_id}",
    response_model=TaskPublic,
    responses={404: {"model": ErrorResponse}},
    summary="Actualizar (parcialmente) una tarea",
)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    service: Annotated[TaskService, Depends(get_task_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TaskPublic:
    try:
        task = await service.update_task(task_id, current_user.id, payload)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TaskPublic.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    summary="Eliminar una tarea",
)
async def delete_task(
    task_id: int,
    service: Annotated[TaskService, Depends(get_task_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    try:
        await service.delete_task(task_id, current_user.id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
