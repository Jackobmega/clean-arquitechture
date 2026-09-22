"""
Servicio de Tarea (capa de lógica de negocio).

La única regla de negocio del recurso es la de pertenencia (ownership):
un usuario solo puede operar sobre sus propias tareas. Si la tarea no
existe o pertenece a otro usuario se lanza la misma excepción de dominio
(`TaskNotFoundError`), para no revelar la existencia de recursos ajenos.
El servicio no conoce HTTP; el router traduce la excepción a un 404.
"""

from typing import Optional

from app.core.exceptions import TaskNotFoundError
from app.models.task import Task, TaskPriority
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    async def create_task(self, user_id: int, data: TaskCreate) -> Task:
        """Crea una tarea asociada al usuario indicado."""
        return await self._repository.create(user_id=user_id, data=data)

    async def list_tasks(
        self,
        user_id: int,
        *,
        page: int,
        page_size: int,
        is_done: Optional[bool] = None,
        priority: Optional[TaskPriority] = None,
    ) -> tuple[list[Task], int]:
        """Lista paginada de las tareas del usuario, con filtros opcionales."""
        offset = (page - 1) * page_size
        tasks, total = await self._repository.list_for_user(
            user_id,
            offset=offset,
            limit=page_size,
            is_done=is_done,
            priority=priority,
        )
        return list(tasks), total

    async def get_task(self, task_id: int, user_id: int) -> Task:
        """Obtiene una tarea del usuario o lanza `TaskNotFoundError`."""
        task = await self._repository.get_by_id_for_user(task_id, user_id)
        if task is None:
            raise TaskNotFoundError(f"Tarea con id={task_id} no encontrada.")
        return task

    async def update_task(self, task_id: int, user_id: int, data: TaskUpdate) -> Task:
        task = await self.get_task(task_id, user_id)
        return await self._repository.update(task, data)

    async def delete_task(self, task_id: int, user_id: int) -> None:
        task = await self.get_task(task_id, user_id)
        await self._repository.delete(task)
