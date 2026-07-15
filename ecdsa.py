# Algoritmo ECDSA — generación de claves, firma y verificación desde cero

import random
from grupos import inverso_modular, suma_puntos, multiplicacion_escalar, orden_punto

# Parámetros de la curva por defecto: y² ≡ x³ + 4x + 7 (mod 11)
# Nota: la misma ecuación mod 23 da |E|=24 (no primo), lo que rompe ECDSA.
#       Mod 11 da |E|=13 (primo), que permite inversos mod n para todo k ∈ [1,n-1].
_A, _B, _P = 4, 7, 11
_G = (1, 1)  # Punto generador — verificación: 1²=1 ≡ 1³+4·1+7=12≡1 (mod 11) ✓
_N = orden_punto(_G, _A, _P)  # Orden de G = |E| = 13 (primo)

CURVA = {
    'a': _A,
    'b': _B,
    'p': _P,
    'G': _G,
    'n': _N,
    'nombre': f'y² ≡ x³ + {_A}x + {_B}  (mod {_P})',
}


# ---------------------------------------------------------------------------
# Hash educativo simplificado
# ADVERTENCIA: solo para demostración didáctica, NO usar en producción.
# ---------------------------------------------------------------------------

def hash_mensaje(mensaje, n, verbose=True):
    """
    Hash simplificado: suma de valores ASCII del mensaje, módulo n.
    En ECDSA real se usa SHA-256 o similar; aquí se simplifica para la demo.
    """
    valores = [ord(c) for c in mensaje]
    total = sum(valores)
    h = total % n
    if verbose:
        suma_str = ' + '.join(str(v) for v in valores)
        print(f"\n  [Hash]  h('{mensaje}')")
        print(f"         = Σ ASCII(c) mod n")
        print(f"         = {suma_str}")
        print(f"         = {total} mod {n} = {h}")
    return h


# ---------------------------------------------------------------------------
# Generación de claves
# ---------------------------------------------------------------------------

def generar_claves(curva=None, verbose=True):
    """
    Genera el par de claves ECDSA:
      d  : clave privada, entero aleatorio en [1, n-1]
      Q  : clave pública, Q = d·G
    """
    if curva is None:
        curva = CURVA
    a, p, G, n = curva['a'], curva['p'], curva['G'], curva['n']

    if verbose:
        print("\n" + "=" * 60)
        print("  GENERACIÓN DE CLAVES ECDSA")
        print("=" * 60)
        print(f"  Curva : {curva['nombre']}")
        print(f"  G = {G}  (punto generador)")
        print(f"  n = {n}  (orden de G, es decir n·G = O)")

    d = random.randint(1, n - 1)

    if verbose:
        print(f"\n  Paso 1: elegir clave privada d ∈ [1, n-1] = [1, {n-1}]")
        print(f"  d = {d}  (aleatoria)")
        print(f"\n  Paso 2: calcular clave pública Q = d·G = {d}·{G}")

    Q = multiplicacion_escalar(d, G, a, p, verbose)

    if verbose:
        print(f"\n  ✓  Clave privada : d = {d}  (¡MANTENER EN SECRETO!)")
        print(f"  ✓  Clave pública  : Q = {Q}  (puede publicarse)")

    return d, Q


# ---------------------------------------------------------------------------
# Firma
# ---------------------------------------------------------------------------

def firmar(mensaje, d, curva=None, k=None, verbose=True):
    """
    Firma un mensaje con ECDSA mostrando cada paso intermedio.
      mensaje : cadena a firmar
      d       : clave privada
      k       : nonce (opcional; si se omite se elige aleatoriamente)
    Retorna (r, s).
    """
    if curva is None:
        curva = CURVA
    a, p, G, n = curva['a'], curva['p'], curva['G'], curva['n']

    if verbose:
        print("\n" + "=" * 60)
        print("  FIRMA ECDSA")
        print("=" * 60)
        print(f"  Mensaje       : '{mensaje}'")
        print(f"  Clave privada : d = {d}")
        print(f"  n             = {n}")

    # Paso 1: hash del mensaje
    if verbose:
        print(f"\n  Paso 1: calcular hash del mensaje")
    h = hash_mensaje(mensaje, n, verbose)

    # Paso 2: nonce k
    k_externo = k is not None
    if k is None:
        k = random.randint(1, n - 1)
    if verbose:
        fuente = "dado externamente (para la demo)" if k_externo else "elegido aleatoriamente en [1, n-1]"
        print(f"\n  Paso 2: elegir nonce k")
        print(f"  k = {k}  ({fuente})")
        print(f"  ADVERTENCIA: k debe ser ÚNICO por firma; reutilizarlo expone la clave privada.")

    # Paso 3: R = k·G
    if verbose:
        print(f"\n  Paso 3: calcular R = k·G = {k}·{G}")
    R = multiplicacion_escalar(k, G, a, p, verbose)

    if R is None:
        raise ValueError("k·G = O; elige otro nonce k.")

    # Paso 4: r = R.x mod n
    r = R[0] % n
    if verbose:
        print(f"\n  Paso 4: r = R.x mod n = {R[0]} mod {n} = {r}")
    if r == 0:
        raise ValueError("r = 0; elige otro nonce k.")

    # Paso 5: s = k⁻¹·(h + d·r) mod n
    if verbose:
        print(f"\n  Paso 5: calcular s = k⁻¹·(h + d·r) mod n")
        print(f"  s = {k}⁻¹ · ({h} + {d}·{r}) mod {n}")
        print(f"  s = {k}⁻¹ · ({h} + {d*r}) mod {n}")
        hdrc = (h + d * r) % n
        print(f"  s = {k}⁻¹ · {hdrc}  mod {n}")

    k_inv = inverso_modular(k, n, verbose)
    s = (k_inv * (h + d * r)) % n

    if verbose:
        print(f"  s = {k_inv} · {(h + d*r) % n} mod {n} = {s}")

    if s == 0:
        raise ValueError("s = 0; elige otro nonce k.")

    if verbose:
        print(f"\n  ✓  Firma: (r, s) = ({r}, {s})")

    return r, s


# ---------------------------------------------------------------------------
# Verificación
# ---------------------------------------------------------------------------

def verificar(mensaje, firma, Q, curva=None, verbose=True):
    """
    Verifica una firma ECDSA mostrando la prueba algebraica completa.
      mensaje : cadena original
      firma   : tupla (r, s)
      Q       : clave pública del firmante
    Retorna True si la firma es válida, False en caso contrario.
    """
    if curva is None:
        curva = CURVA
    a, p, G, n = curva['a'], curva['p'], curva['G'], curva['n']
    r, s = firma

    if verbose:
        print("\n" + "=" * 60)
        print("  VERIFICACIÓN ECDSA")
        print("=" * 60)
        print(f"  Mensaje      : '{mensaje}'")
        print(f"  Firma        : (r, s) = ({r}, {s})")
        print(f"  Clave pública: Q = {Q}")
        print(f"  n            = {n}")

    # Rango válido
    if not (1 <= r <= n - 1 and 1 <= s <= n - 1):
        if verbose:
            print(f"\n  ✗  r o s fuera del rango [1, {n-1}]  →  FIRMA INVÁLIDA")
        return False

    # Paso 1: hash
    if verbose:
        print(f"\n  Paso 1: calcular hash del mensaje")
    h = hash_mensaje(mensaje, n, verbose)

    # Paso 2: w = s⁻¹ mod n
    if verbose:
        print(f"\n  Paso 2: w = s⁻¹ mod n = {s}⁻¹ mod {n}")
    w = inverso_modular(s, n, verbose)
    if verbose:
        print(f"  w = {w}")

    # Paso 3: u1, u2
    u1 = (h * w) % n
    u2 = (r * w) % n
    if verbose:
        print(f"\n  Paso 3: calcular u₁ y u₂")
        print(f"  u₁ = h·w mod n  = {h}·{w} mod {n} = {h*w} mod {n} = {u1}")
        print(f"  u₂ = r·w mod n  = {r}·{w} mod {n} = {r*w} mod {n} = {u2}")

    # Paso 4: X = u1·G + u2·Q
    if verbose:
        print(f"\n  Paso 4: calcular X = u₁·G + u₂·Q")
        print(f"  X = {u1}·{G}  +  {u2}·{Q}")

    X1 = multiplicacion_escalar(u1, G, a, p, verbose)
    X2 = multiplicacion_escalar(u2, Q, a, p, verbose)

    if verbose:
        print(f"\n  u₁·G = {X1}")
        print(f"  u₂·Q = {X2}")
        print(f"\n  Sumando:")

    X = suma_puntos(X1, X2, a, p, verbose)

    if verbose:
        print(f"\n  X = u₁·G + u₂·Q = {X}")

    if X is None:
        if verbose:
            print("  ✗  X = O  →  FIRMA INVÁLIDA")
        return False

    # Paso 5: verificar X.x ≡ r (mod n)
    v = X[0] % n
    if verbose:
        print(f"\n  Paso 5: verificar X.x ≡ r (mod n)")
        print(f"  X.x mod n = {X[0]} mod {n} = {v}")
        print(f"  r          = {r}")

    valida = (v == r)

    if verbose:
        if valida:
            print(f"  ✓  {v} == {r}  →  FIRMA VÁLIDA")
        else:
            print(f"  ✗  {v} ≠ {r}  →  FIRMA INVÁLIDA")

    # Prueba algebraica (solo si es válida)
    if verbose and valida:
        print(f"\n  ─── Prueba Algebraica ───")
        print(f"  Queremos demostrar que u₁·G + u₂·Q = k·G = R")
        print(f"  Sabemos:")
        print(f"    Q = d·G")
        print(f"    u₁ = h·w,  u₂ = r·w,  w = s⁻¹")
        print(f"  Entonces:")
        print(f"    u₁·G + u₂·Q = h·w·G + r·w·(d·G)")
        print(f"                = w·(h + r·d)·G")
        print(f"                = s⁻¹·(h + d·r)·G")
        print(f"  Como s = k⁻¹·(h + d·r)  →  s⁻¹·(h+d·r) = k")
        print(f"  Por tanto:  u₁·G + u₂·Q = k·G = R")
        print(f"  Y se cumple R.x mod n = r  ✓")

    return valida
