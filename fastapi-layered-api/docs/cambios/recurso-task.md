# Cambio: recurso `Task` (tareas por usuario)

Tareas personales asociadas a un usuario (relación N:1 con `User`). Cada
usuario solo puede crear, ver, editar y eliminar **sus propias** tareas.

El diff completo está en [`recurso-task.diff`](recurso-task.diff).

## Archivos por capa

| Capa | Archivo | Estado | Contenido |
|---|---|---|---|
| Models | `app/models/task.py` | nuevo | Modelo `Task` (tabla `tasks`) y enum `TaskPriority` |
| Models | `app/models/__init__.py` | modificado | Registra `Task` en `Base.metadata` |
| Schemas | `app/schemas/task.py` | nuevo | `TaskCreate`, `TaskUpdate`, `TaskPublic`, `TaskListResponse` |
| Core | `app/core/exceptions.py` | modificado | `TaskNotFoundError` |
| Repositories | `app/repositories/task_repository.py` | nuevo | Consultas siempre filtradas por `id` **y** `user_id` |
| Services | `app/services/task_service.py` | nuevo | Regla de pertenencia; lanza `TaskNotFoundError` |
| API | `app/api/deps.py` | modificado | `get_task_repository`, `get_task_service` |
| API | `app/api/v1/routers/tasks.py` | nuevo | 5 endpoints bajo `/tasks` |
| API | `app/api/v1/api.py` | modificado | Registra el router `tasks` |
| Tests | `tests/test_tasks.py` | nuevo | 6 tests de integración |
| Docs | `README.md` | modificado | Estructura del proyecto actualizada |

## Endpoints

Todos requieren autenticación (`Authorization: Bearer <token>`).

| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| POST | `/api/v1/tasks` | 201 | 401 |
| GET | `/api/v1/tasks?page=&page_size=&is_done=&priority=` | 200 | 401 |
| GET | `/api/v1/tasks/{task_id}` | 200 | 401, 404 |
| PUT | `/api/v1/tasks/{task_id}` | 200 | 401, 404 |
| DELETE | `/api/v1/tasks/{task_id}` | 204 | 401, 404 |

Una tarea de otro usuario responde **404** (no 403) para no revelar que
existe (OWASP API1:2023 Broken Object Level Authorization).

## Decisiones

- El `user_id` nunca viaja en la petición: se toma del JWT.
- El listado se ordena por `created_at desc` y luego `id desc` como
  desempate (SQLite guarda `func.now()` con precisión de segundos).
- En `PUT`, un campo enviado como `null` se ignora igual que uno omitido.

## Verificación

```
pytest -v   ->   14 passed (4 auth + 4 users + 6 tasks)
```
