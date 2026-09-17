---
name: Perfil de voz
description: Cómo suenas al hablar: frases firma, ritmo, hooks, humor. Con citas literales.
metadata:
  type: user
---

**SIN POBLAR.** La skill `guion` no puede escribir sin esto.

Se construye con transcripciones REALES de tus vídeos con mejor retención:

```
python3 tools/yt_top_videos.py --days 180 --by-retention --limit 5
python3 tools/yt_transcript.py --video ID --plano
```

Debe llevar **citas literales**, no adjetivos. "Tono cercano" no sirve; la
frase exacta con la que abres tus vídeos, sí. Por debajo de 200 palabras o sin
comillas, está demasiado fino y hay que rehacerlo.

Inventar la voz cuando hay transcripciones disponibles es el error que esta
memoria existe para impedir.
