---
name: ninjasec-multitenant
description: Reglas de aislamiento multi-tenant de NinjaSec — filtrar por organization_id y devolver 404 y no 403. Usar al escribir o revisar cualquier ruta protegida, consulta, modelo o migración que tenga que ver con organizaciones, clientes, sedes, dispositivos o datos de un tenant.
---

# Aislamiento multi-tenant en NinjaSec

`organization_id` está en **18 de las 68 tablas**. Las otras 50 o no tienen
tenant por diseño, o lo derivan por una clave foránea — y ahí es donde
aparecen las fugas.

## La regla

De `AGENTS.md`, literal:

> *Toda ruta protegida valida rol y `organization_id`; datos de otro tenant
> devuelven **404** para no confirmar su existencia.*

Un `403` es un fallo. Dice *«existe, pero no es tuyo»*, y eso ya es
información que el otro cliente no debería tener.

## El patrón correcto

Una función guardia que hace el cruce y lanza 404:

```python
def _cliente_de_mi_org(client_id: int, org_id: int, db: Session) -> Client:
    cliente = db.get(Client, client_id)
    if not cliente or cliente.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Client not found")
    return cliente
```

Y cuando el tenant está a dos saltos, el `join` va en la consulta, no en
Python:

```python
contacto = db.scalar(
    select(ClientContact)
    .join(Client, Client.id == ClientContact.client_id)
    .where(ClientContact.id == contact_id, Client.organization_id == org_id)
)
```

## Los antipatrones, con nombre y apellido

**1. Permiso que empieza en `True`.** Ya costó una fuga en
`connection_service.py`. Lo correcto es empezar en `False`:

```python
permitido = False
if integration and integration.organization_id == org_id:
    permitido = True
elif site and site.client and site.client.organization_id == org_id:
    permitido = True
if not permitido:
    raise HTTPException(status_code=404, ...)
```

**2. Unicidad global en una tabla con tenant.** `services.slug` era único
en toda la tabla: el cliente A le impedía al B usar ese nombre y, de paso,
le confirmaba que existía. Lo correcto:

```python
__table_args__ = (
    UniqueConstraint("organization_id", "slug", name="uq_service_org_slug"),
    Index("ix_services_org", "organization_id"),
)
```

**3. Listado sin filtro.** Un `select(Modelo)` sin `.where(... == org_id)`
en una tabla con tenant es una fuga, aunque la interfaz no la enseñe hoy.

**4. Tenant derivado de claves foráneas nulables.** `devices` deduce su
organización de un `OR` entre dos claves foráneas **ambas nulables**. Si las
dos son nulas, el registro no tiene dueño y se cuela en cualquier filtro mal
escrito. Sigue abierto.

## Lo que sigue roto a esta fecha

| Qué | Consecuencia |
| --- | --- |
| `devices` sin `organization_id` propio | Tenant por `OR` de dos claves nulables |
| `job_applications` sin `organization_id` | Datos personales de candidatos, globales |

Las dos son clase **T4**. No se delegan.

## Falsos positivos

- Las rutas **públicas** —alta de leads, de postulaciones, el portal
  público— no tienen tenant por diseño.
- Un `super_admin` ve varias organizaciones. Eso es correcto: lo que se
  verifica es que el filtro **exista**, no que siempre recorte.

## Cómo se comprueba

El subagente `ns-auditor-tenant` hace esta auditoría completa y no puede
arreglar nada, que es justo lo que se quiere de un auditor.

Para una comprobación rápida de una ruta concreta: pídela con un usuario de
otra organización y confirma que el código es **404** y que el cuerpo no
revela nada.
