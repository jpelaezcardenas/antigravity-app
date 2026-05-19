# OUTPUT_FORMAT.md

## Formato de salida obligatorio para Antigravity

### 1. Resumen inicial
Siempre comenzar con:
- Lo ya confirmado
- Lo indefinido
- Defaults propuestos
- Próximos pasos

### 2. Si la salida es arquitectura
Incluir:
- objetivo del sistema
- herramientas
- diagrama lógico narrado
- qué queda manual
- qué queda automatizado
- MVP vs fase 2

### 3. Si la salida es base de datos
Usar tabla por tabla con columnas:
- nombre de tabla
- objetivo
- campos
- tipo
- ejemplo
- relación con otras tablas

Agregar:
- IDs sugeridos
- naming conventions
- vistas sugeridas
- estados
- fórmulas o campos derivados si aplica

### 4. Si la salida es workflow n8n
Para cada workflow usar esta estructura:
- Nombre
- Objetivo
- Trigger
- Inputs
- Nodos sugeridos
- Lógica paso a paso
- Outputs
- Escritura / lectura de datos
- Validaciones
- Errores comunes
- Manejo de excepciones
- Acción humana requerida
- Estado final esperado

### 5. Si la salida es prompt
Para cada prompt usar esta estructura:
- Nombre del prompt
- Objetivo
- Cuándo usarlo
- Variables de entrada
- Instrucciones
- Restricciones
- Guardrails de marca
- Formato de salida esperado
- Ejemplo breve de output si aporta claridad

### 6. Si la salida es sistema de voz
Incluir:
- arquetipo de voz
- tono permitido
- tono prohibido
- palabras recomendadas
- palabras a evitar
- empathy map
- checklist de humanización
- protocolo para reescribir textos fríos

### 7. Si la salida es roadmap
Usar este formato:
- Fase
- Objetivo
- Tareas clave
- Dependencias
- Riesgos
- Resultado esperado
- Checklist de salida

### 8. Reglas universales de calidad
- No usar teoría genérica si puede reemplazarse por estructura operativa.
- No dejar tablas a medio definir.
- No usar términos vagos para métricas.
- Toda métrica debe expresarse como:
  - nombre
  - valor
  - unidad
  - fecha
- Siempre distinguir entre dato confirmado y asunción recomendada.
- Siempre priorizar una versión MVP primero.
