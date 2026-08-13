# Constantes tributarias para Colombia
#
# UVT_2025 y UVT_2026 corregidos 2026-08-12 (ver hermes-multi-tenant-wrapper's sibling fix):
# este archivo tenía un solo `UVT_2026 = 49799`, pero 49799 es en realidad la UVT de 2025
# (Resolución DIAN pertinente a 2025), no la de 2026. La declaración de Renta 2026 evalúa
# INGRESOS DE 2025, así que los umbrales de "¿toca declarar?" deben seguir usando la UVT 2025
# (valor sin cambios, solo renombrado) — coincide con el $69.7M de la pieza de marketing
# (1400 UVT × $49.799). UVT_2026 ($52.374, Resolución DIAN 238 del 15-dic-2025) es la UVT del
# año en curso, para sanciones/umbrales vigentes hoy (p. ej. elegibilidad de Régimen Simple).

UVT_2025 = 49799  # Valor de la UVT para 2025 — aplica a la declaración de Renta 2026 (ingresos 2025)
UVT_2026 = 52374  # Valor de la UVT para 2026 — Resolución DIAN 238 del 15-dic-2025

# Umbrales en UVT (declaración de renta — evaluados contra ingresos/patrimonio de 2025)
# Fuente: art. 592 y ss. ET; valores en pesos verificados contra la "Guía de Declaración de
# Renta DIAN" (AG 2025 / vigencia 2026) — ingresos/compras/consignaciones 1.400 UVT, patrimonio
# 4.500 UVT, ambos sobre UVT_2025 ($49.799).
UMBRAL_RENTA_UVT = 1400  # Ingresos brutos, compras y consumos, consignaciones bancarias
UMBRAL_IVA_UVT = 3500
UMBRAL_PATRIMONIO_UVT = 4500  # Patrimonio bruto al 31 de dic. del año gravable

# Umbrales en Pesos (COP) — usan UVT_2025 porque evalúan el año gravable 2025
UMBRAL_RENTA_COP = UMBRAL_RENTA_UVT * UVT_2025
UMBRAL_IVA_COP = UMBRAL_IVA_UVT * UVT_2025
UMBRAL_PATRIMONIO_COP = UMBRAL_PATRIMONIO_UVT * UVT_2025

# Tasas por defecto
TASA_RENTA_DEFAULT = 0.35
TASA_IVA_DEFAULT = 0.19
