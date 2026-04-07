# BEO Pipeline Architecture

## Objetivo
Separar parsing, detección de funciones, filtro semántico, extracción de menú, clasificación de servicio, reglas operativas y validación en módulos testeables.

## Estructura
- `beo_pipeline/beo_parser.py`: extrae texto por página y agrupa páginas por `Event Order #`.
- `beo_pipeline/event_detector.py`: detecta funciones detalladas dentro del bloque `ATTENDANCE` y las cruza con su fila de attendance para tiempo, room y GTD.
- `beo_pipeline/food_service_filter.py`: decide si una función realmente pertenece a food service.
- `beo_pipeline/menu_extractor.py`: convierte el bloque raw de una función en `menu_sections`.
- `beo_pipeline/menu_normalizer.py`: normaliza items, cantidades explícitas y fingerprint del menú.
- `beo_pipeline/service_classifier.py`: clasifica `category`, `meal_period` y `subtype`.
- `beo_pipeline/setup_rules.py`: orquesta reglas de setup.
- `beo_pipeline/equipment_rules.py`: capa declarativa para equipment. Incluye trazabilidad de reglas pendientes y excluidas.
- `beo_pipeline/breakdown_rules.py`: base para reglas de breakdown station.
- `beo_pipeline/event_object_builder.py`: construye el objeto final estandarizado.
- `beo_pipeline/validators.py`: validación estructural básica.
- `beo_pipeline/pipeline.py`: punto de orquestación.
- `beo_cli.py`: CLI para procesar un PDF y devolver JSON.

## Decisiones clave
- El parser no depende de nombres exactos de menú. Detecta bloques de detalle por líneas que empiezan con hora simple.
- El filtro de food service no crea eventos a partir de attendance solamente. Exige evidencia textual del bloque real.
- El extractor analiza cada bloque actual. No reutiliza menús históricos por nombre.
- Las reglas de equipment y breakdown están desacopladas y auditables. Si falta fórmula real, el sistema marca la decisión como `pending` en lugar de inventarla.
- La salida conserva `details.raw`, `source_trace.page_ranges`, `source_trace.text_snippets` y `notes`.

## Limitaciones actuales
- Las fórmulas exactas para `glasses`, `covers`, `salad_trees`, `speed_racks`, `plates_in_cold_area`, `plates_in_hot_box`, `hot_boxes` y tamaños reales de breakdown station no existían en el repositorio. La infraestructura quedó lista, pero esos cálculos quedan `pending` hasta cargar reglas operativas reales.
- La clasificación de títulos de sección usa heurísticas robustas para el layout actual, pero sigue siendo extensible porque algunos BEOs pueden introducir nuevos encabezados culinarios.
- Los tiempos de `setup`, `pickup_food` y `clean_up` no se inventan. Solo se rellenan cuando existan reglas aprobadas o datos explícitos.

## Ejecución
```bash
python beo_cli.py "EO BATCH\\4.5.26 - 4.12.26 EOs.pdf" -o output\\events.json
```

## Pruebas
```bash
python -m unittest discover -s tests -v
```
