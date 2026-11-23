# Módulo: Configuración del Sistema

**Ruta:** `/dashboard/settings`
**Acceso:** `super_admin`, `admin` (lectura) · escritura restringida a `super_admin`
**Backend:** `modules/catalogs` y `modules/docs`

---

## ¿Qué es?

Panel de administración de los **catálogos maestros** de la plataforma: las listas de valores que alimentan los selectores del resto de módulos. Cambiar aquí un tipo de proyecto se refleja en Proyectos, Servicios y Reportes sin tocar código.

Es la alternativa a tener enums hardcodeados: lo que el negocio cambia con frecuencia vive en base de datos.

---

## Pestañas

| Pestaña | Tabla | Alimenta a |
|---|---|---|
| **Tipos de proyecto** | `project_types` | Proyectos, Servicios |
| **Áreas** | `areas` | Servicios, Productos, Proyectos, perfil de Colaboradores |
| **Tipos de documento** | `doc_types` | Documentos de proyecto, Aprobaciones |

---

## Entidades

Los tres catálogos comparten forma:

| Campo | Descripción |
|---|---|
| `name` | Nombre único y legible |
| `slug` | Identificador estable en URLs y filtros (no aplica a `doc_types`) |
| `organization_id` | Nullable — un catálogo sin organización es **global del sistema** |
| `is_active` | Retiro lógico: deja de ofrecerse sin romper los registros que lo usan |
| `created_at` | Fecha de alta |

`doc_types` agrega `scope` (`public` / `private` / `both`).

---

## Funcionalidades

- Navegación por pestañas sin recargar la página
- Listado de cada catálogo con su estado activo/inactivo
- Alta de tipo de documento con validación Zod (`name` mínimo 2 caracteres, `scope` de la enum)
- Distinción entre catálogos globales (`organization_id` nulo) y propios de la organización

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Ver catálogos | ✅ | ✅ | ❌ | ❌ |
| Crear tipo de documento | ✅ | ❌ | ❌ | ❌ |
| Editar tipo de documento | ✅ | ❌ | ❌ | ❌ |
| Crear / editar área | ⏳ | ❌ | ❌ | ❌ |
| Crear / editar tipo de proyecto | ⏳ | ❌ | ❌ | ❌ |

⏳ = hoy son de **solo lectura** desde la UI; se administran por seed o SQL directo. Ver el checklist de implementación.

---

## Reglas de negocio

1. **Nunca se borra un elemento de catálogo.** Se marca `is_active = false`; borrar rompería los registros históricos que lo referencian.
2. `slug` es inmutable una vez creado — es la clave estable para filtros y URLs.
3. Un catálogo con `organization_id` nulo es global y no debe editarse desde una organización individual.
4. `name` y `slug` son únicos a nivel de tabla.
5. Solo `super_admin` escribe catálogos: un cambio aquí afecta a todos los módulos y a todos los usuarios.

---

## Alcance actual y límite

Este módulo administra **catálogos**, no configuración de infraestructura. Quedan explícitamente fuera y se gestionan por variables de entorno en `infra/docker-compose.yml`:

- Credenciales y `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `DATABASE_URL`
- Umbrales del motor de alertas (hoy constantes en código — ver [[18-MODULO-ALERTAS]])

Exponer umbrales operativos por organización es candidato natural a una cuarta pestaña.
