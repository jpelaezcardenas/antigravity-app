# Contexia Backend - FastAPI

Este es el servidor API para Contexia, construido con FastAPI y conectado a Supabase.

## Estructura del Proyecto

- `core/`: Lógica central (seguridad, excepciones, constantes).
- `domain/`: Modelos de datos (Pydantic).
- `application/`: Servicios de lógica de negocio.
- `infrastructure/`: Implementaciones de persistencia (SQLAlchemy, Supabase).
- `presentation/`: Controladores API (Routers, Endpoints).

## Ejecución Local

1. Crear entorno virtual: `python -m venv venv`
2. Activar: `.\venv\Scripts\Activate`
3. Instalar: `pip install -r requirements.txt`
4. Configurar `.env` basándose en `.env.example`.
5. Ejecutar: `python main.py`

Acceder a la documentación en `http://localhost:8080/docs`.
