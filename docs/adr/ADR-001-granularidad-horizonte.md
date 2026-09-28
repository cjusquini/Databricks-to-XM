# ADR-001: Granularidad y horizonte del pronóstico

- **Estado:** aceptada
- **Fecha:** 2026-09-28
- **Autor:** cjusquini

## Contexto

Datos de demanda real y pérdidas de energía, por tipo de mercado y clasificación CIIU asociado a su actividad comercial. Se busca desarrollar un pronóstico por agente, mercado, CIIU en un horizonte de 7 días

## Decisión

Se realizará un pronóstico con granularidad serie-día, horizonte: 7 días a futuro, alcance del modelo: 7 días a futuro por agente, mercado, CIIU.

## Alternativas consideradas

- Alternativa 1: Modelo SARIMAX (pdte)
- Alternativa 2: Modelo Regresión Lineal Múltiple (pdte)
- Alternativa 3: Modelo Redes Neuronales (pdte)

## Consecuencias

Se gana un horizonte con un error reducido de cómo se comportará la demanda, la idea es tomar acciones a nivel de OR de cómo gestionar sus activos. Para revertir las decisiones se debe ajustar el modelo y los datos dada la necesidad.
