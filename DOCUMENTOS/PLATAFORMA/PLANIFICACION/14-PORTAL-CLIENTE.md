# Portal Cliente

**Ruta base:** `/portal`
**Acceso:** solo `client`

---

## ¿Qué es?

El portal cliente es el espacio exclusivo para los usuarios de las empresas clientes de NinjaSec. Permite al personal TI del cliente ver el estado de su infraestructura, sus documentos, solicitar servicios y gestionar sus tickets de soporte — sin acceso al backoffice.

---

## Secciones del portal

### Dashboard del portal (`/portal`)
Vista de inicio con:
- Saludo personalizado con nombre y empresa
- KPIs del cliente: tickets abiertos, dispositivos activos, documentos disponibles, servicios contratados
- Accesos rápidos a las secciones del portal
- Últimas alertas o notificaciones del cliente

### Inventario (`/portal/inventory`)
Lista de dispositivos monitoreados de su empresa:
- Filtro por tipo de dispositivo
- Estado visual (semáforo) de cada activo
- Agrupados por tipo
- Banner de alerta si hay dispositivos en `pending_review`

### Documentos (`/portal/documents`)
Biblioteca de documentos compartidos por NinjaSec con el cliente:
- Reportes de seguridad entregados
- Contratos y acuerdos de servicio
- Manuales y procedimientos
- Filtro por tipo de documento
- Preview de PDFs dentro del portal
- Descarga de cada documento
- Badge de estado (Activo / Borrador / Archivado)

### Tickets (`/portal/tickets`)
Gestión de sus solicitudes de soporte:
- Ver todos sus tickets con estado y prioridad
- Crear nuevo ticket (título, descripción, prioridad)
- Ver historial de eventos de cada ticket
- NO puede cambiar estado ni reasignar

### Servicios (`/portal/services`)
Catálogo de servicios de NinjaSec:
- Ver todos los servicios disponibles
- Solicitar un servicio con descripción de necesidad
- Ver estado de sus solicitudes previas

### Perfil (`/portal/profile`)
Gestión de la cuenta personal:
- Ver y editar datos personales
- Barra de progreso de completitud del perfil
- Cambiar contraseña

---

## Qué NO puede hacer el cliente

- Acceder al backoffice (`/dashboard`)
- Ver información de otros clientes
- Cambiar estado de sus tickets
- Ver leads o información comercial
- Acceder a reportes internos de NinjaSec
- Ver o gestionar otros usuarios

---

## Navegación del portal

El portal tiene su propio sidebar simplificado con accesos a:
- Inicio
- Inventario
- Documentos
- Tickets
- Servicios
- Perfil

---

## Ejemplo de usuarios portal (datos demo)

| Empresa | Email |
|---------|-------|
| Blue Shield Corp | client@ninjasec.local |
| LogiGroup Peru | ti@logigroup.ninjasec.local |
| MediSalud Clínicas | ti@medisalud.ninjasec.local |
| Constructora Del Sur | ti@constructorasur.ninjasec.local |
| FinanzApp Technologies | ti@finanzapp.ninjasec.local |
| RetailMax Peru | ti@retailmax.ninjasec.local |

Contraseña de todas: **`NinjaSec2024!`**

---

## Datos técnicos

El portal usa los mismos endpoints del backend que el backoffice, pero el JWT del usuario solo tiene acceso a sus propios datos. El backend filtra automáticamente por `client_id` basado en el token.
