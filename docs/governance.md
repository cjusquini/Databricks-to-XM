# Gobierno de datos — catálogos, grupos y permisos

Quién puede ver y hacer qué, escrito una sola vez. Lo que está aquí es lo que está en Unity Catalog; si difieren, el catálogo tiene la razón y este archivo se corrige.

Se completa en la clase 3. Todo `<…>` es un marcador que debes reemplazar.

## Catálogos (ambientes)

| Catálogo | Propósito | Quién escribe | Quién lee |
|---|---|---|---|
| `dev` | <…> | <…> | <…> |
| `qa` | <…> | <…> | <…> |
| `prod` | <…> | <…> | <…> |

## Esquemas por capa

| Esquema | Contenido | Owner (grupo) |
|---|---|---|
| `bronze_energia` | <…> | <…> |
| `silver_energia` | <…> | <…> |
| `gold_energia` | <…> | <…> |
| `models` | <…> | <…> |

## Grupos y roles

| Grupo | Quiénes (rol en XM) | Necesita |
|---|---|---|
| `grp_ingenieria` | <…> | <…> |
| `grp_analitica` | <…> | <…> |
| `grp_negocio` | <…> | <…> |
| `sp_pipeline` | <service principal, no persona> | <…> |

## Matriz de privilegios

Una celda = los privilegios del grupo sobre ese esquema. `—` si no entra.

| Grupo | dev.bronze / silver | dev.gold | dev.models | qa.* | prod.bronze / silver | prod.gold | prod.models |
|---|---|---|---|---|---|---|---|
| `grp_ingenieria` | <…> | <…> | <…> | <…> | <…> | <…> | <…> |
| `grp_analitica` | <…> | <…> | <…> | <…> | <…> | <…> | <…> |
| `grp_negocio` | <…> | <…> | <…> | <…> | <…> | <…> | <…> |
| `sp_pipeline` | <…> | <…> | <…> | <…> | <…> | <…> | <…> |

## Filtros de filas y máscaras

| Tabla | Filtro / máscara | Quién ve todo | Quién ve la versión restringida |
|---|---|---|---|
| <…> | <…> | <…> | <…> |

## Secretos

| Secreto | Scope | Quién lo lee | Dónde vive en XM |
|---|---|---|---|
| <…> | <…> | <…> | <…> |

## Auditoría y linaje

| Pregunta | Cómo se responde |
|---|---|
| ¿Quién tiene acceso a la tabla X? | <…> |
| ¿Quién leyó la tabla X la semana pasada? | <…> |
| ¿De dónde sale la columna Y de oro? | <…> |
| ¿Qué se rompe si cambio la tabla Z? | <…> |
