# Menús editables por rol

Qué opciones ve cada rol en el sitio web, el panel del equipo y el portal, y
cómo se cambian sin tocar código.

## Qué controla, y qué no

Controla **qué se muestra**. **No es un permiso.** Quien conozca la dirección de
una página la abre igual si el backend no se lo impide, y lo que lo impide es
`require_roles` en cada endpoint.

Por eso cada opción declara `permitidas`: los roles a los que el backend **ya**
deja usar esa pantalla. El editor solo deja mostrar u ocultar **dentro** de ese
conjunto. Mostrarle «Leads» a un colaborador no serviría: vería el enlace y
recibiría un 403. Un menú que lleva a errores es peor que uno que no muestra la
opción.

## Tres superficies

| Superficie | Qué es | Audiencias |
| --- | --- | --- |
| `public` | La barra del sitio web | visitante |
| `staff` | El menú lateral de `/dashboard` | super_admin, admin, collaborator |
| `portal` | El menú lateral de `/portal` | client, collaborator, admin, super_admin |

## Cómo se guarda

La fuente de los valores por defecto es `backend/app/core/navegacion.py`, y
replica lo que antes estaba escrito en `sidebar.tsx`, `portal-sidebar.tsx` y
`site-header.tsx`. Sin ningún cambio guardado, **nadie nota nada**.

La tabla `nav_visibility` guarda solo las **excepciones**. Si una opción vuelve
a su valor por defecto, la fila se borra. Lleva `organization_id` y la
unicidad lo incluye: cada organización edita sus menús sin ver los de otra.

## Quién edita

Solo el **super_admin**, desde *Configuración → Menús por rol*
(`/dashboard/settings/menus`). Cada guardado queda en la auditoría
(`entity_type = nav_visibility`).

## Lo que el editor se niega a hacer

- Mostrar una opción a un rol al que el backend no se la deja usar (422).
- Ocultar **Login** a los visitantes, o **Configuración** al super_admin:
  dejaría a alguien sin forma de entrar o de deshacer el cambio.
- Aplicar un lote a medias: se valida todo antes de tocar nada.

## Cápsulas

Una opción atada a una cápsula apagada **no se muestra a nadie**, diga lo que
diga la configuración. Hoy `telemetria` agrupa Integraciones, Hardening,
Informe SOC y la página pública **Solución**.

Con `telemetria` apagada, además, la **portada**, el **encabezado** y el
**pie** dejan de prometer «reporting por API»: los conectores son simulados.
Hablan de lo que NinjaSec hace hoy, consultoría de infraestructura y
ciberseguridad. Al encender la cápsula vuelve el mensaje de plataforma.

Se retiraron además las cifras fijas de la portada (17 clientes, 73
dispositivos, 62 hallazgos, 28 revisiones): eran de la demo y estaban
escritas a mano.

## Pendiente

- **Un «colaborador admin».** Hoy cada usuario tiene un solo rol, así que esa
  combinación no existe. La vía limpia no es un quinto rol, sino un permiso
  «puede gestionar» por usuario. Queda para después de este cambio.
- **Menús por usuario**, no solo por rol.
- **Lo que no se puede hacer desde aquí:** abrir una pantalla a un rol cuyo
  endpoint no lo permite. Eso es un cambio de permisos, no de menú.
