/**
 * Datos del mapa guía del SGSI.
 *
 * Este archivo es, a propósito, la ÚNICA pieza que hay que tocar para
 * adaptar el mapa: las vistas, los nodos, las herramientas y los textos.
 * El componente que lo dibuja no sabe nada del contenido.
 *
 * Criterio que gobierna el contenido: **lo que ya existe en código abierto
 * se referencia, no se reimplementa.** CISO Assistant y Comp AI gestionan
 * activos, riesgos, SoA y evidencias mejor de lo que construiríamos; aquí se
 * señalan y se enlaza a ellas. Lo que sí es nuestro es la capa de
 * entregables: plantillas en español y generación de Word con la marca de la
 * consultora.
 */

export type Capa = "entrada" | "registro" | "generacion" | "entrega";

export type Origen = "propio" | "abierto" | "comercial" | "manual";

export interface Herramienta {
  nombre: string;
  origen: Origen;
  url?: string;
  /** Qué hace exactamente, en una frase. */
  papel: string;
  /** Límite conocido. Se escribe; no se esconde. */
  limite?: string;
}

export interface NodoGuia {
  id: string;
  titulo: string;
  capa: Capa;
  /** Una línea: qué se produce aquí. */
  resumen: string;
  /** La explicación larga del panel lateral. */
  detalle: string;
  herramientas: Herramienta[];
  /** Cláusula o anexo de ISO/IEC 27001 que lo respalda. */
  norma?: string;
  /** Documentos que salen de este paso. */
  entregables?: string[];
}

export interface Arista {
  desde: string;
  hacia: string;
  etiqueta?: string;
}

export interface VistaGuia {
  id: string;
  titulo: string;
  /** Qué pregunta responde esta vista. */
  proposito: string;
  nodos: NodoGuia[];
  aristas: Arista[];
}

// ---------------------------------------------------------------------------
// Herramientas reutilizadas entre vistas
// ---------------------------------------------------------------------------

const CISO_ASSISTANT: Herramienta = {
  nombre: "CISO Assistant Community",
  origen: "abierto",
  url: "https://github.com/intuitem/ciso-assistant-community",
  papel:
    "Sistema de registro: activos, riesgos, Declaración de Aplicabilidad, evidencias y ciclo de vida de documentos. AGPLv3, se autoaloja gratis.",
  limite:
    "Su biblioteca de políticas está en inglés, francés y húngaro — no hay español. Las plantillas Word propias y la jerarquía multi-cliente son de pago.",
};

const DOCGEN: Herramienta = {
  nombre: "sgsi-docgen",
  origen: "propio",
  papel:
    "Convierte las fuentes en Markdown en el expediente Word con la marca de la consultora: carátula, tabla de control, índice y bloques de firma.",
  limite: "En construcción. El manifiesto y su validación funcionan; la generación de Word se está portando.",
};

const PLANTILLAS_ES: Herramienta = {
  nombre: "Plantillas SGSI en español",
  origen: "propio",
  papel:
    "Corpus de documentos ISO 27001:2022 en español, adaptado a Perú (Ley 29733 de Protección de Datos Personales).",
  limite: "Pendiente. Es la pieza de más valor: no existe ninguna biblioteca libre equivalente.",
};

const DECISION_HUMANA: Herramienta = {
  nombre: "Decisión humana",
  origen: "manual",
  papel:
    "Ninguna herramienta decide esto. Se acuerda con la dirección del cliente y queda por escrito.",
};

// ---------------------------------------------------------------------------
// Vistas
// ---------------------------------------------------------------------------

export const VISTAS: VistaGuia[] = [
  {
    id: "recorrido",
    titulo: "El recorrido completo",
    proposito: "¿Por dónde pasa la documentación, de principio a fin?",
    nodos: [
      {
        id: "contexto",
        titulo: "Contexto y alcance",
        capa: "entrada",
        resumen: "Qué protege el SGSI y qué queda fuera",
        detalle:
          "El primer documento y el que más condiciona todo lo demás. Define qué procesos, sedes y servicios entran en el sistema de gestión, y cuáles no. Un alcance mal delimitado obliga a rehacer la matriz de activos, la de riesgos y la Declaración de Aplicabilidad.\n\nSe redacta con la dirección, no se deduce de una herramienta.",
        norma: "ISO/IEC 27001:2022 — cláusulas 4.1 a 4.4",
        entregables: ["Documento de alcance", "Análisis de partes interesadas"],
        herramientas: [DECISION_HUMANA, PLANTILLAS_ES],
      },
      {
        id: "activos",
        titulo: "Inventario de activos",
        capa: "registro",
        resumen: "Qué hay que proteger, con responsable y criticidad",
        detalle:
          "Todo lo que tiene valor para el negocio dentro del alcance: servidores, aplicaciones, bases de datos, información en papel, personas clave y proveedores.\n\nCada activo necesita responsable asignado y una clasificación de criticidad. Sin esas dos cosas, la matriz de riesgos no se puede construir: no hay a quién asignarle el tratamiento ni con qué priorizar.",
        norma: "ISO/IEC 27001:2022 — A.5.9",
        entregables: ["Matriz de activos"],
        herramientas: [CISO_ASSISTANT],
      },
      {
        id: "riesgos",
        titulo: "Evaluación de riesgos",
        capa: "registro",
        resumen: "Qué puede pasar, con qué probabilidad e impacto",
        detalle:
          "Se cruza cada activo con las amenazas y vulnerabilidades que le aplican, y se valora probabilidad por impacto según los criterios que haya fijado la dirección.\n\nLos criterios de aceptación de riesgo son una decisión de negocio, no técnica: cuánto riesgo está dispuesta a asumir la empresa. Esa decisión se documenta antes de evaluar, no después de ver los resultados.",
        norma: "ISO/IEC 27001:2022 — cláusula 6.1.2 · ISO/IEC 27005",
        entregables: ["Matriz de riesgos", "Criterios de evaluación"],
        herramientas: [CISO_ASSISTANT, DECISION_HUMANA],
      },
      {
        id: "soa",
        titulo: "Tratamiento y Declaración de Aplicabilidad",
        capa: "registro",
        resumen: "Qué controles se aplican y por qué se descartan los demás",
        detalle:
          "Por cada riesgo se decide: mitigar, transferir, evitar o aceptar. Los controles que se eligen se mapean contra los 93 del Anexo A, y los que no se aplican necesitan justificación escrita.\n\nLa Declaración de Aplicabilidad es el documento que un auditor pide primero. Su valor no está en marcar casillas: está en que cada 'no aplica' tenga un motivo defendible.",
        norma: "ISO/IEC 27001:2022 — cláusula 6.1.3 y Anexo A",
        entregables: ["Declaración de Aplicabilidad (SoA)", "Plan de tratamiento"],
        herramientas: [CISO_ASSISTANT],
      },
      {
        id: "redaccion",
        titulo: "Redacción de políticas",
        capa: "generacion",
        resumen: "Las políticas y procedimientos, en Markdown versionado",
        detalle:
          "Las fuentes se escriben en Markdown y viven en control de versiones, no en un Word que circula por correo. Eso permite ver quién cambió qué, revertir y regenerar el expediente completo desde cualquier punto del historial.\n\nLas plantillas dan la estructura; el contenido se adapta a los riesgos y decisiones reales del cliente. Una política copiada sin adaptar es peor que no tenerla: da una falsa sensación de cumplimiento.",
        norma: "ISO/IEC 27001:2022 — cláusula 7.5 (información documentada)",
        entregables: ["Políticas específicas", "Procedimientos operativos"],
        herramientas: [PLANTILLAS_ES, DECISION_HUMANA],
      },
      {
        id: "expediente",
        titulo: "Generación del expediente",
        capa: "generacion",
        resumen: "Markdown entra, Word con marca sale",
        detalle:
          "El manifiesto declara qué documentos componen el expediente, de qué fuentes sale cada uno, quién lo firma y con qué marca se imprime. El generador no sabe nada de ningún cliente concreto: todo lo específico vive en ese archivo.\n\nConsecuencia práctica: el expediente de marzo se puede volver a generar en diciembre, exactamente igual, desde el commit correspondiente.",
        entregables: ["Expediente Word completo", "Registros Excel"],
        herramientas: [DOCGEN],
      },
      {
        id: "coherencia",
        titulo: "Auditoría de coherencia",
        capa: "generacion",
        resumen: "Un linter para los entregables",
        detalle:
          "Cruza los documentos entre sí en ambos sentidos: riesgos que apuntan a activos que ya no existen, criticidades que divergen entre la matriz de activos y la de riesgos, controles del Anexo A inventados, trazabilidad rota entre SoA y riesgo, activos críticos sin evaluar.\n\nEsto es lo que ninguna plataforma cubre: audita los Word y Excel **después** de que el cliente los edita a mano, que es exactamente donde se rompe la cadena en la vida real.",
        entregables: ["Informe de incoherencias"],
        herramientas: [
          {
            nombre: "auditar-coherencia",
            origen: "propio",
            papel:
              "Linter de entregables. Respeta las excepciones declaradas por escrito para no generar ruido.",
            limite: "Pendiente de generalizar: hoy tiene las rutas de un cliente fijadas en el código.",
          },
        ],
      },
      {
        id: "entrega",
        titulo: "Entrega y firma",
        capa: "entrega",
        resumen: "El expediente firmado, en manos del cliente",
        detalle:
          "El expediente se revisa con el cliente en voz alta, no se envía por correo y se da por entregado. La documentación que nadie ha leído no cumple nada: solo existe.\n\nAl cerrar, las credenciales usadas durante el trabajo se rotan y se entregan. Si el cliente decide no seguir, no le queda nada bloqueado.",
        norma: "ISO/IEC 27001:2022 — cláusula 7.5.3 (control de la información documentada)",
        entregables: ["Acta de entrega firmada"],
        herramientas: [DECISION_HUMANA],
      },
    ],
    aristas: [
      { desde: "contexto", hacia: "activos", etiqueta: "delimita" },
      { desde: "activos", hacia: "riesgos", etiqueta: "alimenta" },
      { desde: "riesgos", hacia: "soa", etiqueta: "justifica" },
      { desde: "soa", hacia: "redaccion", etiqueta: "determina" },
      { desde: "redaccion", hacia: "expediente" },
      { desde: "expediente", hacia: "coherencia", etiqueta: "valida" },
      { desde: "coherencia", hacia: "entrega" },
      { desde: "activos", hacia: "coherencia", etiqueta: "se contrasta" },
      { desde: "soa", hacia: "coherencia", etiqueta: "se contrasta" },
    ],
  },
  {
    id: "herramientas",
    titulo: "Qué hace cada herramienta",
    proposito: "¿Qué uso ya hecho y qué construimos nosotros?",
    nodos: [
      {
        id: "h-ciso",
        titulo: "CISO Assistant",
        capa: "registro",
        resumen: "El sistema de registro — no lo reimplementamos",
        detalle:
          "Plataforma de GRC bajo AGPLv3, autoalojable sin coste. Gestiona activos, riesgos, Declaración de Aplicabilidad, evidencias, incidentes y más de 200 marcos normativos. Trae los controles del Anexo A ya traducidos al español.\n\n**No competimos con esto.** Es mejor de lo que construiríamos y está mantenida. Se usa como sistema de registro vía su API REST, y NinjaSec se queda con la capa de entregables.",
        herramientas: [CISO_ASSISTANT],
      },
      {
        id: "h-compai",
        titulo: "Comp AI",
        capa: "registro",
        resumen: "Alternativa, también AGPL",
        detalle:
          "Segunda opción abierta: 52 plantillas de políticas, módulo de SoA, generación de PDF. Su nube es un código base separado y propietario, así que el repositorio comunitario no tiene funciones recortadas dentro — para un fork honesto es más limpio que CISO Assistant.\n\nLímite: todo en inglés, y con cultura SOC 2 más que ISO 27001.",
        herramientas: [
          {
            nombre: "Comp AI Community",
            origen: "abierto",
            url: "https://github.com/trycompai/comp",
            papel: "Gestión de cumplimiento con 52 plantillas y salida PDF.",
            limite: "Solo inglés. Sin salida Word.",
          },
        ],
      },
      {
        id: "h-eramba",
        titulo: "eramba",
        capa: "registro",
        resumen: "⚠️ NO es software libre",
        detalle:
          "Se presenta como «Free, Open GRC» pero **no lo es**. Su propio equipo confirma en el foro oficial que la licencia prohíbe redistribuir y compartir modificaciones, y que evitan deliberadamente el término «open source».\n\nSe incluye aquí precisamente para que nadie la proponga como base: no se puede forkear ni publicar sobre ella.",
        herramientas: [
          {
            nombre: "eramba community",
            origen: "comercial",
            url: "https://www.eramba.org/",
            papel: "Gestor de registros GRC.",
            limite: "Licencia propietaria pese al marketing. Prohíbe la redistribución.",
          },
        ],
      },
      {
        id: "h-plantillas",
        titulo: "Plantillas en español",
        capa: "generacion",
        resumen: "El hueco más grande — no existe nada libre",
        detalle:
          "No hay ni una sola biblioteca de código abierto de plantillas de SGSI en español. CISO Assistant las tiene en inglés, francés y húngaro. Comp AI, 52 en inglés. Lo que existe en español es comercial.\n\nUn corpus en español adaptado a Perú —Ley 29733, expectativas de SBS e Indecopi, terminología de PYME— es trabajo real, no duplicado. Y es importable directamente por cualquier instancia de CISO Assistant.",
        herramientas: [PLANTILLAS_ES],
      },
      {
        id: "h-docgen",
        titulo: "sgsi-docgen",
        capa: "generacion",
        resumen: "El Word con tu marca",
        detalle:
          "En CISO Assistant, usar tu propia plantilla Word es una función de pago, y su código está bajo licencia comercial. Tu entregable —carátula, tabla de control del documento, índice automático, bloques de firma— no lo produce ninguna herramienta abierta.\n\nEl manifiesto es la pieza clave: todo lo específico de un cliente vive ahí, versionado junto al expediente.",
        herramientas: [DOCGEN],
      },
      {
        id: "h-pandoc",
        titulo: "Pandoc",
        capa: "generacion",
        resumen: "El motor de conversión",
        detalle:
          "Convierte Markdown a Word y PDF, y con `--reference-doc` aplica un documento de estilos propio. Es la pieza sobre la que se apoya la generación, no la solución completa: no sabe nada de SGSI.",
        herramientas: [
          {
            nombre: "Pandoc",
            origen: "abierto",
            url: "https://pandoc.org/",
            papel: "Conversión Markdown → Word/PDF con estilos propios.",
          },
        ],
      },
    ],
    aristas: [
      { desde: "h-ciso", hacia: "h-docgen", etiqueta: "exporta datos" },
      { desde: "h-plantillas", hacia: "h-ciso", etiqueta: "se importan" },
      { desde: "h-plantillas", hacia: "h-docgen", etiqueta: "fuentes" },
      { desde: "h-pandoc", hacia: "h-docgen", etiqueta: "motor" },
    ],
  },
];

export const CAPAS: Record<Capa, { titulo: string; descripcion: string }> = {
  entrada: {
    titulo: "Decisión",
    descripcion: "Lo que acuerda la dirección del cliente. Ninguna herramienta lo decide.",
  },
  registro: {
    titulo: "Registro",
    descripcion: "Donde viven los datos: activos, riesgos, controles. Software existente.",
  },
  generacion: {
    titulo: "Generación",
    descripcion: "De los datos al documento. Aquí es donde aportamos.",
  },
  entrega: {
    titulo: "Entrega",
    descripcion: "El expediente en manos del cliente, revisado y firmado.",
  },
};

export const ORIGEN_ETIQUETA: Record<Origen, string> = {
  propio: "NinjaSec",
  abierto: "Código abierto",
  comercial: "Comercial",
  manual: "Humano",
};
