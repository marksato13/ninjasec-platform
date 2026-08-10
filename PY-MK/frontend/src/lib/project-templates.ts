export type ProjectTemplate = {
  id: string;
  name: string;
  description: string;
  /** Títulos de tarea (ProjectTask) que se crean automáticamente al elegir esta plantilla. */
  checklist: string[];
};

/**
 * Catálogo simple, versionado en código (issue #86) -- no hace falta un
 * editor de plantillas desde la UI en esta primera fase. Cada plantilla
 * solo precarga nombre/descripción y genera el checklist inicial de
 * tareas; el resto del formulario (cliente, tipo de proyecto, servicio)
 * lo sigue eligiendo el usuario, porque esos catálogos son por
 * organización y no se pueden fijar de antemano en una constante global.
 */
export const PROJECT_TEMPLATES: ProjectTemplate[] = [
  {
    id: "auditoria-iso27001",
    name: "Auditoría ISO 27001",
    description: "Auditoría de cumplimiento contra el Anexo A de ISO 27001.",
    checklist: [
      "Reunión de arranque con el cliente",
      "Recolectar evidencia de controles del Anexo A",
      "Completar la Declaración de Aplicabilidad (SoA)",
      "Identificar y registrar no conformidades",
      "Redactar informe ejecutivo de hallazgos",
      "Presentar resultados y plan de remediación",
    ],
  },
  {
    id: "implementacion-siem",
    name: "Implementación SIEM/Wazuh",
    description: "Despliegue de Wazuh y normalización de fuentes de log del cliente.",
    checklist: [
      "Relevar fuentes de log disponibles (firewall, endpoints, servidores)",
      "Desplegar Wazuh manager y agentes",
      "Configurar reglas de correlación y alertas críticas",
      "Integrar con pfSense/FortiGate del cliente",
      "Validar alertas con un simulacro de incidente",
      "Documentar runbook de respuesta para el equipo del cliente",
    ],
  },
  {
    id: "revision-seguridad-perimetral",
    name: "Revisión de seguridad perimetral",
    description: "Revisión del firewall y la exposición perimetral del cliente.",
    checklist: [
      "Revisar reglas de firewall activas",
      "Verificar reglas huérfanas o sobre-permisivas",
      "Revisar exposición de servicios a Internet",
      "Verificar VPNs y accesos remotos",
      "Registrar hallazgos en el módulo de Revisiones",
    ],
  },
  {
    id: "diagnostico-red-inicial",
    name: "Diagnóstico de red inicial",
    description: "Levantamiento inicial de infraestructura de red para un cliente nuevo.",
    checklist: [
      "Inventariar dispositivos de red (routers, switches, APs)",
      "Documentar direccionamiento IP y VLANs",
      "Identificar cuellos de botella de rendimiento",
      "Verificar redundancia y puntos únicos de falla",
      "Entregar diagrama de topología actualizado",
    ],
  },
];
