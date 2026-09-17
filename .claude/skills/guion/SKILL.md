---
name: guion
description: Escribe guiones de vídeo con la voz real del canal y la estructura de retención validada. Se invoca ante "escribe el guion", "dame el hook", "estructura este vídeo", "cómo abro este vídeo".
---

# Guion

## CUÁNDO

Escribir o reestructurar un guion, diseñar el gancho de los primeros 30
segundos, colocar los re-hooks, revisar una estructura ya escrita.

## ORDEN DE EJECUCIÓN

1. **Comprobar el perfil de voz**
   Leer `memoria/voice_profile.md`.

   - Si está poblado (más de 150 palabras, con frases textuales), se usa y se
     salta al paso 3.
   - Si está vacío o es genérico, **se construye antes de escribir nada**:
     ```
     python3 tools/yt_top_videos.py --days 180 --by-retention --limit 5
     python3 tools/yt_transcript.py --video ID --plano    # los 3 mejores
     ```
     Se analizan muletillas, aperturas, transiciones y cierres reales, y se
     escribe `memoria/voice_profile.md` con citas textuales.

   Inventarse la voz cuando hay transcripciones disponibles es el error que este
   paso previene.

2. **Primacía estructural del SOP**
   Leer `memoria/sop/scripting_sop.md`. **Es la fuente de verdad de la
   estructura.** Si existe una fórmula ahí, los outliers y las keywords de los
   pasos siguientes informan el TEMA, nunca reescriben la estructura.

3. **Validar el tema**
   ```
   python3 tools/yt_outliers_channels.py --min-ratio 2.0
   python3 tools/kw_research.py --kw "tema principal; variante"
   ```
   Los outliers dicen qué ganchos están dando vistas ahora. El score de
   keywords es `heuristic`: sirve para ordenar opciones, no para afirmar
   demanda.

4. **Verificar el hook contra retención real** — si existe un vídeo comparable
   `python3 tools/yt_retention.py --video ID`
   Mirar dónde cayó la audiencia en ese vídeo y no repetir el patrón. Esto
   convierte el SOP en algo verificable en vez de una convención heredada.

5. Escribir, aplicando el SOP y la voz del paso 1.

## FUENTES

Paso 1 `youtube_api` (transcripciones). Paso 3 `derived` + `heuristic`.
Paso 4 `youtube_api`. Al citar el score de keywords hay que declararlo.

## SALIDA

Según lo que se haya pedido: gancho por segundos, outline resumido, o guion
completo. Por defecto el resumido; el completo solo si se confirma.

Cada bloque lleva su función declarada (promesa, prueba, plan, re-hook) para que
se pueda medir después con `yt_retention.py`.
