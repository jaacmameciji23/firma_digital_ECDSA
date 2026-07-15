# Interfaz interactiva de la demo didáctica ECDSA

from grupos import listar_puntos, orden_punto, multiplicacion_escalar
from ecdsa import CURVA, generar_claves, firmar, verificar


def cabecera():
    print("\n" + "=" * 60)
    print("  DEMO DIDÁCTICA: FIRMA DIGITAL ECDSA")
    print("=" * 60)
    print(f"  Curva : {CURVA['nombre']}")
    print(f"  G     = {CURVA['G']}  (punto generador)")
    print(f"  n     = {CURVA['n']}  (orden de G,  n·G = O)")
    print("=" * 60)


def menu():
    print("\n  Opciones:")
    print("  1. Listar todos los puntos de E(Z_p)")
    print("  2. Generar par de claves (d, Q)")
    print("  3. Firmar un mensaje")
    print("  4. Verificar una firma")
    print("  5. Ataque: recuperar clave por nonce reutilizado")
    print("  6. Flujo completo automático (1 → 5)")
    print("  0. Salir")


def pedir_opcion(prompt="  Opción: "):
    return input(prompt).strip()


# ---------------------------------------------------------------------------
# Flujos individuales
# ---------------------------------------------------------------------------

def flujo_listar():
    listar_puntos(CURVA['a'], CURVA['b'], CURVA['p'])


def flujo_generar():
    d, Q = generar_claves(CURVA, verbose=True)
    return d, Q


def flujo_firmar(d):
    print(f"\n  Clave privada activa: d = {d}")
    msg = input("  Mensaje a firmar (Enter = 'Hola Mundo'): ").strip() or "Hola Mundo"
    r, s = firmar(msg, d, CURVA, verbose=True)
    return msg, (r, s)


def flujo_verificar(mensaje, firma, Q):
    print(f"\n  Verificando la firma guardada en sesión:")
    print(f"    Mensaje : '{mensaje}'")
    print(f"    Firma   : {firma}")
    print(f"    Q       : {Q}")
    verificar(mensaje, firma, Q, CURVA, verbose=True)


def flujo_ataque():
    from ataque import demostrar_ataque
    demostrar_ataque(CURVA)


def flujo_completo():
    from ataque import demostrar_ataque

    print("\n" + "#" * 60)
    print("  FLUJO COMPLETO: Curva → Claves → Firma → Verificación → Ataque")
    print("#" * 60)

    # 1. Mostrar la curva
    print("\n>>> [1/5]  Puntos de la curva")
    listar_puntos(CURVA['a'], CURVA['b'], CURVA['p'])

    # 2. Generar claves
    print("\n>>> [2/5]  Generación de claves")
    d, Q = generar_claves(CURVA, verbose=True)

    # 3. Firmar
    print("\n>>> [3/5]  Firma")
    msg = input("  Mensaje a firmar (Enter = 'Demo ECDSA'): ").strip() or "Demo ECDSA"
    r, s = firmar(msg, d, CURVA, verbose=True)

    # 4. Verificar firma legítima
    print("\n>>> [4/5]  Verificación")
    print("  — Verificando firma LEGÍTIMA:")
    verificar(msg, (r, s), Q, CURVA, verbose=True)

    print("\n  — Verificando firma con MENSAJE ALTERADO (debe fallar):")
    verificar(msg + " [alterado]", (r, s), Q, CURVA, verbose=True)

    # 5. Ataque
    print("\n>>> [5/5]  Ataque por reutilización de nonce")
    demostrar_ataque(CURVA)


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------

def main():
    cabecera()

    # Estado de sesión
    sesion = {'d': None, 'Q': None, 'mensaje': None, 'firma': None}

    while True:
        menu()
        op = pedir_opcion()

        if op == '0':
            print("\n  Hasta luego.\n")
            break

        elif op == '1':
            flujo_listar()

        elif op == '2':
            sesion['d'], sesion['Q'] = flujo_generar()

        elif op == '3':
            if sesion['d'] is None:
                print("\n  Primero genera las claves (opción 2).")
                continue
            sesion['mensaje'], sesion['firma'] = flujo_firmar(sesion['d'])

        elif op == '4':
            if sesion['firma'] is None:
                print("\n  Primero firma un mensaje (opción 3).")
                continue
            flujo_verificar(sesion['mensaje'], sesion['firma'], sesion['Q'])

        elif op == '5':
            flujo_ataque()

        elif op == '6':
            flujo_completo()

        else:
            print("  Opción no reconocida.")

        input("\n  [Enter para continuar...]")


if __name__ == "__main__":
    main()
