# Plan de mejoras técnicas — NinjaSec

Especificaciones de implementación para las 4 mejoras prioritarias detectadas en la auditoría técnica.

---

## Tarea 1 — Arreglar IP hardcodeada en `docker-compose.yml`

### Problema

`infra/docker-compose.yml` tiene una IP de red local fija en el build arg del frontend:

```yaml
# infra/docker-compose.yml línea 52
args:
  NEXT_PUBLIC_API_URL: http://10.40.131.94:8024/api/v1   # ROMPE en otra máquina
```

Y `frontend/.env.local` tiene la misma IP:

```env
NEXT_PUBLIC_API_URL=http://10.40.131.94:8024/api/v1
```

Consecuencia: el proyecto no levanta correctamente en ninguna máquina distinta a la tuya.

### Solución

**Paso 1 — Actualizar `infra/docker-compose.yml`**

Cambiar el `args` del servicio `frontend` para leer la variable del entorno del host, con fallback a `localhost`:

```yaml
# ANTES
args:
  NEXT_PUBLIC_API_URL: http://10.40.131.94:8024/api/v1

# DESPUÉS
args:
  NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8024/api/v1}
```

**Paso 2 — Crear `infra/.env.example`**

Nuevo archivo que documente las variables necesarias para levantar Docker:

```env
# infra/.env.example
NEXT_PUBLIC_API_URL=http://localhost:8024/api/v1
```

**Paso 3 — Corregir `frontend/.env.local`**

```env
# ANTES
NEXT_PUBLIC_API_URL=http://10.40.131.94:8024/api/v1

# DESPUÉS
NEXT_PUBLIC_API_URL=http://localhost:8024/api/v1
```

### Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `infra/docker-compose.yml` | Línea 52: cambiar IP por `${NEXT_PUBLIC_API_URL:-http://localhost:8024/api/v1}` |
| `frontend/.env.local` | Cambiar IP por `http://localhost:8024/api/v1` |
| `infra/.env.example` | Crear nuevo con la variable documentada |

### Criterio de éxito

- `./up-detached.ps1` levanta correctamente en una máquina sin la IP `10.40.131.94`
- El frontend puede hacer requests al backend en `localhost:8024`
- Para redes internas (universidad/trabajo), basta con setear `NEXT_PUBLIC_API_URL` antes de levantar

---

## Tarea 2 — Crear `frontend/src/app/login/page.tsx`

### Problema

La ruta `/login` existe como carpeta pero no tiene `page.tsx`. Navegar a `http://localhost:3018/login` devuelve 404.

### Contexto del código existente

La lógica ya está implementada, solo falta la UI:

- `lib/api.ts` — tiene `login(email, password)` que llama a `POST /api/v1/auth/login`
- `lib/auth.ts` — tiene `persistSession(token, user)`, `clearSession()`, `hasSession()`, `isAdminRole()`
- `LoginResponse` en `lib/api.ts` — incluye `access_token`, `redirect_to`, y `user`
- El backend retorna `redirect_to: "/dashboard"` para admin y `"/portal"` para colaborador/cliente

### Especificación de la página

**Archivo:** `frontend/src/app/login/page.tsx`

**Comportamiento:**

1. Si el usuario ya tiene sesión activa (`hasSession()`), redirigir inmediatamente según su rol
2. Renderizar formulario con campos `email` y `password`
3. Al enviar:
   - Llamar `login(email, password)` de `lib/api.ts`
   - Si éxito: llamar `persistSession(token, user)` y redirigir a `response.redirect_to`
   - Si error: mostrar mensaje de error inline (no redirigir)
4. Mostrar estado de carga mientras espera respuesta

**Validación con Zod (ya disponible en el proyecto):**

```typescript
import { z } from "zod"

const loginSchema = z.object({
  email: z.string().email("Email inválido").min(5).max(180),
  password: z.string().min(6, "Mínimo 6 caracteres").max(128),
})
```

**UI requerida:**

- Fondo oscuro consistente con el tema NinjaSec (`#0A0A0A` o `bg-black`)
- Logo o nombre "NinjaSec" en la parte superior
- Card/formulario centrado en pantalla
- Input de email con label
- Input de password con label y botón para mostrar/ocultar
- Botón de submit con estado loading (deshabilitado mientras hace fetch)
- Área de error debajo del formulario (texto rojo, visible solo cuando hay error)
- No usar SweetAlert2 aquí — error inline es mejor UX para login

**Dependencias a importar:**

```typescript
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useRouter } from "next/navigation"
import { login } from "@/lib/api"
import { persistSession, hasSession, isAdminRole } from "@/lib/auth"
```

**Flujo de redirección post-login:**

```typescript
// El backend ya decide a dónde ir
const response = await login(data.email, data.password)
persistSession(response.access_token, {
  id: response.user.id,
  name: response.user.name,
  role: response.user.role,
  email: response.user.email,
  job_title: response.user.job_title,
})
router.push(response.redirect_to)  // "/dashboard" o "/portal"
```

### Archivos a crear/modificar

| Archivo | Acción |
|---------|--------|
| `frontend/src/app/login/page.tsx` | Crear — página completa del formulario de login |

### Criterio de éxito

- Navegar a `http://localhost:3018/login` muestra el formulario (no 404)
- Login con `admin@ninjasec.local` / `change-me` redirige a `/dashboard`
- Login con credenciales incorrectas muestra mensaje de error visible
- El botón de submit se deshabilita durante la petición
- No hay errores de TypeScript (`npm run lint` pasa limpio)

---

## Tarea 3 — Agregar librería de generación de PDF

### Problema

El módulo `reports` existe en el backend y el frontend ya tiene `runReport()` y `downloadFile()`, pero `requirements.txt` no tiene ninguna librería de PDF. Cualquier intento de generar PDF falla en runtime.

### Comparación de opciones

| Librería | Pros | Contras | Recomendación |
|----------|------|---------|---------------|
| `reportlab` | Sin deps del sistema, madura (25+ años), control total del layout | API verbose, curva de aprendizaje | **Usar para PDFs programáticos** |
| `weasyprint` | HTML/CSS a PDF, fácil de plantillar | Requiere Cairo/Pango instalado en el sistema/Docker | Agregar si se necesita HTML templating |
| `fpdf2` | Ligero, simple | Menos features que reportlab | No usar, reportlab ya es suficiente |
| `xhtml2pdf` | HTML a PDF, simple | Poco mantenido, output mediocre | No usar |

### Decisión

Usar `reportlab` como librería principal. Para templating de HTML se puede agregar `jinja2` (ya puede estar disponible como dep transitiva de FastAPI, verificar antes de agregar).

### Cambio en `requirements.txt`

```
# AGREGAR al final de requirements.txt
reportlab==4.4.2
```

### Cambio en `backend/Dockerfile`

Verificar que el Dockerfile base tiene las dependencias del sistema para reportlab. En Alpine/Debian generalmente no se necesita nada extra para reportlab básico (a diferencia de weasyprint).

Si el Dockerfile usa `python:3.12-slim` o `python:3.12-alpine`, agregar en el paso de build:

```dockerfile
# Solo necesario si se usan fuentes TrueType en reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*
```

### Dónde usarla

El módulo `backend/app/modules/reports/` es donde va la lógica de generación. Estructura esperada del servicio:

```python
# backend/app/modules/reports/services/pdf_service.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet
import io

def generate_report_pdf(data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    # ... construir contenido
    doc.build(elements)
    return buffer.getvalue()
```

El router de reports ya debe retornar el PDF con:

```python
from fastapi.responses import Response

return Response(
    content=pdf_bytes,
    media_type="application/pdf",
    headers={"Content-Disposition": "attachment; filename=reporte.pdf"}
)
```

### Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `backend/requirements.txt` | Agregar `reportlab==4.4.2` |
| `backend/Dockerfile` | Agregar deps del sistema si es necesario (verificar primero) |
| `backend/app/modules/reports/services/` | Crear `pdf_service.py` con función base de generación |

### Criterio de éxito

- `pip install -r requirements.txt` instala sin errores
- `from reportlab.lib.pagesizes import A4` en Python no lanza `ImportError`
- El contenedor Docker levanta correctamente tras reconstruir con `./watch-backend.ps1`

---

## Tarea 4 — Tests del módulo `auth`

### Problema

`backend/tests/` solo tiene un `README.md`. Sin tests, cualquier cambio en el módulo de autenticación puede romper el acceso a todo el sistema sin ninguna señal de alerta.

### Stack de testing

Ya existe `httpx==0.28.1` en `requirements.txt`, que es lo que usa `TestClient` de FastAPI internamente. Solo falta agregar `pytest` y `pytest-cov`.

**Agregar a `requirements.txt`:**

```
# Testing (solo dev, se pueden separar en requirements-dev.txt si se prefiere)
pytest==8.4.0
pytest-cov==6.0.0
```

### Estructura de archivos a crear

```
backend/tests/
├── conftest.py            <- fixtures compartidas (db, client, usuario de prueba)
├── test_auth_login.py     <- tests de POST /api/v1/auth/login
├── test_auth_me.py        <- tests de GET /api/v1/auth/me
└── test_auth_security.py  <- tests de casos edge de seguridad
```

### `conftest.py` — fixtures necesarias

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.common.deps.database import get_db
from app.core.security import hash_password

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(db):
    # Crear usuario admin de prueba
    # Importar User y Organization model según la estructura real del proyecto
    ...
    
@pytest.fixture
def admin_token(client, admin_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "test-admin@ninjasec.local",
        "password": "testpassword123"
    })
    return response.json()["access_token"]
```

### `test_auth_login.py` — casos a cubrir

```
CASO 1: Login exitoso con credenciales válidas
  - POST /api/v1/auth/login { email: válido, password: válido }
  - Espera: 200, body tiene access_token, token_type="bearer", redirect_to

CASO 2: Password incorrecto
  - POST /api/v1/auth/login { email: válido, password: "wrong" }
  - Espera: 401

CASO 3: Email no registrado
  - POST /api/v1/auth/login { email: "noexiste@x.com", password: "abc123" }
  - Espera: 401

CASO 4: Email demasiado corto (falla validación Pydantic)
  - POST /api/v1/auth/login { email: "a@b", password: "abc123" }
  - Espera: 422

CASO 5: Password demasiado corto (falla validación Pydantic)
  - POST /api/v1/auth/login { email: "user@test.com", password: "abc" }
  - Espera: 422

CASO 6: Body vacío
  - POST /api/v1/auth/login {}
  - Espera: 422

CASO 7: Redirección según rol
  - Admin → redirect_to == "/dashboard"
  - Collaborator → redirect_to == "/portal"
```

### `test_auth_me.py` — casos a cubrir

```
CASO 1: Token válido retorna datos del usuario
  - GET /api/v1/auth/me con header Authorization: Bearer <token_válido>
  - Espera: 200, body tiene id, email, role, full_name, organization_id

CASO 2: Sin token retorna 401
  - GET /api/v1/auth/me sin header Authorization
  - Espera: 401

CASO 3: Token malformado retorna 401
  - GET /api/v1/auth/me con Authorization: Bearer token_basura
  - Espera: 401
```

### `test_auth_security.py` — casos edge

```
CASO 1: Token expirado retorna 401
  - Generar token con expiración en el pasado (timedelta negativo)
  - GET /api/v1/auth/me con ese token
  - Espera: 401

CASO 2: Token con firma incorrecta retorna 401
  - Usar jwt.encode con un secret diferente al de la app
  - GET /api/v1/auth/me con ese token
  - Espera: 401

CASO 3: SQL injection en email no rompe la app
  - POST /api/v1/auth/login { email: "' OR 1=1 --", password: "abc123" }
  - Espera: 401 o 422 (nunca 200, nunca 500)

CASO 4: Login actualiza last_login_at
  - Hacer login exitoso
  - Verificar que el campo last_login_at del usuario fue actualizado en la DB
```

### Comando para correr los tests

```powershell
# Desde backend/
cd backend
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

### Archivos a crear/modificar

| Archivo | Acción |
|---------|--------|
| `backend/requirements.txt` | Agregar `pytest==8.4.0` y `pytest-cov==6.0.0` |
| `backend/tests/conftest.py` | Crear — fixtures de DB, client, usuarios de prueba |
| `backend/tests/test_auth_login.py` | Crear — 7 casos de POST /login |
| `backend/tests/test_auth_me.py` | Crear — 3 casos de GET /me |
| `backend/tests/test_auth_security.py` | Crear — 4 casos edge de seguridad |

### Criterio de éxito

- `python -m pytest tests/ -v` corre sin errores de configuración
- Los 14 casos definidos pasan en verde
- La cobertura del módulo `auth` (routers + services + schemas) supera el 80%
- No se usa la base de datos de producción ni la de desarrollo para los tests

---

## Resumen de todos los cambios

| Tarea | Archivos afectados | Complejidad | Prioridad |
|-------|-------------------|-------------|-----------|
| 1. IP hardcodeada | 3 archivos, cambio de 1 línea c/u | Baja (15 min) | Inmediata |
| 2. Login page | 1 archivo nuevo (~80 líneas) | Media (2-3 hs) | Alta |
| 3. PDF library | 2 archivos + 1 archivo nuevo de servicio | Baja (30 min setup, luego implementación) | Media |
| 4. Tests auth | 4 archivos nuevos (~150 líneas total) | Media-Alta (3-4 hs) | Alta |

**Orden recomendado de implementación:**
1. Tarea 1 (rápida, debloquea trabajo colaborativo)
2. Tarea 2 (el login roto bloquea toda la UX)
3. Tarea 4 (los tests protegen lo que ya funciona)
4. Tarea 3 (feature nueva, puede esperar a que el MVP esté estable)
