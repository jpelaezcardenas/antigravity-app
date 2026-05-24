#!/usr/bin/env python3
"""
DIAGNÓSTICO AUTOMÁTICO DE ROUTERS
Ejecuta esto para encontrar qué router está roto
"""

import sys
import traceback

def diagnose_router(router_name, module_path):
    """Intenta importar un router y reporta qué falla"""
    print(f"\n{'='*70}")
    print(f"Diagnosticando: {router_name}")
    print(f"Module: {module_path}")
    print(f"{'='*70}")

    try:
        # Paso 1: Importar el módulo
        print(f"[1] Intentando importar {module_path}...")
        mod = __import__(module_path, fromlist=['router'])
        print(f"    ✓ Módulo importado exitosamente")

        # Paso 2: Verificar que existe 'router'
        print(f"[2] Buscando 'router' en {module_path}...")
        if hasattr(mod, 'router'):
            router = getattr(mod, 'router')
            print(f"    ✓ 'router' encontrado: {type(router)}")
        else:
            print(f"    ✗ ERROR: No hay 'router' en {module_path}")
            print(f"    Atributos disponibles: {dir(mod)}")
            return False

        # Paso 3: Verificar que es un APIRouter
        from fastapi import APIRouter
        if isinstance(router, APIRouter):
            print(f"    ✓ Es un APIRouter válido")
            print(f"    ✓ ROUTER OK: {router_name} está listo para registrar")
            return True
        else:
            print(f"    ✗ ERROR: 'router' no es un APIRouter")
            print(f"    Tipo encontrado: {type(router)}")
            return False

    except ModuleNotFoundError as e:
        print(f"    ✗ MODULO NO ENCONTRADO")
        print(f"    Error: {e}")
        print(f"    Falta dependencia: {str(e).split()[-1]}")
        return False

    except ImportError as e:
        print(f"    ✗ ERROR DE IMPORTACION")
        print(f"    Error: {e}")
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"    ✗ ERROR DESCONOCIDO")
        print(f"    Tipo: {type(e).__name__}")
        print(f"    Mensaje: {e}")
        traceback.print_exc()
        return False


def main():
    """Diagnostica todos los routers"""

    routers = [
        ("auth_router", "presentation.auth_endpoints"),
        ("pulso_router", "presentation.pulso_endpoints"),
        ("centinela_router", "presentation.centinela_endpoints"),
        ("cobro_router", "presentation.cobro_endpoints"),
        ("agents_router", "presentation.agents_endpoints"),
        ("taty_router", "presentation.taty_endpoints"),
    ]

    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " DIAGNÓSTICO DE ROUTERS - DAY 6 MVP ".center(68) + "║")
    print("╚" + "═"*68 + "╝")

    results = {}
    for name, path in routers:
        results[name] = diagnose_router(name, path)

    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN")
    print(f"{'='*70}")

    ok_count = sum(1 for v in results.values() if v)
    total = len(results)

    for name, success in results.items():
        status = "✓ OK" if success else "✗ FALLA"
        print(f"{status:8} {name}")

    print(f"\nTotal: {ok_count}/{total} routers funcionando")

    # Diagnóstico final
    print(f"\n{'='*70}")
    print("DIAGNÓSTICO FINAL")
    print(f"{'='*70}")

    if ok_count == total:
        print("✓ TODOS LOS ROUTERS ESTÁN OK")
        print("  Si siguen fallando en Railway, es un issue de deployment/env vars")
    else:
        print(f"✗ {total - ok_count} ROUTER(S) CON ERROR")
        failed = [k for k, v in results.items() if not v]
        for f in failed:
            print(f"  - {f}")
        print("\nPRÓXIMOS PASOS:")
        print("1. Revisar los errores específicos arriba")
        print("2. Arreglar la importación en el archivo del router")
        print("3. Hacer commit y push")
        print("4. Railway auto-redeploy")

    return 0 if ok_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
