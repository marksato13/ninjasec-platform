# Módulo: Catálogo de Equipos de Red

**Ruta prevista:** `/dashboard/catalog/devices`
**Acceso:** todos los roles internos (consulta) · `super_admin` y `admin` (edición)
**Backend previsto:** `modules/device_catalog`

---

## ¿Qué es?

Base de datos técnica de modelos de equipos de red: especificaciones, enlaces a datasheets oficiales, manuales, firmware y estado de ciclo de vida. Filtrado facetado tipo tienda online, pero para specs.

**Diferencia clave con el módulo 05 — Dispositivos:** aquel inventaría *instancias* (el switch de la sede Miraflores del cliente X). Este cataloga *modelos* (el Catalyst 2960-X como producto). Un modelo, muchas instancias.

---

## Problema que resuelve

Cuando hay que cotizar, diagnosticar o planificar un reemplazo, la información está dispersa entre PDFs de fabricantes, foros y correos. Y lo más costoso: **nadie sabe qué equipos del parque instalado ya están en EOL** hasta que uno falla y no hay repuesto.

---

## Entidades

### `catalog_devices`
| Campo | Descripción |
|---|---|
| `slug` | Identificador estable (`cisco-catalyst-2960x`) |
| `brand` / `model` | Marca y modelo |
| `category` | `router` · `switch` · `firewall` · `access_point` · `modem` · `server` · `nas` · `ups` |
| `subcategory` | `access` · `distribution` · `core` · `edge` |
| `osi_layer` | `L2` · `L3` · `L2+L3` |
| `segment` | `soho` · `smb` · `enterprise` · `carrier` |
| `port_count` / `port_speed` | Puertos y velocidad |
| `poe` / `poe_budget_w` | Soporte PoE y presupuesto |
| `stackable` / `rack_mountable` / `managed` | Características |
| `switching_capacity_gbps` / `throughput_mbps` | Rendimiento |
| `power_consumption_w` | Consumo — insumo para costeo operativo |
| `lifecycle_status` | `active` · `eos` (fin de venta) · `eol` (fin de vida) |
| `eos_date` / `eol_date` | Fechas oficiales del fabricante |
| `price_range_usd` | Precio referencial |
| `use_cases` | Casos de uso típicos |
| `tags` | Etiquetas de búsqueda |

### `catalog_device_links`
| Campo | Descripción |
|---|---|
| `catalog_device_id` | Modelo |
| `link_type` | `datasheet` · `config_manual` · `firmware` · `eol_notice` · `security_advisory` |
| `url` | **URL oficial del fabricante** |
| `archive_url` | Respaldo en Wayback Machine — los enlaces de Cisco y Huawei se caen a menudo |
| `last_checked_at` | Última verificación de que el enlace vive |

### `catalog_device_summaries`
Resumen ejecutivo **de elaboración propia**: specs clave extraídas, valoración práctica, problemas conocidos, compatibilidades. Es el valor agregado y es contenido original, no copiado.

---

## ⚠️ Regla de copyright — innegociable

**Los datasheets de fabricantes NO se alojan en la plataforma.** Son propiedad de Cisco, Huawei, MikroTik y demás. La política es:

1. Enlazar a la URL oficial del fabricante
2. Guardar un enlace de respaldo al Wayback Machine si la URL se cae
3. Redactar un resumen ejecutivo **propio**, citando la fuente

Misma política ya establecida en [[19-MODULO-DOCUMENTOS]]: la plataforma aloja punteros, no archivos de terceros.

---

## Filtros facetados

| Faceta | Valores |
|---|---|
| Marca | Cisco, MikroTik, Huawei, Ubiquiti, Juniper, Aruba, Fortinet, TP-Link |
| Categoría | Router, Switch, Firewall, AP, Módem, Servidor, NAS, UPS |
| Capa OSI | L2, L3, L2+L3 |
| Segmento | SOHO, SMB, Enterprise, Carrier |
| Características | PoE, apilable, gestionable, montaje en rack |
| **Ciclo de vida** | Activo, EOS, EOL |
| Rango de precio | Por tramos |

El filtro de ciclo de vida es el más valioso operativamente: responde "¿qué equipos del cliente ya no tienen soporte?".

---

## Funcionalidades previstas

### Buscador con filtros
Búsqueda difusa por marca, modelo y etiquetas, combinada con filtros facetados. Conteo de resultados por faceta.

### Ficha del modelo
Especificaciones completas, enlaces oficiales, resumen propio, casos de uso y **cuántas instancias hay en el parque instalado** (cruce con `devices`).

### Comparador
Hasta 4 modelos lado a lado — herramienta directa de preventa.

### Alerta de EOL en el inventario
Cruce automático: si un `device` del cliente corresponde a un modelo con `eol_date` pasada o próxima, se genera alerta en [[18-MODULO-ALERTAS]]. **Este cruce es la funcionalidad más rentable del módulo:** convierte el catálogo en un motor de oportunidades de renovación.

### Verificador de enlaces
Job periódico que comprueba los `url` y marca los caídos para actualizar con el respaldo.

---

## Acciones disponibles

| Acción | super_admin | admin | collaborator | client |
|---|:---:|:---:|:---:|:---:|
| Buscar y filtrar el catálogo | ✅ | ✅ | ✅ | ❌ |
| Ver ficha del modelo | ✅ | ✅ | ✅ | ❌ |
| Comparar modelos | ✅ | ✅ | ✅ | ❌ |
| Crear / editar modelo | ✅ | ✅ | ❌ | ❌ |
| Editar resumen ejecutivo | ✅ | ✅ | ✅ | ❌ |
| Ver alertas de EOL de su parque | ✅ | ✅ | ✅ | ⏳ |

---

## Reglas de negocio

1. **Nunca rehospedar documentación de terceros** — solo enlaces oficiales o al archivo web.
2. `slug` es único e inmutable.
3. Un modelo referenciado por dispositivos del inventario **no se borra**: se marca `eol`.
4. El resumen ejecutivo es contenido original con cita de la fuente.
5. Los enlaces se verifican periódicamente; uno roto no se elimina, se marca y se ofrece el respaldo.
6. Las fechas de EOS/EOL deben proceder del aviso oficial del fabricante, con el enlace como respaldo.

---

## Alcance por fases

| Fase | Alcance |
|---|---|
| **P1** | Entidad + CRUD + listado con filtros facetados. Carga inicial: 20-30 modelos habituales en PYMEs peruanas |
| **P2** | Ficha detallada + enlaces + resumen ejecutivo propio |
| **P3** | **Cruce con inventario + alerta de EOL** ← mayor retorno |
| **P4** | Comparador de modelos |
| **P5** | Verificador automático de enlaces + respaldo en archivo web |
| **P6** | Vínculo con [[28-MODULO-NETDOCTOR]]: qué comandos aplican a qué modelo |

---

## Nota sobre el origen de la idea

La versión estática en GitHub Pages (JSON + Fuse.js + filtros en el navegador) sigue siendo válida **como proyecto de portafolio independiente**. Dentro de NinjaSec el módulo justifica su lugar por una sola razón: el cruce con el inventario real de clientes. Sin ese cruce, es una wiki y no debería vivir aquí.
