# Módulo: Reportes

**Ruta:** `/dashboard/reports`
**Acceso:** `super_admin`, `admin`

---

## ¿Qué es?

Centro visual de generación y descarga de reportes. Agrupa todos los tipos de reportes disponibles en el sistema, con filtros por cliente y rango de fechas.

---

## Tipos de reporte

| Tipo | Formato | Descripción |
|------|---------|-------------|
| Reporte de Seguridad | PDF | Hallazgos de revisiones, vulnerabilidades y recomendaciones |
| Inventario de Activos | XLSX | Lista completa de dispositivos por cliente |
| Tickets de Soporte | XLSX | Historial de tickets con tiempos de respuesta |
| Reporte Ejecutivo | PDF | Resumen gerencial del estado de seguridad |
| Pipeline Comercial | XLSX | Leads y estado del CRM |
| Consolidado Cliente | PDF | Reporte 360° de un cliente específico |

---

## Funcionalidades

### Filtros globales
- Por cliente (dropdown)
- Por rango de fechas (desde / hasta)

### Cards de reporte
Cada reporte se muestra como una card con:
- Icono representativo con gradiente de color
- Título y descripción del contenido
- Preview de métricas relevantes (fecha del último reporte, conteo de registros)
- Botón PDF → descarga directa del PDF
- Botón XLSX → descarga directa de la hoja de cálculo
- Indicador de carga (spinner) durante la generación

### Gráfico de hallazgos
Barras horizontales CSS mostrando la distribución de hallazgos por severidad (critical, high, medium, low, info). Sin librería externa — CSS puro.

---

## Acciones disponibles

| Acción | super_admin | admin |
|--------|:-----------:|:-----:|
| Ver todos los reportes | ✅ | ✅ |
| Descargar PDF | ✅ | ✅ |
| Descargar XLSX | ✅ | ✅ |
| Filtrar por cliente | ✅ | ✅ |

---

## Proceso de generación

1. Usuario selecciona filtros (cliente, fechas)
2. Hace clic en el botón de formato deseado (PDF / XLSX)
3. El frontend llama al endpoint correspondiente del backend
4. El backend genera el archivo en memoria y lo devuelve como blob
5. El browser dispara la descarga automáticamente

---

## Datos técnicos

- Reporte seguridad PDF: `GET /api/v1/reports/security/{review_id}/pdf`
- Inventario XLSX: `GET /api/v1/reports/inventory/xlsx`
- Tickets XLSX: `GET /api/v1/support-tickets/export/xlsx`
- Consolidado cliente PDF: `GET /api/v1/reports/client/{id}/consolidated/pdf`
