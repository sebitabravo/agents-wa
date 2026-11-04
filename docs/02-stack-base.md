<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Capítulo 2 — Stack base para agentes sobre WhatsApp con FastAPI

Este capítulo define el stack mínimo para un agente sobre WhatsApp con FastAPI:
configuración fail-fast, base de datos, rate-limit y observabilidad. La regla es
empezar simple con SQLite y endurecer solo cuando el despliegue lo exige.

La audiencia es un desarrollador Python que necesita una base copiable verificada
contra cuatro proyectos reales. Al terminar dispone de un servicio que rechaza
configuración inválida en el arranque, persiste sesiones acotadas y expone límites
y salud observables.

## 2.1 Estructura mínima del proyecto

Los servicios de dominio viven en un paquete dedicado, como en AgroVoz
(`backend/app/services/` con más de 30 servicios: clima, audio, RAG y WhatsApp).

```text
backend/
  app/
    main.py              # app factory, middlewares, routers, startup checks
    core/
      config.py          # Settings con pydantic-settings, validación fail-fast
      database.py        # engine, SessionLocal, PRAGMAs
      security.py        # middlewares: rate-limit, headers, hosts
      rate_limiter.py    # limiters por recurso (sliding window)
    api/
      health.py          # GET /api/v1/health y /api/v1/ready
      chat.py            # POST /api/v1/chat (rate-limit + sesión)
      admin/metrics.py   # panel operativo de solo lectura
    services/
      llm_service.py     # cliente httpx hacia el proveedor LLM
      sessions.py        # historial acotado por sesión
      metrics_service.py # KPIs para el panel
  .env.example
  requirements.txt       # fastapi, uvicorn, pydantic-settings, httpx, sqlalchemy
```

## 2.2 Configuración y entorno con falla rápida

Toda configuración sale de variables de entorno y se valida en el arranque. Dos
patrones reales marcan los extremos: Wenuke usa un `dataclass` ligero con
`os.getenv` y una propiedad que habilita el modo admin solo con token suficiente
(`Wenuke/backend/config.py:9-17` y `:28-30`). ManttoAI usa
`pydantic-settings` con validadores que abortan ante entornos no soportados o
secretos demo (`ManttoAI/backend/app/config.py:162-174` para el validador de
seguridad; el fallback a memoria
está en `middleware/rate_limit.py:96-134`). AgroVoz sigue la misma escuela
(`AgroVoz/backend/app/core/config.py:26`).

El estándar recomendado es `pydantic-settings`: convierte errores de configuración
en excepciones antes de aceptar tráfico. El piso de 16 caracteres es el mínimo
verificado en los secretos operativos del copiloto (`copiloto-recepcion/copiloto/src/copiloto/config.py:128-134`).

```python
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SUPPORTED_ENVS = frozenset({"development", "staging", "production"})

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = "sqlite:///./agent.db"
    secret_key: str = Field(default="")
    llm_api_key: str = Field(default="")
    llm_model: str = "llama-3.1-70b-versatile"
    rate_limit_per_minute: int = 60

    @field_validator("app_env", mode="before")
    @classmethod
    def validate_env(cls, value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized not in SUPPORTED_ENVS:
            raise ValueError(f"Unsupported APP_ENV: {value!r}")
        return normalized

    @field_validator("secret_key")
    @classmethod
    def require_secret_outside_dev(cls, value: str, info) -> str:
        env = info.data.get("app_env", "development") if info.data else "development"
        if env != "development" and len(value) < 16:
            raise ValueError("SECRET_KEY needs 16+ chars outside development")
        return value

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

La validación se completa con un chequeo explícito en `startup`:

```python
async def validate_startup(settings: Settings) -> None:
    if not settings.llm_api_key:
        raise RuntimeError("Missing LLM_API_KEY; set it in .env")
    if settings.app_env != "development" and settings.database_url.startswith("sqlite"):
        raise RuntimeError("SQLite not allowed outside development; set DATABASE_URL")
```

## 2.3 Receta mínima de `.env` y verificación de arranque

Cinco entradas bastan para levantar SQLite + proveedor LLM + rate-limit en memoria.

```bash
# --- minimal .env (development) ---
APP_ENV=development
DATABASE_URL=sqlite:///./agent.db
SECRET_KEY=change-me-in-production-min-16-chars-0000
LLM_API_KEY=put-your-provider-key-here
LLM_MODEL=llama-3.1-70b-versatile
```

Verificación en tres pasos: validar settings, probar salud y confirmar `ready`.
Ningún worker acepta tráfico si un paso falla.

```bash
# 1. Fail-fast before binding the port
python -c "from app.core.config import get_settings; s = get_settings(); print(s.app_env, s.database_url)"
# 2. Smoke test after boot
uvicorn app.main:app --port 8000 &
curl -s http://localhost:8000/api/v1/health; echo
curl -s http://localhost:8000/api/v1/ready; echo
```

Si el primer comando lanza `ValueError` o `RuntimeError`, el problema es de
configuración, no de código. Esa es la propiedad fail-fast: fallar en segundos en
el arranque en lugar de fallar en horas en producción.

## 2.4 Base de datos: SQLite primero

SQLite es el default para desarrollo, demos y pilotos de un nodo. Wenuke resuelve
`DB_PATH` con default local (`Wenuke/backend/config.py:11`),
AgroVoz define `sqlite:///.../agrovoz.db` como default
(`AgroVoz/backend/app/core/config.py:23`) y el copiloto
persiste sesiones en SQLite con historial acotado
(`copiloto-recepcion/copiloto/src/copiloto/ai/sessions.py:12-22,33-51`).

El patrón del copiloto es la referencia para memoria conversacional: truncar cada
mensaje a `MAX_TEXT` y recortar el historial a un límite fijo antes de guardar
(el diseño por canal se cubre en el [Capítulo 6](06-canales-memoria.md)).

```python
import json
import sqlite3

MAX_TEXT = 1200

def save_turn(db: sqlite3.Connection, session_id: str, history: list[dict]) -> None:
    trimmed = [{"role": m["role"], "content": m["content"][:MAX_TEXT]} for m in history]
    db.execute(
        """INSERT INTO ai_sessions(session_id, history, updated_at)
           VALUES (?, ?, strftime('%s','now'))
           ON CONFLICT(session_id) DO UPDATE SET history=excluded.history""",
        (session_id, json.dumps(trimmed, ensure_ascii=False)),
    )
    db.commit()
```

Para SQLAlchemy se usa WAL, `check_same_thread=False` y PRAGMAs al conectar
(AgroVoz: `backend/app/core/database.py:49`):

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///./agent.db", connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def apply_pragmas(dbapi_connection, _record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
```

Un piloto opera así sin infraestructura: un proceso, un archivo, copias con
`sqlite3 .backup`. El límite real es la escritura concurrente, no el volumen.

## 2.5 Cuándo migrar a MySQL o Turso

Se migra ante señales concretas: múltiples réplicas, escrituras concurrentes o
serverless sin disco. ManttoAI lo impone por código: SQLite o credenciales demo
fuera de desarrollo abortan el arranque
(`ManttoAI/backend/app/config.py:162`). Wenuke
anticipa la ruta serverless con Turso sobre HTTP
(`Wenuke/backend/config.py:15-17`).

| Criterio | SQLite local | MySQL | Turso |
|---|---|---|---|
| Uso | Desarrollo, demo, piloto de un nodo | Producción multirréplica | Serverless sin disco |
| Operación | Cero: un archivo | Servidor, backups, usuarios | Gestionado por HTTP |
| Concurrencia | Un escritor (WAL ayuda en lectura) | Alta con pool | Alta en lectura |
| Variable | `DATABASE_URL=sqlite:///./agent.db` | `DATABASE_URL=mysql+pymysql://user:pass@host:3306/agent` | `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN` |

La migración cambia solo configuración: `DATABASE_URL` obligatoria en producción,
pool (`pool_size`, `max_overflow`, `pool_pre_ping=True`) y migraciones
reversibles. Para Turso se conservan las tablas y se usa el cliente HTTP.

## 2.6 Llamadas HTTP salientes con `httpx`

Toda integración externa usa `httpx` con timeout explícito. AgroVoz lo aplica con
cliente reutilizado para clima (`AgroVoz/backend/app/services/weather_service.py:408`)
y clientes de corta vida para WhatsApp
(`AgroVoz/backend/app/services/openwa_service.py:166`).

```python
import httpx

TIMEOUT = httpx.Timeout(8.0, connect=3.0)

async def call_llm(api_key: str, model: str, messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "messages": messages, "temperature": 0.2},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"LLM provider error: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"LLM network error: {type(exc).__name__}") from exc
    return str(response.json()["choices"][0]["message"]["content"])
```

Reglas: timeout siempre, reutilizar `AsyncClient` en rutas calientes y distinguir
error de red de error de estado. El llamante decide el fallback, nunca el cliente.

## 2.7 Rate-limit por IP y por recurso

El rate-limit protege el costo del LLM y la cuota de WhatsApp: límite global barato
más límites estrictos por recurso costoso. ManttoAI usa `slowapi` con Redis y
fallback a memoria (`ManttoAI/backend/app/middleware/rate_limit.py:96-134`;
registro en `ManttoAI/backend/app/main.py:146`).
AgroVoz usa middleware propio por IP más limiters por recurso
(`AgroVoz/backend/app/core/security.py:214`,
`AgroVoz/backend/app/core/rate_limiter.py:30`).

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# @limiter.limit("5/minute") on POST /api/v1/chat (LLM cost)
# @limiter.limit("30/minute") on GET /api/v1/weather (data cost)
```

Receta: 60/minuto global por IP, 5/minuto en chat o demo con LLM y 30/minuto en
datos. Los limiters por recurso responden `429` con `Retry-After`
(`rate_limiter.py:119-137`); el middleware global devuelve `429` sin ese header
(`security.py:255-260`). En un nodo basta memoria; con réplicas se comparte el
contador vía `REDIS_URL`.

## 2.8 Observabilidad mínima: salud, logs y métricas

Dos endpoints, `/health` y `/ready` (`ManttoAI/backend/app/main.py:200-209`),
trazabilidad mediante `X-Correlation-ID` (`ManttoAI/backend/app/middleware/correlation.py:9-21`)
y un panel de solo lectura (`backend/app/api/admin/metrics.py:1-25`). AgroVoz expone
`/health` (`AgroVoz/backend/app/api/health.py:40`) y un
chequeo SQLite dedicado (`AgroVoz/backend/app/services/monitor_service.py:181`).

```python
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1")

@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "agent"}

@router.get("/ready")
def ready(db: Session) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
```

La convención es registrar `request_id`, latencia del LLM, modelo y resultado. Las métricas mínimas son conversaciones por día, latencia p50/p95, intenciones y errores por tipo. Con eso el piloto detecta caídas, abusos y deriva sin telemetría pesada.

## 2.9 Lista de verificación antes de exponer el servicio

- [ ] `APP_ENV` válido y `SECRET_KEY` de 16+ caracteres fuera de desarrollo.
- [ ] `validate_startup` supera LLM, escritura SQLite y coherencia entorno/DB.
- [ ] `GET /health` y `GET /ready` responden 200 con base de datos `ok`.
- [ ] `429` comprobado en chat con 6 envíos rápidos.
- [ ] Historial acotado (`MAX_TEXT` y límite de turnos) verificado en dos turnos largos.
- [ ] Logs con `request_id` y métricas diarias visibles en el panel admin.
- [ ] Plan de migración a MySQL o Turso documentado si el piloto supera un nodo.

### Referencias de evidencia (path:línea)

- `Wenuke/backend/config.py:9-17` — config con `os.getenv` y `DB_PATH`; `:28-30` — `admin_token_activo`.
- `Wenuke/backend/config.py:15-17` — Turso (`TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`).
- `ManttoAI/backend/app/config.py:128-131` — Redis.
- `ManttoAI/backend/app/middleware/rate_limit.py:96-134` — fallback a memoria.
- `ManttoAI/backend/app/config.py:151-173` — fail-fast que prohíbe SQLite y credenciales demo en producción.
- `AgroVoz/backend/app/core/config.py:26` — `Settings` con `pydantic-settings`.
- `AgroVoz/backend/app/main.py:65-104` — `request_id` en logs y respuestas.
- `AgroVoz/backend/app/api/admin/metrics.py:1-25` — panel admin de solo lectura.
- `AgroVoz/backend/app/services/` — `httpx` (`weather_service.py:408`, `openwa_service.py:166`).
- `AgroVoz/backend/app/core/database.py:49` — PRAGMAs SQLite.
- `copiloto-recepcion/copiloto/src/copiloto/ai/sessions.py:12-22,33-51` — sesiones acotadas y persistencia.
