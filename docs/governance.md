# Gobierno de datos — catálogos, grupos y permisos

Quién puede ver y hacer qué, escrito una sola vez. Lo que está aquí es lo que está en Unity Catalog; si difieren, el catálogo tiene la razón y este archivo se corrige.

Se completa en la clase 3. Todo `<…>` es un marcador que debes reemplazar.

## Catálogos (ambientes)

| Catálogo | Propósito | Quién escribe | Quién lee |
|---|---|---|---|
| `dev` | Desarrollo: pipeline y modelos | `grp_ingenieria` (bronce, plata). `grp_analitica` (plata, oro) | `grp_ingenieria`, `grp_analitica` |
| `qa` | QA: validación antes de producción | pipeline | `grp_ingenieria`, `grp_analitica` |
| `prod` | Producción: datos oficiales para consumo | pipeline | `grp_ingenieria`, `grp_analitica`, `grp_negocio` |

## Esquemas por capa

| Esquema | Contenido | Owner (grupo) |
|---|---|---|
| `bronze_energia` | Datos crudos de XM (precios, demanda, generación) sin transformar | `grp_ingenieria` |
| `silver_energia` | Datos limpios, validados y normalizados por fuente | `grp_ingenieria` |
| `gold_energia` | Datos agregados listos para análisis y dashboards | `grp_analitica` |
| `models` | Modelos ML registrados en Unity Catalog | `grp_analitica` |

## Grupos y roles

| Grupo | Quiénes (rol en XM) | Necesita |
|---|---|---|
| `grp_ingenieria` | Ingenieros de datos (XM) | `USE CATALOG`, `USE SCHEMA`, `SELECT`, `MODIFY` en bronze/silver |
| `grp_analitica` | Analistas y científicos de datos (XM) | `USE CATALOG`, `USE SCHEMA`, `SELECT` en gold; `MODIFY` en gold/models |
| `grp_negocio` | Usuarios de negocio (XM) | `USE CATALOG`, `USE SCHEMA`, `SELECT` en gold de prod |
| `sp_pipeline` | <service principal, no persona> | `USE CATALOG`, `USE SCHEMA`, `ALL PRIVILEGES` en dev/qa/prod para ejecutar el pipeline |

## Matriz de privilegios

Una celda = los privilegios del grupo sobre ese esquema. `—` si no entra.

| Grupo | dev.bronze / silver | dev.gold | dev.models | qa.* | prod.bronze / silver | prod.gold | prod.models |
|---|---|---|---|---|---|---|---|
| `grp_ingenieria` | `SELECT`, `MODIFY` | `SELECT` | `—` | `SELECT` | `SELECT`, `MODIFY` | `SELECT` | `—` |
| `grp_analitica` | `SELECT` | `SELECT`, `MODIFY` | `SELECT`, `MODIFY` | `SELECT` | `SELECT`, `MODIFY` | `SELECT`, `MODIFY` |
| `grp_negocio` | `—` | `—` | `—` | `—` | `—` | `SELECT` | `—` |
| `sp_pipeline` | `ALL PRIVILEGES` | `ALL PRIVILEGES` | `ALL PRIVILEGES` | `ALL PRIVILEGES` | `ALL PRIVILEGES` | `ALL PRIVILEGES` | `ALL PRIVILEGES` |

## Filtros de filas y máscaras

| Tabla | Filtro / máscara | Quién ve todo | Quién ve la versión restringida |
|---|---|---|---|
| `prod.gold_energia.precios_mercado` | Filtro por `zona` — solo filas de la zona del usuario | `grp_analitica`, `sp_pipeline` | `grp_negocio` (ve solo su zona) |
| `prod.gold_energia.demanda_regional` | Máscara sobre `cliente_id` — hash si no es analítica | `grp_analitica` | `grp_negocio` (ve hash, no ID real) |

## Secretos

| Secreto | Scope | Quién lo lee | Dónde vive en XM |
|---|---|---|---|
| `xm_api_token` | `xm_secrets` | `sp_pipeline` | Credenciales de la API de XM (gestionadas por operaciones) |
| `db_warehouse_pwd` | `xm_secrets` | `sp_pipeline` | Contraseña del data warehouse de XM |

## Auditoría y linaje

| Pregunta | Cómo se responde |
|---|---|
| ¿Quién tiene acceso a la tabla X? | `SHOW GRANTS ON TABLE <tabla>` en UC |
| ¿Quién leyó la tabla X la semana pasada? | `system.access.audit` filtrando por `se.action_name = 'SELECT'` y `se.object_name = '<tabla>'` |
| ¿De dónde sale la columna Y de oro? | Linaje de Unity Catalog: `system.access.table_lineage` o pestaña Lineage en el catálogo |
| ¿Qué se rompe si cambio la tabla Z? | Linaje descendente en `system.access.table_lineage` + revisión de pipeline que dependen de Z |
