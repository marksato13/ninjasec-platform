# Checklist operativo previo a Fase 2.2 (ESXi VMs)

## Objetivo

Antes de crear las VMs `ninjasec-web` y `ninjasec-db`, validar que pfSense ya tiene listas las VLANs, gateways, DHCP (si aplica) y reglas base.

## Decision recomendada de direccionamiento

Para este escenario, la recomendacion es:

- `ninjasec-web` -> IP estatica en `VLAN20`
- `ninjasec-db` -> IP estatica en `VLAN30`
- `ninjasec-runner` -> IP estatica en `VLAN20`

IPs previstas en el plan:

- `ninjasec-web` -> `192.168.10.4`
- `ninjasec-runner` -> `192.168.10.6`
- `ninjasec-db` -> `172.16.30.5`

## Que verificar en pfSense antes de crear VMs

### 1. Interfaces VLAN creadas

Debes verificar que existan en pfSense:

- `VLAN20` sobre el trunk correcto
- `VLAN30` sobre el trunk correcto

Y que ambas esten asignadas como interfaces.

### 2. IP de gateway de cada VLAN

Verificar que pfSense tenga estas IPs en sus interfaces:

- `VLAN20` -> `192.168.10.1/24`
- `VLAN30` -> `172.16.30.1/24`

Estas IPs seran los gateways de las VMs.

### 3. DHCP o estatico

Para servidores, usar estatico.

Por lo tanto:

- No dependes de DHCP para `web`, `db` ni `runner`
- Si habilitas DHCP en VLAN20/VLAN30, que sea solo para pruebas o futuros hosts no criticos

### 4. Si dejas DHCP habilitado, revisar rango

Asegurate de que el pool DHCP NO choque con las IPs fijas.

Ejemplo seguro:

- VLAN20 DHCP: `192.168.10.100 - 192.168.10.199`
- VLAN30 DHCP: `172.16.30.100 - 172.16.30.199`

Reservar fuera de ese rango:

- `192.168.10.4`
- `192.168.10.6`
- `172.16.30.5`

### 5. Reglas de firewall minimas

#### VLAN20

- permitir salida a Internet
- permitir `192.168.10.4 -> 172.16.30.5:5432`
- bloquear `VLAN20 -> VLAN10`
- bloquear `VLAN20 -> VLAN40`

#### VLAN10

- permitir `192.168.1.0/24 -> 192.168.10.4:22`
- permitir `192.168.1.0/24 -> 192.168.10.6:22`
- permitir `192.168.1.0/24 -> 172.16.30.5:22`

#### VLAN30

- no hace falta abrir entrada amplia
- solo confirmar retorno y acceso desde web VM a `5432`

### 6. DNS y salida

Desde cada VLAN debe haber salida DNS/Internet si vas a:

- instalar paquetes Ubuntu
- instalar Docker
- registrar runner con GitHub
- usar DuckDNS
- obtener certificados Let's Encrypt

## Secuencia recomendada

1. Verificar VLAN20 y VLAN30 en pfSense
2. Verificar IPs gateway `.1`
3. Decidir si DHCP queda deshabilitado o solo para clientes no criticos
4. Reservar/excluir IPs fijas del plan
5. Verificar reglas base de firewall
6. Recién ahi crear VMs en ESXi
