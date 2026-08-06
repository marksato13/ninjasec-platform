# Flujo: Onboarding de Nuevo Cliente

---

## Descripción

Proceso completo para dar de alta a una nueva empresa cliente desde que firma el contrato hasta que su equipo accede al portal.

---

## Actores

| Actor | Rol |
|-------|-----|
| Líder comercial | Cierra el deal y entrega el lead a operaciones |
| Gerente de operaciones | Crea el cliente en el sistema |
| Ingeniero responsable | Configura las integraciones |
| Personal TI del cliente | Usuario final del portal |

---

## Pasos del flujo

```
1. LEAD GANADO
   ↓
   En módulo Leads: marcar como CLOSED_WON

2. CREAR CLIENTE
   ↓
   Admin va a /dashboard/clients → "Nuevo cliente"
   Ingresa: nombre empresa, sector, país, contacto principal

3. CONFIGURAR INTEGRACIÓN(ES)
   ↓
   Admin va a /dashboard/integrations → "Nueva integración"
   Por cada sede del cliente:
   - Tipo: pfSense o FortiGate
   - Ambiente: producción / DR / staging
   - Fecha de vencimiento de licencia
   - Técnico responsable

4. AGREGAR DISPOSITIVOS
   ↓
   Admin o collaborator va a /dashboard/devices
   Por cada activo del cliente:
   - Nombre e IP
   - Tipo (firewall, switch, server, etc.)
   - Integración a la que pertenece
   - Estado inicial: active

5. CREAR USUARIO PORTAL
   ↓
   Admin va a /dashboard/users → "Nuevo usuario"
   - Email del responsable TI del cliente
   - Rol: client
   - Vincular al cliente correcto
   - El usuario recibe sus credenciales por email

6. PRIMERA REVISIÓN DE SEGURIDAD
   ↓
   Admin crea una revisión en /dashboard/security-reviews
   - Estado: scheduled
   - Asignada al cliente y consola recién configurada
   - Asigna técnico responsable

7. COMPARTIR DOCUMENTOS INICIALES
   ↓
   Admin sube los documentos iniciales al portal:
   - Contrato firmado
   - Manual de uso del portal
   - Presentación del equipo NinjaSec

8. VERIFICACIÓN
   ↓
   El responsable TI del cliente hace login en:
   http://localhost:3018/portal
   Email: ti@[empresa].ninjasec.local
   Pass: [enviada por email seguro]
```

---

## Checklist de verificación

- [ ] Cliente creado en el sistema
- [ ] Al menos 1 integración configurada
- [ ] Dispositivos cargados en inventario
- [ ] Usuario portal creado y credenciales enviadas
- [ ] Primera revisión agendada
- [ ] Documentos iniciales subidos al portal
- [ ] Cliente puede hacer login y ve su inventario

---

## Tiempo estimado

| Paso | Tiempo |
|------|--------|
| Crear cliente | 5 min |
| Configurar integraciones | 15 min por sede |
| Cargar dispositivos | 20-60 min según cantidad |
| Crear usuario | 2 min |
| Primera revisión | 10 min (agendar) |
| **Total mínimo** | **~1 hora** |
