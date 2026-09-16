# Lab 2 — Explorar para diseñar

**Duración:** 45 min · **Modalidad:** individual, en tu propio fork · **Rama:** `feature/c02-arquitectura`

## Objetivo

Diseñar las cinco tablas de la solución (bronce, plata, oro) con su contrato, y registrar la primera decisión de arquitectura. Poco código, mucho criterio.

## Antes de empezar

| Requisito | Si no lo tienes |
|---|---|
| Lab 1 terminado (`workspace.c01_<usuario>.demanda_raw`) | Usa `usuario = docente` en el widget: la tabla `workspace.c01_docente.demanda_raw` tiene permiso de lectura para todos |
| Git folder actualizado | Botón Git → **Pull** para traer los archivos de la clase 2 |

## Pasos

### Parte 1 — Explorar (20 min)

1. En el Git folder crea la rama `feature/c02-arquitectura`.
2. Abre `clases/c02-arquitectura-medallion/notebooks/lab02_explorar_para_disenar`. Widget `usuario` = el de tu esquema.
3. Ejecuta bloque por bloque. Cada bloque reproduce un hecho del dato y termina con una pregunta de diseño; escribe tu respuesta en la celda de texto `_Tu respuesta:_`.

| Hecho | Valor esperado |
|---|---|
| Filas por serie-día | Siempre 2 (72.704 serie-días) |
| Retraso de publicación | mín 5 · mediana 68 · máx 205 días |
| Series incompletas | 4 (una con solo 7 días) |
| Regulado / No regulado | 29 series y 69 % de la energía / 326 series |
| Serie-días con demanda 0 | 299 |
| Pérdidas > demanda | 0 casos; ratio mediano ≈ 0,015 |

### Parte 2 — Diseñar (25 min)

4. Abre `docs/architecture.md`. Llena, para cada una de las cinco tablas, las columnas **grano, dueño, frescura y garantías**. El dueño es un rol de XM (por ejemplo "equipo de analítica", "ingeniería de datos"), no un nombre.
5. Abre `docs/adr/ADR-001-granularidad-horizonte.md`. Completa contexto, decisión, alternativas descartadas (al menos dos, con el porqué) y consecuencias. Cambia el estado a `aceptada`.
6. Vuelve al notebook y ejecuta la última celda, `verificar()`. Revisa los dos archivos.
7. Commit `feat(c02): arquitectura y ADR-001` → push → PR hacia `main` de tu fork → CI en verde → merge.

## Criterios de aceptación

- [ ] `docs/architecture.md` con las 5 tablas y sin celdas vacías ni marcadores `<…>`
- [ ] `ADR-001` en estado aceptada, con decisión escrita y ≥ 2 alternativas descartadas
- [ ] `verificar()` en OK; PR en verde

**Hito 1 cerrado** cuando además `verificar()` del lab 1 está en verde.

## Comparar con la solución de referencia

Al cierre se libera el tag `s02`:

```bash
git fetch upstream --tags
git diff s02 -- docs/architecture.md docs/adr/ADR-001-granularidad-horizonte.md
```

No hay una única respuesta correcta en el diseño; sí hay decisiones sin justificar. Compara el porqué, no el qué.

## Extensión opcional

Diseña la sexta tabla, `gold_energia.desempeno_modelo` (observado vs. estimado por serie y día), con su contrato. La usaremos en la clase 15.

## Problemas frecuentes

| Síntoma | Causa probable |
|---|---|
| `TABLE_OR_VIEW_NOT_FOUND` | Widget `usuario` no coincide con tu esquema (o el lab 1 no terminó: usa `docente`) |
| `No encuentro docs/architecture.md` | El notebook se abrió fuera del Git folder (por ejemplo, importado a Workspace) |
| `FALTA architecture.md: sin celdas vacías` | Quedó algún `<…>` de la plantilla o una celda `| |` en blanco |
| `FALTA ADR-001 con al menos 2 alternativas` | Las alternativas deben ir como lista con `- ` |

## Así sería en Azure Databricks

| Hoy | En XM |
|---|---|
| Contratos en `docs/architecture.md` | Además: `COMMENT ON TABLE` y tags (`owner`, `capa`, `frescura`) en Unity Catalog |
| Bronce recibe un upload manual | Landing zone en ADLS Gen2 + Auto Loader (clase 4) |
| Dueño = rol escrito | Grupo de Entra ID como owner del esquema |
