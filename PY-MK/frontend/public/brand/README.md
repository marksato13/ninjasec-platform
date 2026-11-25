# Marca Ninja Tech: recursos para la web

Versiones **optimizadas** (WebP) del kit de marca. Los originales, con nombres descriptivos y un índice,
están en el repositorio privado de la empresa (`MARKETING/brand-kit/ninja-tech/`); no se versionan aquí
porque pesan 31 MB y incluyen material de redes que no es del sitio.

Marca general **Ninja Tech**, con dos áreas activas, **Ninja Sec** y **Ninja Dev**. La mascota es **Kuro**.

## Qué hay y dónde se usa

| Archivo | Tamaño | Se usa en |
|---|---|---|
| `icono-cabeza.webp` | 256 px | Marca de la cabecera pública |
| `logo-ninja-tech.webp` | 720 px | Pie de página |
| `avatar-ninja-sec.webp` | 320 px | Tarjeta de Ninja Sec en la portada |
| `avatar-ninja-dev.webp` | 320 px | Tarjeta de Ninja Dev en la portada |
| `avatar-ninja-tech.webp`, `avatar-general.webp` | 320 px | Reservados (redes y comunidad) |
| `poses/tech-escudo-ventana.webp` | 520 px | Portada (hero) |
| `poses/*` (las otras 6) | 520 px | Reservadas para Servicios, Proyectos, Contacto y Colabora |
| `anim/busca-404.webp` | 240 px | Página 404 |
| `anim/celebra-envio.webp` | 240 px | Formulario de contacto al enviarse |
| `anim/seguridad.webp`, `anim/desarrollo.webp` | 300 px | Tarjetas de Ninja Sec y Ninja Dev |
| `anim/saludo.webp`, `anim/senala-proyecto.webp`, `anim/caminando.webp`, `anim/cruzando.webp` | 240–640 px | Reservadas |

## Reglas

- **Las animadas van con `unoptimized`** en `next/image`: el optimizador de Next no soporta WebP animado.
- **Respetan «reducir movimiento»:** `.branch-card__anim` se oculta con `prefers-reduced-motion`. Una animación
  nueva debe hacer lo mismo o no ser esencial.
- Escribe siempre «Ninja Tech», «Ninja Sec» y «Ninja Dev», con espacio.
- No sirvas aquí los originales de 1,4 MB. Para regenerar una versión, parte del original del repo privado.
