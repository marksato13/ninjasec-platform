"""Contenido de los planes de estudio: Fortinet NSE 4 y Cisco CCNA.

Separado de `seed.py` a propósito: esto es **contenido**, no datos de
prueba. Se puede volver a ejecutar cuando el temario cambie, sin arrastrar
los 11 usuarios de demostración ni los clientes.

Es idempotente: busca por `(organization_id, slug)` y actualiza en vez de
duplicar.

Cada módulo lleva tres cosas que no suelen estar juntas en un temario:

1. **Un objetivo que se puede demostrar.** No «conocer las políticas de
   firewall», sino «escribir una política que haga X y comprobar que el
   tráfico Y la atraviesa». Un objetivo que no se puede demostrar no sirve
   para medir progreso.
2. **El laboratorio que lo demuestra.** Ni NSE 4 ni CCNA se aprueban
   leyendo.
3. **El peso en el examen real**, cuando el fabricante lo publica. Es lo que
   permite decidir dónde meter las horas cuando van justas.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.organization import Organization
from app.db.models.study_plan import StudyModule, StudyPlan


# --------------------------------------------------------------------------
# Fortinet NSE 4 — FortiGate Security + Infrastructure
# --------------------------------------------------------------------------

NSE4 = {
    "name": "Fortinet NSE 4 — FortiGate Security e Infrastructure",
    "slug": "fortinet-nse4",
    "area": "Ciberseguridad",
    "vendor": "Fortinet",
    "exam_code": "NSE4_FGT",
    "target_certification": "Fortinet NSE 4 Network Security Professional",
    "estimated_hours": None,  # se calcula desde los modulos
    "description": (
        "La certificación de FortiGate que de verdad se pide en el mercado "
        "peruano. Son dos cursos en un examen: Security (lo que atraviesa el "
        "cortafuegos) e Infrastructure (cómo se enruta, se agrupa y se "
        "sostiene). El examen es de producto: pregunta por el comportamiento "
        "real de FortiOS, no por teoría de redes."
    ),
    "modules": [
        {
            "title": "Configuración inicial y administración de FortiOS",
            "objective": (
                "Dejar un FortiGate recién sacado de la caja operativo: "
                "interfaces, administradores, perfiles de acceso y respaldo "
                "de configuración restaurado y comprobado."
            ),
            "topics": (
                "Modos NAT y Transparente\n"
                "Interfaces: físicas, VLAN, agregadas, zonas\n"
                "Administradores y perfiles de acceso (trusted hosts)\n"
                "Respaldo y restauración de configuración\n"
                "Registro del dispositivo y licencias de FortiGuard\n"
                "Actualización de firmware y plan de vuelta atrás"
            ),
            "lab": (
                "Levantar un FortiGate VM, configurar WAN y LAN, crear un "
                "administrador de solo lectura restringido por trusted host, "
                "hacer respaldo, cambiar algo y restaurar."
            ),
            "estimated_hours": 8,
        },
        {
            "title": "Políticas de cortafuegos",
            "objective": (
                "Escribir una política que permita exactamente el tráfico "
                "pedido y demostrar con el registro que lo que no está "
                "permitido se deniega."
            ),
            "topics": (
                "Orden de evaluación: de arriba abajo, primera coincidencia\n"
                "Objetos: direcciones, grupos, servicios, horarios\n"
                "Política implícita de denegación\n"
                "Sesiones y tabla de sesiones\n"
                "Interfaces ANY y por qué conviene evitarlas\n"
                "Policy lookup como herramienta de diagnóstico"
            ),
            "lab": (
                "Permitir solo HTTPS saliente desde una subred, denegar el "
                "resto, y demostrarlo con `diagnose sniffer packet` y el "
                "registro de tráfico."
            ),
            "estimated_hours": 10,
        },
        {
            "title": "NAT: origen y destino",
            "objective": (
                "Publicar un servicio interno hacia Internet y explicar qué "
                "dirección ve el servidor de destino en cada caso."
            ),
            "topics": (
                "SNAT: por interfaz y con IP Pool\n"
                "DNAT: Virtual IP y VIP de rango\n"
                "Central NAT frente a NAT por política\n"
                "Port forwarding\n"
                "Hairpin NAT, el que siempre se olvida\n"
                "Orden: la política decide, el NAT traduce"
            ),
            "lab": (
                "Publicar un servidor web interno con una VIP, comprobar que "
                "responde desde fuera, y que desde dentro también funciona "
                "(hairpin)."
            ),
            "estimated_hours": 10,
        },
        {
            "title": "Autenticación de usuarios",
            "objective": (
                "Hacer que una política se aplique a una persona y no a una "
                "dirección IP."
            ),
            "topics": (
                "Usuarios locales y grupos\n"
                "Servidores remotos: LDAP, RADIUS\n"
                "Autenticación activa (portal) y pasiva (FSSO)\n"
                "FSSO: agente en el controlador de dominio y modo polling\n"
                "Dos factores con FortiToken\n"
                "Portal cautivo para invitados"
            ),
            "lab": (
                "Integrar con un LDAP, crear un grupo y una política que solo "
                "ese grupo atraviese. Comprobar qué pasa con un usuario fuera "
                "del grupo."
            ),
            "estimated_hours": 10,
        },
        {
            "title": "Perfiles de seguridad: antivirus, web filter y control de aplicaciones",
            "objective": (
                "Aplicar inspección al tráfico y demostrar que bloquea lo "
                "esperado sin romper lo que no debe tocar."
            ),
            "topics": (
                "Antivirus: modos proxy y flow, y en qué se diferencian\n"
                "Web filter por categoría de FortiGuard y por URL\n"
                "Control de aplicaciones y su relación con el web filter\n"
                "DNS filter\n"
                "Perfiles por política, no globales\n"
                "Qué hace el modo monitor y por qué conviene empezar ahí"
            ),
            "lab": (
                "Bloquear una categoría, comprobar la página de bloqueo, "
                "poner una excepción por URL y verificar que la excepción "
                "gana."
            ),
            "estimated_hours": 12,
        },
        {
            "title": "Inspección SSL/TLS",
            "objective": (
                "Explicar por qué sin inspección profunda la mitad de los "
                "perfiles de seguridad no ven nada, y montarla sin romper el "
                "navegador."
            ),
            "topics": (
                "Certificate inspection frente a deep inspection\n"
                "El FortiGate como autoridad certificadora intermedia\n"
                "Distribuir el certificado a los clientes\n"
                "Exenciones: banca, salud, actualizaciones del sistema\n"
                "Certificate pinning: por qué algunas aplicaciones fallan\n"
                "Implicaciones legales y de privacidad de abrir el tráfico"
            ),
            "lab": (
                "Activar deep inspection, instalar el certificado en un "
                "equipo, comprobar que el antivirus ya detecta un EICAR "
                "descargado por HTTPS, y añadir una exención."
            ),
            "estimated_hours": 10,
        },
        {
            "title": "Enrutamiento",
            "objective": (
                "Hacer que el tráfico salga por donde debe y diagnosticar "
                "cuándo no lo hace."
            ),
            "topics": (
                "Rutas estáticas, distancia y prioridad\n"
                "ECMP y cómo se reparte\n"
                "Policy routes: se evalúan ANTES que la tabla de rutas\n"
                "Reverse Path Forwarding: estricto y laxo\n"
                "OSPF básico: áreas, vecinos, redistribución\n"
                "`get router info routing-table` y `diagnose ip route list`"
            ),
            "lab": (
                "Dos salidas a Internet, una con más prioridad. Tirar la "
                "principal y comprobar el failover. Luego una policy route "
                "que mande un origen concreto por la secundaria."
            ),
            "estimated_hours": 12,
        },
        {
            "title": "VPN IPsec sitio a sitio",
            "objective": (
                "Levantar un túnel entre dos sedes y diagnosticarlo cuando no "
                "sube."
            ),
            "topics": (
                "IKEv1 e IKEv2: fase 1 y fase 2\n"
                "Modo túnel y modo interfaz (la que usa FortiGate)\n"
                "Selectores de tráfico y por qué fallan\n"
                "Políticas y rutas que el túnel necesita\n"
                "NAT traversal, DPD y keepalives\n"
                "`diagnose vpn ike log-filter` y `diagnose debug app ike`"
            ),
            "lab": (
                "Túnel entre dos FortiGate VM, ping entre LAN, y luego "
                "romperlo a propósito (desajuste de propuesta) para leer el "
                "error en el debug."
            ),
            "estimated_hours": 12,
        },
        {
            "title": "SSL VPN para acceso remoto",
            "objective": (
                "Dar acceso remoto a un grupo concreto, con portal y con "
                "cliente, y limitar a qué puede llegar."
            ),
            "topics": (
                "Modo web (portal) y modo túnel\n"
                "Portales por grupo de usuarios\n"
                "Rango de direcciones y rutas que se empujan\n"
                "Split tunneling: cuándo sí y cuándo no\n"
                "Host check y comprobación del equipo\n"
                "Diagnóstico: `diagnose vpn ssl list`"
            ),
            "lab": (
                "SSL VPN en modo túnel con FortiClient, split tunneling "
                "activado, y una política que solo deje llegar a un servidor."
            ),
            "estimated_hours": 8,
        },
        {
            "title": "Dominios virtuales (VDOM)",
            "objective": (
                "Partir un FortiGate en varios cortafuegos lógicos y explicar "
                "cuándo compensa."
            ),
            "topics": (
                "VDOM en modo split-task y multi-vdom\n"
                "VDOM de gestión y VDOM root\n"
                "Enlaces entre VDOM (inter-VDOM links)\n"
                "Recursos globales frente a por VDOM\n"
                "Administradores con ámbito de VDOM\n"
                "Cuándo NO usar VDOM: casi siempre que baste con zonas"
            ),
            "lab": (
                "Dos VDOM con un enlace entre ellos, políticas en cada uno, y "
                "un administrador que solo ve uno."
            ),
            "estimated_hours": 8,
        },
        {
            "title": "Alta disponibilidad (FGCP)",
            "objective": (
                "Montar un clúster y provocar un failover sin perder las "
                "sesiones."
            ),
            "topics": (
                "Activo-pasivo y activo-activo\n"
                "Elección del primario: override, prioridad, número de serie\n"
                "Sincronización de sesiones y de configuración\n"
                "Monitorización de interfaces y failover por enlace caído\n"
                "Heartbeat: interfaces dedicadas\n"
                "`get system ha status` y `diagnose sys ha checksum show`"
            ),
            "lab": (
                "Clúster de dos FortiGate VM activo-pasivo, mantener un ping "
                "y tirar el primario para medir la pérdida."
            ),
            "estimated_hours": 8,
        },
        {
            "title": "SD-WAN",
            "objective": (
                "Repartir el tráfico entre varios enlaces según calidad, no "
                "solo según prioridad."
            ),
            "topics": (
                "Miembros, zonas y reglas\n"
                "Performance SLA: latencia, jitter, pérdida\n"
                "Estrategias: manual, best quality, lowest cost\n"
                "Reglas por aplicación\n"
                "Relación con las rutas estáticas y con ECMP\n"
                "`diagnose sys sdwan health-check`"
            ),
            "lab": (
                "Dos enlaces con SLA. Degradar uno (añadir latencia) y "
                "comprobar que el tráfico se mueve solo."
            ),
            "estimated_hours": 8,
        },
        {
            "title": "Registro, monitorización y Security Fabric",
            "objective": (
                "Saber dónde mirar cuando algo falla, antes de que un cliente "
                "lo pregunte."
            ),
            "topics": (
                "Tipos de registro: tráfico, evento, UTM\n"
                "Destinos: memoria, disco, FortiAnalyzer, syslog\n"
                "Qué NO registrar y por qué: volumen y privacidad\n"
                "Security Fabric: raíz, hojas y topología\n"
                "Automation stitches\n"
                "Informes y su valor comercial para un MSP"
            ),
            "lab": (
                "Enviar registros a un syslog, generar tráfico bloqueado y "
                "encontrarlo. Montar un stitch que avise por correo."
            ),
            "estimated_hours": 8,
        },
        {
            "title": "Diagnóstico: el módulo que decide el examen y el trabajo",
            "objective": (
                "Ante «no funciona», llegar a la causa con comandos, no con "
                "conjeturas."
            ),
            "topics": (
                "`diagnose debug flow`: la herramienta más útil de FortiOS\n"
                "`diagnose sniffer packet` con sus niveles de verbosidad\n"
                "Tabla de sesiones: `diagnose sys session list|filter`\n"
                "Policy lookup\n"
                "`execute ping-options` y `execute traceroute`\n"
                "Método: de abajo arriba, y descartar antes de cambiar"
            ),
            "lab": (
                "Que alguien te rompa una configuración sin decirte qué, y "
                "encontrarlo solo con comandos de diagnóstico. Cronometrarlo."
            ),
            "estimated_hours": 10,
        },
    ],
}


# --------------------------------------------------------------------------
# Cisco CCNA 200-301
# --------------------------------------------------------------------------

CCNA = {
    "name": "Cisco CCNA 200-301",
    "slug": "cisco-ccna-200-301",
    "area": "Redes",
    "vendor": "Cisco",
    "exam_code": "200-301",
    "target_certification": "Cisco Certified Network Associate (CCNA)",
    "estimated_hours": None,  # se calcula desde los modulos
    "description": (
        "La base sobre la que se apoya todo lo demás. Los pesos de cada "
        "dominio son los que publica Cisco para el examen 200-301, y están "
        "aquí para decidir dónde meter las horas: Network Access e IP "
        "Connectivity son el 45% entre los dos."
    ),
    "modules": [
        {
            "title": "Fundamentos: componentes, topologías y cableado",
            "objective": (
                "Explicar qué hace cada dispositivo de una red y por qué el "
                "tráfico pasa por donde pasa."
            ),
            "topics": (
                "Router, switch, firewall, AP, controlador\n"
                "Topologías: estrella, malla, tres capas, spine-leaf\n"
                "Cobre, fibra monomodo y multimodo\n"
                "Modelo OSI y TCP/IP: qué capa resuelve qué\n"
                "Dúplex, velocidad y errores de autonegociación\n"
                "Dónde empieza y acaba un dominio de colisión y uno de difusión"
            ),
            "lab": (
                "Montar en Packet Tracer o GNS3 una topología de tres capas y "
                "seguir un paquete de extremo a extremo."
            ),
            "estimated_hours": 10,
            "weight_percent": 20,
        },
        {
            "title": "Direccionamiento IPv4 y subredes",
            "objective": (
                "Subnetear de cabeza, sin calculadora, en menos de un minuto. "
                "Es lo que más se pregunta y lo que más tiempo quita en el "
                "examen si no está automatizado."
            ),
            "topics": (
                "Clases, CIDR y máscaras de longitud variable\n"
                "Cálculo de red, difusión y rango útil\n"
                "VLSM: repartir un bloque según necesidad real\n"
                "Sumarización de rutas\n"
                "Direcciones privadas, APIPA, loopback\n"
                "El atajo: potencias de 2 y la tabla de bloques"
            ),
            "lab": (
                "50 ejercicios de subnetting cronometrados. Objetivo: 30 "
                "segundos cada uno."
            ),
            "estimated_hours": 14,
        },
        {
            "title": "IPv6",
            "objective": (
                "Direccionar y enrutar IPv6 sin tratarlo como «IPv4 con más "
                "dígitos»."
            ),
            "topics": (
                "Formato, abreviación y prefijos\n"
                "Tipos: global unicast, link-local, unique local, multicast\n"
                "EUI-64 y direcciones aleatorias\n"
                "SLAAC, DHCPv6 con y sin estado\n"
                "NDP: sustituye a ARP\n"
                "Rutas estáticas IPv6"
            ),
            "lab": (
                "Direccionar una topología solo con IPv6 y hacer ping de "
                "extremo a extremo."
            ),
            "estimated_hours": 8,
        },
        {
            "title": "Conmutación: VLAN, trunking e inter-VLAN",
            "objective": (
                "Segmentar una red y hacer que las VLAN se hablen solo donde "
                "deben."
            ),
            "topics": (
                "VLAN, puertos de acceso y troncales\n"
                "802.1Q y VLAN nativa (y su riesgo)\n"
                "DTP y por qué conviene desactivarlo\n"
                "Router-on-a-stick y SVI en switch de capa 3\n"
                "VTP: qué es y por qué casi nadie lo usa ya\n"
                "Diagnóstico: `show vlan brief`, `show interfaces trunk`"
            ),
            "lab": (
                "Tres VLAN, un troncal, inter-VLAN por SVI. Luego romper la "
                "VLAN nativa en un extremo y ver qué ocurre."
            ),
            "estimated_hours": 12,
            "weight_percent": 20,
        },
        {
            "title": "Spanning Tree y EtherChannel",
            "objective": (
                "Explicar por qué un bucle tumba una red entera y cómo STP lo "
                "evita."
            ),
            "topics": (
                "STP, RSTP y PVST+\n"
                "Elección de raíz, puertos raíz, designados y bloqueados\n"
                "PortFast, BPDU Guard, Root Guard\n"
                "Forzar la raíz: prioridad, no suerte\n"
                "EtherChannel: LACP, PAgP y estático\n"
                "Por qué un EtherChannel mal formado crea un bucle"
            ),
            "lab": (
                "Dos switches con dos enlaces. Ver STP bloquear uno. Luego "
                "agruparlos en EtherChannel y ver que los dos pasan a usarse."
            ),
            "estimated_hours": 12,
        },
        {
            "title": "Enrutamiento estático y OSPF",
            "objective": (
                "Hacer que dos redes se vean, primero a mano y luego con un "
                "protocolo, y saber leer la tabla de rutas."
            ),
            "topics": (
                "Tabla de rutas: cómo se elige (longest match, AD, métrica)\n"
                "Rutas estáticas, por defecto y flotantes\n"
                "OSPFv2 de área única: vecindad, DR/BDR, LSA\n"
                "Router ID y por qué conviene fijarlo\n"
                "Tipos de red OSPF: broadcast y point-to-point\n"
                "`show ip route`, `show ip ospf neighbor`"
            ),
            "lab": (
                "Topología de cuatro routers con OSPF. Tirar un enlace y "
                "medir cuánto tarda en converger."
            ),
            "estimated_hours": 16,
            "weight_percent": 25,
        },
        {
            "title": "Redes inalámbricas",
            "objective": (
                "Explicar cómo se conecta un AP a un controlador y qué cambia "
                "respecto a una red cableada."
            ),
            "topics": (
                "Bandas, canales y solapamiento (1, 6, 11)\n"
                "SSID, BSSID, ESS\n"
                "AP autónomos, ligeros y controlador (WLC)\n"
                "CAPWAP: plano de control y de datos\n"
                "WPA2 y WPA3, personal y empresarial\n"
                "Configuración de una WLAN desde la interfaz del WLC"
            ),
            "lab": (
                "Configurar una WLAN en un WLC simulado con WPA2-Enterprise "
                "contra RADIUS."
            ),
            "estimated_hours": 10,
        },
        {
            "title": "Servicios IP: NAT, DHCP, NTP, syslog y QoS",
            "objective": (
                "Montar los servicios sin los que una red funciona en el "
                "laboratorio y falla en producción."
            ),
            "topics": (
                "NAT estático, dinámico y PAT\n"
                "DHCP: servidor, relay (`ip helper-address`), reservas\n"
                "NTP y por qué sin hora sincronizada los registros no sirven\n"
                "Syslog: niveles de severidad\n"
                "SNMP v2c frente a v3\n"
                "QoS: clasificación, marcado, colas, shaping y policing"
            ),
            "lab": (
                "PAT hacia Internet, DHCP con relay desde otra VLAN, y "
                "comprobar que los registros llevan la hora correcta."
            ),
            "estimated_hours": 12,
            "weight_percent": 10,
        },
        {
            "title": "Seguridad: ACL, port security y acceso al dispositivo",
            "objective": (
                "Aplicar control de acceso donde toca y endurecer el equipo "
                "antes de ponerlo en producción."
            ),
            "topics": (
                "ACL estándar y extendida, numeradas y nombradas\n"
                "Dónde se aplica cada una y por qué\n"
                "La denegación implícita del final\n"
                "Port security: modos y violaciones\n"
                "DHCP snooping y Dynamic ARP Inspection\n"
                "AAA, SSH en vez de Telnet, contraseñas cifradas"
            ),
            "lab": (
                "ACL extendida que deje pasar solo lo pedido. Port security "
                "en modo restrict y provocar una violación."
            ),
            "estimated_hours": 12,
            "weight_percent": 15,
        },
        {
            "title": "Automatización y programabilidad",
            "objective": (
                "Entender por qué el examen pregunta esto y en qué cambia el "
                "trabajo diario."
            ),
            "topics": (
                "Configuración manual frente a basada en intención\n"
                "JSON, XML y YAML: leerlos sin dudar\n"
                "API REST: métodos, códigos de estado, autenticación\n"
                "Ansible, Puppet y Chef: en qué se diferencian\n"
                "SDN: separación de planos, controlador\n"
                "Cisco DNA Center: qué hace, a alto nivel"
            ),
            "lab": (
                "Leer un JSON de configuración y escribir un playbook de "
                "Ansible que configure una VLAN en dos switches."
            ),
            "estimated_hours": 10,
            "weight_percent": 10,
        },
        {
            "title": "Simulacros y gestión del tiempo",
            "objective": (
                "Aprobar. Que es distinto de saberse el temario."
            ),
            "topics": (
                "Formato del examen y tipos de pregunta\n"
                "Los labs del examen: no se puede volver atrás\n"
                "Estrategia: subnetting rápido primero, labs sin atascarse\n"
                "Simulacros completos cronometrados\n"
                "Repasar SOLO los fallos, no todo otra vez\n"
                "Qué hacer la semana antes"
            ),
            "lab": (
                "Tres simulacros completos de 120 minutos en semanas "
                "distintas. Apuntar cada fallo y su motivo."
            ),
            "estimated_hours": 12,
        },
    ],
}


# --------------------------------------------------------------------------

PLANES = [NSE4, CCNA]


def _horas_del_plan(plan: dict) -> int:
    """Las horas de un plan son la suma de las de sus modulos.

    Antes eran un numero escrito a mano al lado, y ya no cuadraban: NSE 4
    declaraba 120 y sus modulos sumaban 134. Un plan que miente sobre cuanto
    cuesta no sirve para decidir si la fecha objetivo es realista.
    """
    return sum(m.get("estimated_hours") or 0 for m in plan["modules"])


for _plan in PLANES:
    _plan["estimated_hours"] = _horas_del_plan(_plan)


def sembrar_planes_de_estudio(db: Session, organization_id: int | None = None) -> int:
    """Crea o actualiza los planes de estudio. Devuelve cuántos tocó.

    Idempotente: busca por `(organization_id, slug)`. Si el plan existe, se
    actualizan sus datos y se reemplazan sus módulos, para que al corregir un
    temario no queden módulos sueltos de la versión anterior.
    """
    if organization_id is None:
        organizacion = db.scalar(
            select(Organization).where(Organization.slug == "ninjasec-internal")
        )
        if not organizacion:
            raise RuntimeError(
                "No existe la organización 'ninjasec-internal'. "
                "Ejecuta primero el seed principal."
            )
        organization_id = organizacion.id

    tocados = 0
    for datos in PLANES:
        plan = db.scalar(
            select(StudyPlan).where(
                StudyPlan.organization_id == organization_id,
                StudyPlan.slug == datos["slug"],
            )
        )
        if not plan:
            plan = StudyPlan(organization_id=organization_id, slug=datos["slug"])
            db.add(plan)

        plan.name = datos["name"]
        plan.area = datos["area"]
        plan.vendor = datos["vendor"]
        plan.exam_code = datos["exam_code"]
        plan.target_certification = datos["target_certification"]
        plan.estimated_hours = datos["estimated_hours"]
        plan.description = datos["description"]
        plan.is_active = True
        db.flush()

        # Se reemplazan: al corregir un temario no pueden quedar módulos
        # sueltos de la versión anterior.
        for viejo in list(plan.modules):
            db.delete(viejo)
        db.flush()

        for posicion, modulo in enumerate(datos["modules"], start=1):
            db.add(
                StudyModule(
                    plan_id=plan.id,
                    position=posicion,
                    title=modulo["title"],
                    objective=modulo.get("objective"),
                    topics=modulo.get("topics"),
                    lab=modulo.get("lab"),
                    estimated_hours=modulo.get("estimated_hours"),
                    weight_percent=modulo.get("weight_percent"),
                )
            )
        tocados += 1

    db.commit()
    return tocados


if __name__ == "__main__":  # pragma: no cover
    from app.db.session import SessionLocal

    with SessionLocal() as sesion:
        cuantos = sembrar_planes_de_estudio(sesion)
        print(f"[OK] {cuantos} planes de estudio sembrados")
