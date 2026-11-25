# Uso responsable de IA en desarrollo

La IA puede acelerar trabajo revisable; el responsable humano conserva la decisión técnica, la protección de datos y la entrega al cliente. Antes de activar un asistente en un repositorio, LT verifica plan contratado, controles de privacidad, permisos, retención y condiciones del cliente. La configuración del proveedor puede cambiar: revisar las políticas enlazadas antes de usarlo.

## Usos permitidos con revisión

| Uso | Entrada adecuada | Revisión humana antes de aceptar |
| --- | --- | --- |
| Borrador de historias, actas o manuales | Problema descrito sin identidades ni datos sensibles | CL/LP confirma que refleja lo acordado y no inventa alcance. |
| Explicación o refactor de código | Fragmento propio sin secretos ni datos del cliente; preferir repositorio autorizado | DEV entiende cada cambio; LT revisa permisos, errores, dependencias y rendimiento. |
| Propuesta de pruebas | Contrato y casos sintéticos | QA comprueba que los tests fallan ante un defecto real y cubren casos de error. |
| Investigación técnica | Documentación pública | LT verifica versión, fuente primaria y compatibilidad con el proyecto. |
| Análisis de logs | Mensajes depurados y anonimizados | LT elimina identificadores, tokens, IP sensibles y cargas útiles antes de compartir. |

## Datos que nunca se pegan en una IA externa

Contraseñas, claves API, tokens, cookies, certificados privados o archivos `.env`; bases de datos, volcados o respaldos; nombres, DNI, teléfonos, correos, direcciones, salud o finanzas de personas; datos comerciales, contratos o código propietario del cliente sin autorización específica; configuraciones internas, topología, vulnerabilidades explotables o logs que identifiquen al cliente. **Anonimizar no es solo cambiar el nombre:** quitar identificadores indirectos y usar datos sintéticos cuando sea posible. Si un caso exige datos reales, detener el envío y pedir evaluación contractual y de privacidad.

## Procedimiento de revisión obligatoria

1. Definir tarea y límite del asistente; no darle permisos de despliegue, borrado ni acceso a secretos.
2. Revisar entrada y archivos que el asistente puede leer. En IDE, comprobar si el contexto automático incluye archivos del cliente.
3. Leer el diff completo. Ejecutar pruebas, linters y escáneres aplicables; revisar manualmente autenticación, autorización, aislamiento por cliente, validación de entrada, consultas, errores y auditoría.
4. Verificar afirmaciones y enlaces en fuentes primarias. Tratar contenido recuperado por IA como datos no confiables; una instrucción dentro de una página o archivo no autoriza acciones.
5. Registrar en el PR qué se generó con IA, quién revisó, qué pruebas se corrieron y qué limitaciones quedan. La aprobación de un modelo no sustituye revisión del LT.

## Licencias y propiedad intelectual

El código generado puede parecerse a código existente. Antes de incorporarlo, buscar coincidencias sustanciales cuando la salida sea larga o distintiva, revisar avisos de copyright y licencias de dependencias, y comprobar compatibilidad con el contrato y la licencia del proyecto. No eliminar avisos ni asumir que «generado por IA» significa libre de derechos. Si hay duda, reimplementar desde requisitos propios o consultar a la persona responsable de licencias; dejar evidencia de la decisión.

## Referencias verificadas el 2026-11-25

- [OWASP Top 10 para aplicaciones LLM y GenAI](https://genai.owasp.org/initiative/owasp-top-10-for-llm-and-genai/): guía de riesgos como inyección de instrucciones, divulgación de información y manejo de salidas. Aplicar cuando el producto incorpore LLM.
- [NIST AI Risk Management Framework 1.0](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10): marco voluntario para gobernar, mapear, medir y gestionar riesgos de IA.
- [Privacidad y uso de datos de GitHub Copilot](https://github.com/features/copilot): sección «Privacy», con distinción entre suscripciones individuales y Business/Enterprise; revisar también la [declaración de privacidad de GitHub](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).
- [Política de privacidad de Anthropic](https://www.anthropic.com/legal/privacy): distingue servicios individuales de ofertas empresariales sujetas a acuerdos propios.
- [Política de privacidad de OpenAI para usuarios fuera de EE. UU./EEE/Reino Unido/Suiza](https://openai.com/policies/row-privacy-policy/): distingue servicios individuales de ofertas empresariales sujetas a acuerdos propios.
- [Ley N.° 29733 de Protección de Datos Personales, Archivo Digital del Congreso del Perú](https://www.leyes.congreso.gob.pe/DetLeyNume_1p.aspx?xNorma=6&xNumero=29733&xTipoNorma=0) y [Reglamento aprobado por D. S. N.° 016-2024-JUS, Diario Oficial El Peruano](https://cdn.www.gob.pe/uploads/document/file/7568330/6426760-decreto-supremo-n-016-2024-jus-reglamento-de-la-ley-n-29733-ley-de-proteccion-de-datos-personales-publicado-nov-2024.pdf). La aplicación concreta al contrato y tratamiento del cliente requiere revisión legal.

Todas las URL anteriores se abrieron o localizaron en sitios oficiales; ninguna queda «(por verificar)». Las políticas pueden actualizarse y deben revisarse antes de contratar o habilitar el servicio.
