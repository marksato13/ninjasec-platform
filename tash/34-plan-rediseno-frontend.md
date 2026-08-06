# Plan de rediseño frontend — NinjaSec Dashboard

Planificación completa de mejoras visuales, paleta de colores profesional
y reorganización de módulos por rol.

---

## Diagnóstico desde las capturas

| Problema | Impacto | Causa raíz |
|----------|---------|-----------|
| Gran espacio vacío en el content area | Alto | El `workspace` no tiene `padding-top` después del topbar; el contenido de cada page no ocupa el espacio correctamente |
| Sidebar muestra TODOS los módulos sin filtro por rol | Alto | `navGroups` es estático, no filtra según el rol del usuario logueado |
| Paleta es un solo tono (navy oscuro) | Medio | Pocas variables de color; falta jerarquía visual entre niveles de superficie |
| Topbar demasiado pesado vs contenido | Medio | El topbar ocupa mucho espacio vertical sin densidad informativa |
| "Espacio de marca" en sidebar es placeholder | Bajo | Texto literal de desarrollo, no se reemplazó |
| Iconos todos iguales (mismo SVG para distintas secciones) | Bajo | `file` se usa para Servicios y Reportes simultáneamente |
| Márgenes del content area sin restricción de ancho máximo | Medio | El `children` se expande al 100% sin `max-width` ni padding lateral |

---

## Fase 1 — Nueva paleta de colores profesional

### Tokens CSS (`globals.css` — sección `:root`)

```
Modo oscuro (default)
─────────────────────────────────────────────────────
Superficie base          --bg:           #080F1A   (slate profundo)
Superficie suave         --bg-soft:      #0D1626   (panel secundario)
Panel principal          --panel:        rgba(13, 22, 38, 0.94)
Panel fuerte             --panel-strong: #111E33
Borde sutil              --line:         rgba(255,255,255,0.07)
Borde activo             --line-active:  rgba(99,179,237,0.25)

Texto principal          --text:         #E8F0FE
Texto secundario         --muted:        #8BA3C1
Texto desactivado        --disabled:     #4A6080

Acento primario          --primary:      #3B82F6   (blue-500 — acciones)
Acento fuerte            --primary-strong:#2563EB  (blue-600)
Acento suave             --primary-soft: rgba(59,130,246,0.12)

Acento seguridad         --security:     #10B981   (emerald-500 — brand NinjaSec)
Acento seguridad suave   --security-soft:rgba(16,185,129,0.12)

Peligro                  --danger:       #F87171   (red-400)
Advertencia              --warning:      #FBBF24   (amber-400)
Éxito                    --success:      #34D399   (emerald-400)
Info                     --info:         #60A5FA   (blue-400)

Sombra                   --shadow:       0 8px 32px rgba(0,0,0,0.4), 0 2px 8px rgba(0,0,0,0.2)
Sombra card              --shadow-card:  0 4px 16px rgba(0,0,0,0.3)
Focus ring               --focus:        rgba(59,130,246,0.45)

Sidebar width            --sidebar-w:    260px
Sidebar collapsed        --sidebar-w-sm: 72px
Topbar height            --topbar-h:     64px
```

### Paleta modo claro (`[data-theme="light"]`) — ajustar en paralelo

---

## Fase 2 — Mejoras de layout y espaciado

### `.admin-shell`
```css
/* Antes */
grid-template-columns: 260px 1fr;

/* Después — usar variable */
grid-template-columns: var(--sidebar-w) 1fr;
height: 100vh;           /* fijar al viewport */
overflow: hidden;        /* el scroll va en .workspace */
```

### `.workspace`
```css
.workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.workspace-content {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;    /* margen generoso lateral */
  max-width: 1400px;     /* ancho máximo para pantallas grandes */
  width: 100%;
  margin: 0 auto;        /* centrado en pantallas ultra-wide */
}
```

### `.topbar`
```css
height: var(--topbar-h);   /* fijo, no crece */
padding: 0 24px;
border-bottom: 1px solid var(--line);
background: rgba(8,15,26,0.85);
backdrop-filter: blur(16px);
position: sticky;
top: 0;
z-index: 20;
```

### `.sidebar`
```css
width: var(--sidebar-w);
height: 100vh;
position: sticky;
top: 0;
overflow-y: auto;
overflow-x: hidden;
border-right: 1px solid var(--line);
background: linear-gradient(160deg, #0D1626 0%, #080F1A 100%);
padding: 0;            /* mover padding a sub-secciones */
```

---

## Fase 3 — Reorganización del sidebar por rol

### Acceso por rol

| Módulo | super_admin | admin | collaborator | client |
|--------|:-----------:|:-----:|:------------:|:------:|
| Dashboard | ✅ | ✅ | ❌ | ❌ |
| Proyectos | ✅ | ✅ | ✅ (solo asignados) | ✅ (solo los suyos) |
| Clientes | ✅ | ✅ | ❌ | ❌ |
| Usuarios | ✅ | ✅ | ❌ | ❌ |
| Colaboradores | ✅ | ✅ | ❌ | ❌ |
| Integraciones | ✅ | ✅ | ❌ | ❌ |
| Dispositivos | ✅ | ✅ | ❌ | ❌ |
| Revisiones | ✅ | ✅ | ✅ (asignadas) | ❌ |
| Tickets | ✅ | ✅ | ✅ | ✅ |
| Reportes | ✅ | ✅ | ❌ | ✅ |
| Leads | ✅ | ✅ | ❌ | ❌ |
| Postulaciones | ✅ | ✅ | ✅ (la propia) | ❌ |
| Aprobaciones | ✅ | ✅ | ❌ | ❌ |
| Auditoria | ✅ | ❌ | ❌ | ❌ |
| Configuracion | ✅ | ✅ | ❌ | ❌ |
| Mi perfil | ❌ | ❌ | ✅ | ✅ |
| Skills/Certs | ❌ | ❌ | ✅ | ❌ |
| Documentos | ❌ | ❌ | ✅ | ✅ |

### Estructura de `navGroups` filtrada por rol

```typescript
// En sidebar.tsx
const NAV_CONFIG: Record<string, NavGroup[]> = {
  super_admin: [/* todos los grupos */],
  admin:       [/* operaciones, comercial, talento, control */],
  collaborator:[/* mi-trabajo, mi-perfil */],
  client:      [/* mis-proyectos, mis-tickets, mis-reportes */],
}
```

### Grupos admin/super_admin (rediseñados)
```
OPERACIONES
  ├── Dashboard        /dashboard
  ├── Proyectos        /dashboard/projects
  ├── Integraciones    /dashboard/integrations
  ├── Dispositivos     /dashboard/devices
  ├── Revisiones       /dashboard/security-reviews
  └── Tickets          /dashboard/support-tickets

CLIENTES
  ├── Clientes         /dashboard/clients
  ├── Leads            /dashboard/leads
  └── Servicios        /dashboard/services

TALENTO
  ├── Usuarios         /dashboard/users
  ├── Colaboradores    /dashboard/collaborators
  └── Postulaciones    /dashboard/applications

REPORTES Y CONTROL
  ├── Reportes         /dashboard/reports
  ├── Aprobaciones     /dashboard/approvals
  ├── Auditoria        /dashboard/audit (solo super_admin)
  └── Configuración    /dashboard/settings
```

### Grupos collaborator
```
MI TRABAJO
  ├── Proyectos        /portal/projects
  ├── Tickets          /portal/tickets
  └── Revisiones       /portal/reviews

MI PERFIL
  ├── Perfil           /portal/profile
  ├── Skills           /portal/profile#skills
  └── Certificaciones  /portal/profile#certifications
```

---

## Fase 4 — Mejoras visuales específicas

### Sidebar brand block
```
ANTES: "NS" + "NinjaSec" + "Backoffice" + "Espacio de marca" (placeholder)
DESPUÉS:
  - Logo círculo con gradiente #3B82F6 → #10B981
  - "NinjaSec" en bold
  - Badge de rol del usuario (ADMIN / SUPER ADMIN / etc.)
  - Footer del sidebar: avatar + nombre + botón logout (compacto)
```

### Nav items
```
ANTES: fondo plano, texto bold, icono pequeño
DESPUÉS:
  - padding: 10px 14px
  - border-radius: 10px
  - gap entre icono y texto: 10px
  - active: bg linear-gradient azul, borde izquierdo 3px verde security
  - hover: bg rgba(59,130,246,0.08)
  - transición: 150ms ease
  - iconos: Lucide React (ya instalado) — tamaño 16px, stroke-width 1.5
```

### Topbar
```
ANTES: título grande + subtítulo + acciones a la derecha
DESPUÉS:
  - Altura fija 64px
  - Breadcrumb compacto: eyebrow solo en mobile
  - Título h2 (font-size: 1.1rem, no 2rem)
  - Acciones: solo iconos relevantes a la página actual
  - User chip: avatar + nombre truncado + dropdown (logout)
```

### Content area
```
ANTES: children directo sin padding
DESPUÉS:
  - padding: 28px 32px
  - max-width: 1360px
  - Cada page-header con: título, subtítulo, acciones primarias
  - Cards con border-radius: 16px, shadow-card, border 1px line
```

### Tablas
```
ANTES: .table-base con colores planos
DESPUÉS:
  - Header: bg panel-strong, text muted uppercase 0.7rem
  - Row hover: bg rgba(59,130,246,0.04)
  - Row alt: bg rgba(255,255,255,0.015)
  - Bordes: solo horizontal, 1px line
  - Sticky header en tablas largas
```

---

## Archivos a modificar

| Archivo | Tipo de cambio |
|---------|---------------|
| `frontend/src/app/globals.css` | Nueva paleta + layout fixes + sidebar/topbar/tabla estilos |
| `frontend/src/components/dashboard/sidebar.tsx` | Role-aware nav, Lucide icons, brand block mejorado |
| `frontend/src/components/dashboard/topbar.tsx` | Altura fija, título compacto, user dropdown |
| `frontend/src/app/(admin)/dashboard/layout.tsx` | Agregar `.workspace-content` wrapper |
| `frontend/src/components/dashboard/portal-sidebar.tsx` | Misma mejora para el portal |

## Orden de implementación

1. `globals.css` — nueva paleta y tokens (base para todo lo demás)
2. `sidebar.tsx` — role-aware + estilos nuevos
3. `layout.tsx` — agregar `workspace-content` wrapper
4. `topbar.tsx` — altura fija + mejoras
5. `portal-sidebar.tsx` — paridad de estilos con admin sidebar
