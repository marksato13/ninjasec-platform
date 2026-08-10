"""28-P1: modo guiado -- árbol de decisión declarativo (JSON), sin IA/ML.

Cada nodo es una pregunta de sí/no con dos opciones, cada una apuntando a
otro nodo o a un `issue_code` del catálogo (hoja del árbol). El frontend
solo necesita caminar esta estructura y, al llegar a una hoja, mostrar el
`NetdoctorIssue` correspondiente con el comando para el vendor elegido.
"""

GUIDED_TREE: dict[str, dict] = {
    "start": {
        "question": "¿El dispositivo tiene conectividad de red (responde ping al gateway)?",
        "options": [{"label": "No", "next": "no_conn"}, {"label": "Sí", "next": "has_gw"}],
    },
    "no_conn": {
        "question": "¿El puerto del switch muestra el enlace activo (LED encendido)?",
        "options": [{"label": "No", "next": "port_check"}, {"label": "Sí", "next": "ip_dup_check"}],
    },
    "port_check": {"issue_code": "ND-PORTDOWN"},
    "ip_dup_check": {
        "question": "¿Hay otro dispositivo usando la misma dirección IP en la red?",
        "options": [{"label": "Sí", "next": "ip_conflict"}, {"label": "No", "next": "no_connectivity"}],
    },
    "ip_conflict": {"issue_code": "ND-IPCONF"},
    "no_connectivity": {"issue_code": "ND-NOCONN"},
    "has_gw": {
        "question": "¿Puedes alcanzar el gateway pero no salir a otras redes/Internet?",
        "options": [{"label": "Sí", "next": "gw_down"}, {"label": "No", "next": "slow_check"}],
    },
    "gw_down": {"issue_code": "ND-GWDOWN"},
    "slow_check": {
        "question": "¿El problema es que la red está lenta, no que falte conectividad?",
        "options": [{"label": "Sí", "next": "duplex_check"}, {"label": "No", "next": "dns_check"}],
    },
    "duplex_check": {
        "question": "¿Hay muchos errores CRC o colisiones tardías en la interfaz?",
        "options": [{"label": "Sí", "next": "duplex_mismatch"}, {"label": "No", "next": "latency_check"}],
    },
    "duplex_mismatch": {"issue_code": "ND-DUPLEX"},
    "latency_check": {
        "question": "¿Es lento hacia un destino específico (alta latencia o pérdida de paquetes)?",
        "options": [{"label": "Sí", "next": "latency_loss"}, {"label": "No", "next": "slow_perf"}],
    },
    "latency_loss": {"issue_code": "ND-LATLOSS"},
    "slow_perf": {"issue_code": "ND-SLOWPERF"},
    "dns_check": {
        "question": "¿El problema es no poder resolver nombres de dominio (aunque las IPs sí responden)?",
        "options": [{"label": "Sí", "next": "dns_fail"}, {"label": "No", "next": "dhcp_check"}],
    },
    "dns_fail": {"issue_code": "ND-DNSFAIL"},
    "dhcp_check": {
        "question": "¿El dispositivo no obtiene una IP automáticamente (DHCP)?",
        "options": [{"label": "Sí", "next": "dhcp_fail"}, {"label": "No", "next": "vlan_scope_check"}],
    },
    "dhcp_fail": {"issue_code": "ND-DHCPFAIL"},
    "vlan_scope_check": {
        "question": "¿El problema afecta a toda una VLAN o el tráfico entre switches?",
        "options": [{"label": "Sí", "next": "instability_check"}, {"label": "No", "next": "service_check"}],
    },
    "instability_check": {
        "question": "¿Hay inestabilidad general de la red (tormenta de broadcast, CPU alta en switches)?",
        "options": [{"label": "Sí", "next": "stp_loop"}, {"label": "No", "next": "trunk_misconfig"}],
    },
    "stp_loop": {"issue_code": "ND-STPLOOP"},
    "trunk_misconfig": {"issue_code": "ND-TRUNKMIS"},
    "service_check": {
        "question": "¿Un servicio específico (puerto/aplicación) no funciona pero el resto de la red sí?",
        "options": [{"label": "Sí", "next": "nat_check"}, {"label": "No", "next": "vlan_mismatch"}],
    },
    "nat_check": {
        "question": "¿Es un servicio publicado hacia Internet (acceso desde afuera)?",
        "options": [{"label": "Sí", "next": "nat_misconfig"}, {"label": "No", "next": "acl_block"}],
    },
    "nat_misconfig": {"issue_code": "ND-NATMIS"},
    "acl_block": {"issue_code": "ND-ACLBLOCK"},
    "vlan_mismatch": {"issue_code": "ND-VLANMIS"},
}
