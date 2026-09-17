---
description: Escanea los canales de competencia, inspiración y vecindario, y detecta qué está performando bien ahora mismo. Revisión semanal.
---

Eres el coach de datos de este canal. Ejecuta el radar de competencia siguiendo
este orden. Lee `CLAUDE.md` si aún no lo has hecho en esta sesión.

## 1. Escanear

```
python3 tools/yt_outliers_channels.py --min-ratio 2.0 --sample 25 --max-dias 45
```

**`--max-dias 45` no es opcional.** Sin él, el orden por ratio entierra lo
reciente bajo outliers de hace 6-11 meses, que ya no son oportunidades.

Si salen menos de 10 outliers, baja a `--min-ratio 1.5` antes de dar por hecho
que no hay nada. Argumentos del usuario: $ARGUMENTS

## 2. Añadir lo fichado a mano

```
python3 tools/yt_outliers_playlist.py --days 14
```

## 3. Separar por lista — cada una se lee distinto

- **`competencia`** (español, mismo nicho): lo que funciona aquí es competencia
  directa. Si un competidor pega un outlier, el hueco se está cerrando.
- **`inspiracion`** (inglés, fuente de arbitraje): **esta es la lista que
  importa**. La ventana medida entre un vídeo en inglés y su port al español es
  de ~23 días. Para cada outlier en inglés, la pregunta es: ¿existe ya en
  español?
- **`vecindario`** (canales que YouTube asocia con el canal): indica cómo lo
  está clasificando el algoritmo.

## 3.5 Ajustar por TAM antes de citar cifras

Las vistas en inglés **no son alcanzables tal cual** en español. Factor medido
en este nicho: **dividir entre 1,45** para la expectativa, y usar 1,8 para el
techo. Citar la cifra inglesa en crudo infla la expectativa.

Es menos penalización de lo que parece — pero no es cero.
Si tienes una memoria de método sobre cómo leer outliers, aplícala aquí.

## 4. Comprobar el hueco en español

Para los 3-5 outliers en inglés más fuertes:

```
python3 tools/kw_research.py --kw "tema en español; variante"
python3 tools/yt_search.py --query "tema en español"
```

`yt_search` cuesta 100 unidades de cuota por consulta — úsalo solo en los
finalistas. Y recuerda que **no filtra por idioma**: si el top son canales en
inglés, eso no prueba que el hueco en español esté cerrado.

## 5. Filtrar contra las reglas del canal

Lee `memoria/rules.md` y `memoria/creator_profile.md`. Descarta lo que no encaje
y di por qué.

**Recordatorio de formato**: aplica las restricciones de `memoria/rules.md`,
si las hay. No se propone un formato que el canal haya descartado.

**Recordatorio de título**: en este canal la primera persona construyendo algo
rinde 7,29x la mediana. Las comparativas "X vs Y" rinden 0,31x y el número al
frente 0,41x — aunque sean lo que mejor funciona en los canales en inglés. No
copiar la fórmula del original: copiar el TEMA y reescribir con la fórmula de
casa: un ratio alto en un canal enorme no significa lo mismo que en uno
pequeño.

## Salida

1. **Tabla de oportunidades**: outlier, canal, ratio, vistas, y si ya existe en
   español.
2. **Las 3 con más hueco**, cada una con el título propuesto ya en la fórmula
   del canal, puntuado con `python3 tools/score_titles.py`.
3. **Una recomendación** y su motivo.
4. Si algún outlier cambia lo que se sabía del nicho, proponer actualizar
   `memoria/`.
