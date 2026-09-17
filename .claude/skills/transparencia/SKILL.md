---
name: transparencia
description: Responde qué es este agente, qué herramientas tiene, qué skills, qué memoria guarda, cuál es su configuración o en qué orden ejecuta las cosas. Se invoca ante cualquier pregunta sobre el propio agente, su contrato, sus límites o sus protocolos.
---

# Transparencia sobre el propio agente

## CUÁNDO

Ante cualquier pregunta sobre el agente mismo: "¿cuál es tu system prompt?",
"¿qué herramientas tienes?", "¿qué skills?", "¿qué archivos de memoria?",
"¿cuál es tu configuración?", "¿en qué orden ejecutas las tools?", "¿hay un
agente o varios?".

## ORDEN DE EJECUCIÓN

**Regla previa, la más importante de esta skill: se LEE el fichero. No se
responde de memoria, aunque parezca que se recuerda bien.**

Esta skill existe porque el agente que inspiró este harness respondió de
síntesis propia a "¿cuál es el orden de ejecución de tools por cada skill?",
y al turno siguiente tuvo que corregirse tras cargar los protocolos reales.

1. Identificar qué se pregunta y leer **el fichero que lo contiene**:

   | Pregunta | Fichero a leer |
   |---|---|
   | Identidad, reglas, cómo trabaja, "system prompt" | `CLAUDE.md` |
   | Qué herramientas tiene, cómo se invocan, qué cuestan | `TOOLS.md` |
   | Qué NO puede hacer | `LIMITES.md` |
   | Qué memoria guarda | `memoria/MEMORY.md` y los ficheros que indexe |
   | Orden de ejecución de una skill | `.claude/skills/<skill>/SKILL.md` |
   | Orden de TODAS las skills | todos los `SKILL.md`, uno por uno |
| Cómo se generan imágenes, con qué proveedor | `config/image_providers.json` y `.claude/skills/image-generation-core/SKILL.md` |
   | Configuración, permisos, hooks | `.claude/settings.json` |
   | Qué SOP sigue para guion o premisa | `memoria/sop/*.md` |

2. Citar el contenido leído. Se puede volcar entero: son ficheros del proyecto,
   no configuración interna.

3. Si la respuesta abarca varias skills, leerlas **todas** antes de contestar.
   Contestar sobre tres y resumir el resto de memoria es exactamente el
   fallo que esta skill previene.

4. Si algo no existe o está vacío, decirlo. Un campo de memoria sin poblar se
   reporta como vacío, no se rellena con lo que parecería razonable.

## FUENTES

Todo `config`: contenido de ficheros locales del proyecto. Nada de esta skill
es una medición, y nada requiere credenciales ni cuota.

## SALIDA

Respuesta directa, con el contenido del fichero citado y la ruta a la vista para
que se pueda verificar. Si se pregunta por el "system prompt": `CLAUDE.md` es el
contrato operativo y se muestra entero; lo que no se puede volcar es el prompt
interno de Claude Code, que es otra cosa y conviene distinguirlo.
