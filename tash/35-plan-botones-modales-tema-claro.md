# Plan — Botones, Modales de Confirmación y Tema Claro

---

## Diagnóstico

### 1. Botones
| Problema | Causa |
|----------|-------|
| Hover de `.button-secondary` usa `rgba(31, 111, 235, 0.16)` hardcodeado | No usa variables CSS, rompe en tema claro |
| `.button-destructive` es demasiado sutil (solo borde) | No comunica peligro con suficiente fuerza |
| No existe `.button-sm` ni `.button-xs` | Tablas y filtros usan botones demasiado grandes |
| No existe `.button-success` | Acciones de aprobación usan primario azul |
| `border-radius: 14px` es demasiado grande para botones inline de tabla | Se ven como píldoras, no botones de acción |
| Hover no usa `transform` en secondary/ghost | Falta feedback táctil |

### 2. Modales y confirmaciones
| Problema | Causa |
|----------|-------|
| SweetAlert2 **ya está instalado** (`v11.26.24`) | No hay problema de librería |
| `confirmAction()` en `lib/alerts.ts` ya existe | No hay problema de implementación base |
| Falta `confirmDelete()` con botón rojo y ícono de trash | Solo hay `confirmAction()` genérico |
| El popup de Swal usa estilos por defecto que chocan con el tema | Faltan overrides CSS en `globals.css` |
| No hay `notifyWarning()` ni `notifyInfo()` | Solo success y error |
| El botón de confirmación en `confirmDelete` usa la misma clase `button-primary` (azul) que una acción normal | Debería ser rojo |

### 3. Tema claro
| Problema | Causa |
|----------|-------|
| Sidebar invisible o con texto ilegible | `--bg-soft: #E5ECF5` demasiado claro para el texto `--muted: #4A6080` |
| Botones con glassmorphism se ven raros | Los `rgba()` de fondos de botón no escalan bien con fondos blancos |
| SweetAlert2 muestra popup blanco sobre fondo blanco | No hay override del tema claro para Swal |
| `.nav-item-active` left border se pierde en blanco | El accent `--security` (#059669) tiene poco contraste sobre blanco |
| Cards y panels no tienen suficiente separación visual | Las sombras son muy suaves para tema claro |

---

## Plan de implementación

### Archivo 1: `globals.css` — Sección botones

**Cambios:**

```
.button               → padding más compacto (9px 16px), border-radius: 10px
.button-primary       → usar vars, glow sutil actualizado
.button-secondary     → hover usa var(--primary-soft), no hardcoded
.button-ghost         → hover: bg var(--row-hover)
.button-destructive   → NUEVO: rojo sólido (para usar en tablas como icono)

NUEVOS:
.button-danger        → rojo filled (Eliminar, con texto)
.button-success       → verde filled (Aprobar)
.button-warning       → ámbar filled (Advertencia)
.button-sm            → padding 6px 12px, font-size 0.82rem, border-radius: 8px
.button-xs            → padding 4px 8px, font-size 0.75rem, border-radius: 6px
.button-icon-sm       → 30px × 30px, solo ícono
```

### Archivo 2: `globals.css` — Sección SweetAlert2 overrides

**Nuevas reglas CSS:**

```css
/* Dark mode (default) */
.swal2-popup          → bg var(--panel-strong), border var(--line), shadow
.swal2-title          → color var(--text), font-size 1.1rem
.swal2-html-container → color var(--muted), font-size 0.9rem
.swal2-icon           → bordes con colores semánticos
.swal2-actions        → gap 10px
/* Los botones ya usan .button .button-primary via customClass */

/* Tema claro: mismo popup con fondo blanco */
[data-theme="light"] .swal2-popup → bg white, border sutil
```

### Archivo 3: `globals.css` — Tema claro fixes

**Cambios específicos:**

```css
[data-theme="light"] {
  /* Sidebar */
  background: linear-gradient(160deg, #E8EFF8 0%, #F0F4FA 100%);
  
  /* Nav items */
  .nav-item-active → bg var(--primary-soft), left border --primary (azul en claro)
  
  /* Cards */
  --shadow: 0 2px 16px rgba(0,0,0,0.10) — más pronunciada
  
  /* Topbar */
  background: rgba(248, 250, 253, 0.90)
}
```

### Archivo 4: `lib/alerts.ts` — Nuevas funciones

**Agregar:**

```typescript
export async function confirmDelete(title?, text?) {
  // Usa .button-danger como confirmButton
  // ícono: warning con color rojo
  // texto por defecto: "Esta acción eliminará el registro permanentemente."
}

export async function confirmApprove(title?, text?) {
  // Usa .button-success como confirmButton
  // ícono: question con color verde
}

export function notifyWarning(title, text?) { }
export function notifyInfo(title, text?) { }
```

---

## Orden de implementación

1. `globals.css` — Botones (sección independiente)
2. `globals.css` — SweetAlert2 overrides (nuevas reglas al final del archivo)
3. `globals.css` — Tema claro fixes (actualizar variables de `[data-theme="light"]`)
4. `lib/alerts.ts` — Nuevas funciones (+ fix `baseAlert` para que lea vars actualizadas)

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `frontend/src/app/globals.css` | Botones + Swal overrides + tema claro |
| `frontend/src/lib/alerts.ts` | `confirmDelete`, `confirmApprove`, `notifyWarning`, `notifyInfo` |
