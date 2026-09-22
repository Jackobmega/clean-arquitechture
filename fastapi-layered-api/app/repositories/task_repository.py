"""
Repositorio de Tarea (patrón Repository).

Responsabilidad única: traducir operaciones a consultas SQLAlchemy sobre
la tabla `tasks`. No conoce reglas de negocio ni HTTP.

Todas las lecturas de una tarea individual filtran SIEMPRE por `id` Y
`user_id`, de modo que una tarea ajena se comporta exactamente igual que
una inexistente (autorización a nivel de objeto, OWASP API1:2023).
"""

from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: int, data: TaskCreate) -> Task:
        task = Task(
            user_id=user_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
        )
        self._session.add(task)
        await self._session.flush()  # asigna el `id` sin cerrar la transacción
        await self._session.refresh(task)
        return task

    async def get_by_id_for_user(self, task_id: int, user_id: int) -> Optional[Task]:
        result = await self._session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
        is_done: Optional[bool] = None,
        priority: Optional[TaskPriority] = None,
    ) -> tuple[Sequence[Task], int]:
        # Los mismos filtros se aplican a la consulta de items y al conteo total.
        filters = [Task.user_id == user_id]
        if is_done is not None:
            filters.append(Task.is_done == is_done)
        if priority is not None:
            filters.append(Task.priority == priority)

        items_result = await self._session.execute(
            select(Task)
            .where(*filters)
            .order_by(Task.created_at.desc(), Task.id.desc())
            .offset(offset)
            .limit(limit)
        )
        total_result = await self._session.execute(
            select(func.count()).select_from(Task).where(*filters)
        )
        total = total_result.scalar_one()
        return items_result.scalars().all(), total

    async def update(self, task: Task, data: TaskUpdate) -> Task:
        # Solo se asignan los campos enviados con un valor distinto de None.
        for field, value in data.model_dump().items():
            if value is not None:
                setattr(task, field, value)
        await self._session.flush()
        await self._session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self._session.delete(task)
        await self._session.flush()
