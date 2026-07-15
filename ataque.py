# Ataque por reutilización de nonce en ECDSA — implementación didáctica

from grupos import inverso_modular
from ecdsa import CURVA, hash_mensaje, firmar, generar_claves


def ataque_reutilizacion_nonce(mensaje1, firma1, mensaje2, firma2, curva=None, verbose=True):
    """
    Recupera la clave privada d cuando se firma con el mismo nonce k dos veces.

    Fundamento matemático:
      Si se usan el mismo k para firmar m1 y m2, entonces r₁ = r₂ = r
      (porque R = k·G es el mismo punto).

      s₁ = k⁻¹(h₁ + d·r) mod n
      s₂ = k⁻¹(h₂ + d·r) mod n

      Restando:  s₁ - s₂ = k⁻¹(h₁ - h₂)  mod n
      Despejando k:  k = (h₁ - h₂)·(s₁ - s₂)⁻¹  mod n

      Con k conocido, de s₁ = k⁻¹(h₁ + d·r) se despeja d:
        d = (s₁·k - h₁)·r⁻¹  mod n
    """
    if curva is None:
        curva = CURVA
    n = curva['n']

    r1, s1 = firma1
    r2, s2 = firma2

    if verbose:
        print("\n" + "=" * 60)
        print("  ATAQUE: REUTILIZACIÓN DE NONCE (k fijo)")
        print("=" * 60)
        print(f"  Mensaje 1: '{mensaje1}'  →  firma (r₁,s₁) = ({r1},{s1})")
        print(f"  Mensaje 2: '{mensaje2}'  →  firma (r₂,s₂) = ({r2},{s2})")

    if r1 != r2:
        if verbose:
            print(f"\n  r₁={r1} ≠ r₂={r2}: el nonce NO fue reutilizado.")
            print(f"  El ataque no aplica con estas firmas.")
        return None

    if verbose:
        print(f"\n  ¡ r₁ = r₂ = {r1} !  →  mismo R → mismo nonce k  →  ataque posible")
    r = r1

    # Paso 1: hashes
    if verbose:
        print(f"\n  Paso 1: calcular los hashes de ambos mensajes")
    h1 = hash_mensaje(mensaje1, n, verbose=verbose)
    h2 = hash_mensaje(mensaje2, n, verbose=verbose)

    if h1 == h2:
        if verbose:
            print(f"\n  h₁ = h₂ = {h1}: los mensajes tienen el mismo hash; el ataque no puede distinguirlos.")
        return None

    # Paso 2: recuperar k
    if verbose:
        print(f"\n  Paso 2: recuperar el nonce k")
        print(f"  De  s₁ - s₂ = k⁻¹(h₁ - h₂)  mod n  despejamos:")
        print(f"  k = (h₁ - h₂) · (s₁ - s₂)⁻¹  mod n")
        print(f"  k = ({h1} - {h2}) · ({s1} - {s2})⁻¹  mod {n}")

    dif_h = (h1 - h2) % n
    dif_s = (s1 - s2) % n

    if verbose:
        print(f"  k = {dif_h} · {dif_s}⁻¹  mod {n}")

    dif_s_inv = inverso_modular(dif_s, n, verbose=verbose)
    k_recuperado = (dif_h * dif_s_inv) % n

    if verbose:
        print(f"  k = {dif_h} · {dif_s_inv} mod {n} = {k_recuperado}")

    # Paso 3: recuperar d
    if verbose:
        print(f"\n  Paso 3: recuperar la clave privada d")
        print(f"  De  s₁ = k⁻¹(h₁ + d·r)  despejamos d:")
        print(f"  s₁·k = h₁ + d·r  mod n")
        print(f"  d·r  = s₁·k - h₁  mod n")
        print(f"  d    = (s₁·k - h₁) · r⁻¹  mod n")
        print(f"  d    = ({s1}·{k_recuperado} - {h1}) · {r}⁻¹  mod {n}")

    s1k = (s1 * k_recuperado) % n

    if verbose:
        print(f"  d    = ({s1k} - {h1}) · {r}⁻¹  mod {n}")

    s1k_h1 = (s1k - h1) % n

    if verbose:
        print(f"  d    = {s1k_h1} · {r}⁻¹  mod {n}")

    r_inv = inverso_modular(r, n, verbose=verbose)
    d_recuperado = (s1k_h1 * r_inv) % n

    if verbose:
        print(f"  d    = {s1k_h1} · {r_inv} mod {n} = {d_recuperado}")
        print(f"\n  ✓  Nonce recuperado  : k = {k_recuperado}")
        print(f"  ✓  Clave privada     : d = {d_recuperado}  ← ¡COMPROMETIDA!")

    return k_recuperado, d_recuperado


def demostrar_ataque(curva=None):
    """
    Demostración completa del ataque: genera claves reales, firma dos mensajes
    con el mismo k, luego recupera la clave privada desde las firmas públicas.
    """
    if curva is None:
        curva = CURVA

    print("\n" + "#" * 60)
    print("  DEMOSTRACIÓN COMPLETA: ATAQUE POR NONCE REUTILIZADO")
    print("#" * 60)

    # 1. La víctima genera sus claves
    print("\n[1] La víctima genera su par de claves:")
    d, Q = generar_claves(curva, verbose=False)
    print(f"    d (privada, SECRETA) = {d}")
    print(f"    Q (pública, visible) = {Q}")

    # 2. La víctima comete el error de reutilizar k
    k_fijo = 7  # nonce reutilizado (el "error" crítico)
    mensaje1 = "Transferencia: 50 EUR a cuenta 1234"
    mensaje2 = "Transferencia: 200 EUR a cuenta 5678"

    print(f"\n[2] La víctima firma DOS mensajes con el MISMO nonce k={k_fijo}:")
    print(f"    (Error crítico: k debe ser único e impredecible en cada firma)")
    print()

    r1, s1 = firmar(mensaje1, d, curva, k=k_fijo, verbose=False)
    r2, s2 = firmar(mensaje2, d, curva, k=k_fijo, verbose=False)

    print(f"    Firma de '{mensaje1}':")
    print(f"      (r, s) = ({r1}, {s1})")
    print(f"    Firma de '{mensaje2}':")
    print(f"      (r, s) = ({r2}, {s2})")
    print(f"\n    Observación: r₁ = {r1} = r₂ = {r2}  →  mismo k!")

    # 3. El atacante ejecuta el ataque
    print(f"\n[3] El atacante, con acceso solo a mensajes y firmas públicas, ejecuta:")
    resultado = ataque_reutilizacion_nonce(
        mensaje1, (r1, s1),
        mensaje2, (r2, s2),
        curva,
    )

    # 4. Verificación
    if resultado:
        k_rec, d_rec = resultado
        print(f"\n[4] Verificación del resultado:")
        print(f"    d real        = {d}")
        print(f"    d recuperado  = {d_rec}")
        if d_rec == d:
            print(f"    ✓  ¡ATAQUE EXITOSO! La clave privada fue completamente comprometida.")
            print(f"    El atacante puede ahora forjar firmas válidas por la víctima.")
        else:
            print(f"    ✗  Discrepancia inesperada (revisar parámetros de la curva).")
