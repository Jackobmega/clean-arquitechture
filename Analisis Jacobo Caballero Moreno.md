# Análisis del Repositorio: Clean Architecture con Python y FastAPI

Este documento analiza la estructura del repositorio `alefeans/python-clean-architecture` solicitado.

## 1. Flujo de una Petición en Clean Architecture (General)

En la Arquitectura Limpia (Clean Architecture), el flujo de una petición sigue la **Regla de Dependencia**: las dependencias en el código fuente solo pueden apuntar hacia adentro, hacia las reglas de negocio de más alto nivel (el Dominio).

El flujo típico de una petición (ej. HTTP) de afuera hacia adentro es:

1. **Framework y API (Capa Externa / Presentación):** El cliente realiza una petición HTTP. El framework web (como FastAPI) recibe la petición a través de un **Controlador (Router)**.
2. **Adaptadores (Controladores / DTOs):** El controlador recibe los datos crudos, los valida superficialmente y los mapea a un DTO (Data Transfer Object). Luego, llama al **Caso de Uso** (Interactor) enviando el DTO.
3. **Casos de Uso (Capa de Aplicación):** El caso de uso orquesta la lógica del negocio.
   - Obtiene datos desde la base de datos a través de los **Puertos (Interfaces Abstractas de Repositorios)**, para no depender de la base de datos real.
   - Ejecuta la lógica del negocio orquestando entidades.
4. **Entidades (Capa de Dominio):** El caso de uso interactúa con las **Entidades** y los **Objetos de Valor**, que son las reglas de negocio puras e independientes de cualquier tecnología.
5. **Infraestructura (Bases de Datos / APIs externas):** La implementación concreta del Repositorio (que pertenece a la capa más externa de infraestructura) ejecuta las consultas a la base de datos (usando SQLModel) para almacenar o devolver las Entidades de Dominio al Caso de Uso.
6. **Respuesta:** El caso de uso retorna el resultado (a través de otro DTO) al controlador, que finalmente lo formatea como JSON y lo responde al cliente.

---

## 2. Identificación de Capas en el Proyecto

Revisando la documentación y los patrones declarados en el repositorio, las capas propuestas por Clean Architecture están claramente presentes:

- **Dominio (Domain):** Está presente. El repositorio implementa **Value Objects** (Objetos de Valor para *Email, Password, ID/UUID*) que se auto-validan, y cuenta con un **Manejo Centralizado de Excepciones de Dominio** (Domain-specific exceptions) para representar fallos de negocio.
- **Aplicación (Application / Use Cases):** Está presente. Se mencionan explícitamente **Use Cases** para operaciones (ej. CRUD de usuarios), usando **DTOs**. Además, declara las interfaces abstractas mediante el **Repository Pattern** y el **Unit of Work Pattern**.
- **Presentación (API):** Está presente. Se utiliza **FastAPI** para exponer los endpoints (Routers), inyectando los casos de uso para que procesen las peticiones y orquestando la autenticación (OAuth2 + JWT).
- **Infraestructura (Infrastructure):** Está presente. Contiene la **implementación concreta** de los repositorios, la base de datos (**PostgreSQL** gestionada a través del ORM **SQLModel** y migraciones con **Alembic**), y el adaptador de seguridad (**Passlib** para hashear).

---

## 3. Flujo de una Petición de Acuerdo con los Componentes del Proyecto

Tomando como ejemplo el flujo de **Creación de un Usuario (User CRUD)** implementado en este proyecto:

1. **Petición del Cliente:** El cliente envía una petición POST a la ruta de usuarios con los datos (JSON).
2. **Capa API (FastAPI Router):**
   - El *Router de FastAPI* intercepta la petición HTTP.
   - Usa Pydantic/FastAPI para la validación estructural inicial del request (el DTO de entrada).
   - Mediante inyección de dependencias (`Depends`), instancia y llama al **Caso de Uso** (Create User Use Case).
3. **Validación de Dominio (Value Objects):**
   - Durante el proceso, campos como el Email, Password o el UUID se pasan por los **Value Objects** correspondientes, donde ocurren validaciones estrictas de dominio (ej. formato de email válido o contraseña fuerte).
4. **Capa de Aplicación (Caso de Uso & Unit of Work):**
   - El Caso de Uso utiliza el **Unit of Work Pattern** abstracto para iniciar y garantizar una transacción en base de datos.
   - Pide al **Repositorio Abstracto** (Abstract Interface) que compruebe si el usuario o email ya existe. Si es así, arroja una Excepción de Dominio (ej. `UserAlreadyExistsException`).
   - El Caso de Uso orquesta el hash de la contraseña y ensambla la Entidad de Usuario.
5. **Capa de Infraestructura (SQLModel & PostgreSQL):**
   - El Caso de Uso le dice al Unit of Work que guarde (save/commit).
   - En ejecución real, se inyecta la **Implementación Concreta del Repositorio**. Este repositorio concreto mapea la Entidad de dominio pura a un modelo ORM de **SQLModel**.
   - Se ejecuta el SQL hacia **PostgreSQL** y se hace *commit* a la base de datos.
6. **Respuesta al Cliente:**
   - La entidad recién creada es mapeada a un DTO de respuesta seguro (ocultando el password hash).
   - El Router de FastAPI lo formatea en JSON y envía la respuesta `201 Created` al cliente.
