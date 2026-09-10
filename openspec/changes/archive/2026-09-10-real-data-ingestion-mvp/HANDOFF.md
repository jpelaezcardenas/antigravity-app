# Entrega — real-data-ingestion-mvp

## Explicación fácil (como para un niño de 10 años)

Imagina que Contexia es una tienda. Ya construimos **3 puertas** por donde los clientes pueden
meter sus recibos y facturas: subir un archivo desde la app, conectar Siigo, o mandar un correo
a Taty. Las 3 puertas ya están construidas y probadas con muñecos de prueba (tests).

Pero **2 de las 3 puertas están cerradas con llave a propósito**, porque todavía no les hemos
puesto la llave (unas claves secretas que solo tú puedes generar). Eso es bueno — significa que
nada se rompe ni se filtra, simplemente está esperando.

**Lo que falta no es programar más código. Es que tú hagas 6 cositas** (generar una clave,
pegar un archivo en Supabase, conseguir un dato de Siigo, etc.) y luego probarlo una vez con
un cliente real.

## Qué quedó listo y ya funciona (verificado hoy, no supuesto)

| Cosa | Estado |
|---|---|
| Backend en Railway | vivo (`200`) |
| App en Vercel (`contexia.online`) | viva (`200`) |
| Bug de seguridad (datos de un cliente se iban al lugar equivocado) | arreglado y verificado |
| Subir CSV/Excel/XML/PDF y que se lean bien | arreglado, 33/33 tests pasando |
| Puerta 2 (Siigo) y puerta 3 (Gmail) | código listo, **cerradas con llave a propósito** (dan error 503, es lo correcto) |
| Documentación del cambio (por qué, cómo, specs) | completa |

## Las 6 cositas pendientes (todas tuyas, ninguna es código)

1. Generar una clave secreta (`INTERNAL_API_KEY`) y pegarla en 3 lugares
2. Pegar un archivo SQL en Supabase (la "puerta" de Gmail lo necesita)
3. Conseguir un dato de Siigo (`Partner-Id`) — pedirlo a tu contacto de Siigo
4. Pedirle a cada cliente con Siigo su `access_key` (no su contraseña)
5. Conectar el Gmail de Taty (un solo clic de autorización, una vez)
6. Correr una consulta para saber **para cuáles de tus 11 clientes** es esto

Los comandos exactos, uno por uno, están en:
`openspec/changes/real-data-ingestion-mvp/RUNBOOK.md`

## Cómo comprobar que de verdad funciona (la prueba final)

1. Entra a `contexia.online/login.html` con el usuario de un cliente real (no el admin)
2. Ve a "Resumen" (`/app/overview`), usa el botón "Conectar mis datos", sube un archivo
3. En Supabase, revisa que ese archivo quedó guardado a nombre de **ese cliente** (no de
   Cliente Cero)
4. Recarga la pantalla — debe mostrar la plata real del cliente, no el número de mentira

Esa prueba es la única que falta y **nadie más que tú (o un cliente real) la puede hacer**,
porque necesita una sesión de login real.

## Archivos que el chat nuevo debe leer primero

- `openspec/changes/real-data-ingestion-mvp/RUNBOOK.md` — los 6 pasos con comandos
- `openspec/changes/real-data-ingestion-mvp/proposal.md` — qué se construyó y por qué
- `ARCHITECTURE.md` — Decisión #22 (el resumen técnico completo)
