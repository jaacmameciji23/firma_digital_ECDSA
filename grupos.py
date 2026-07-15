# Operaciones algebraicas sobre curvas elípticas E(Z_p) — implementación desde cero


def euclides_extendido(a, b, verbose=True):
    """
    Algoritmo de Euclides Extendido.
    Retorna (mcd, x, y) tal que a*x + b*y = mcd(a, b).
    """
    if verbose:
        print(f"\n    [Euclides Extendido] Buscando x, y tal que {a}·x + {b}·y = mcd")

    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    paso = 0

    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
        paso += 1
        if verbose:
            print(f"      Paso {paso}: q={q}  →  r={old_r}, s={old_s}, t={old_t}")

    if verbose:
        print(f"      Resultado: mcd={old_r},  {a}·({old_s}) + {b}·({old_t}) = {old_r}")

    return old_r, old_s, old_t


def inverso_modular(a, p, verbose=True):
    """
    Calcula a^(-1) mod p usando el Algoritmo de Euclides Extendido.
    Requiere mcd(a, p) = 1.
    """
    a_mod = a % p
    if verbose:
        print(f"\n    [Inverso Modular] {a} mod {p} = {a_mod}  →  buscando {a_mod}⁻¹ mod {p}")

    mcd, x, _ = euclides_extendido(a_mod, p, verbose)
    if mcd != 1:
        raise ValueError(f"No existe inverso de {a} mod {p}: mcd({a_mod}, {p}) = {mcd}")

    inv = x % p
    if verbose:
        print(f"    => {a}⁻¹ mod {p} = {inv}   "
              f"[verificación: {a_mod}·{inv} = {a_mod * inv} ≡ {(a_mod * inv) % p} (mod {p})]")
    return inv


def suma_puntos(P, Q, a, p, verbose=True):
    """
    Suma de puntos en la curva elíptica y² ≡ x³ + ax + b (mod p).
    None representa el punto en el infinito O (elemento neutro).
    """
    if verbose:
        Ps = "O" if P is None else str(P)
        Qs = "O" if Q is None else str(Q)
        print(f"\n  [Suma de Puntos]  {Ps} + {Qs}  (mod {p})")

    if P is None:
        if verbose:
            print(f"  P = O (neutro)  =>  resultado = Q")
        return Q
    if Q is None:
        if verbose:
            print(f"  Q = O (neutro)  =>  resultado = P")
        return P

    x1, y1 = P
    x2, y2 = Q

    # Puntos inversos: misma abscisa, ordenadas opuestas mod p
    if x1 == x2 and (y1 + y2) % p == 0:
        if verbose:
            print(f"  y₁ + y₂ = {y1} + {y2} = {y1 + y2} ≡ 0 (mod {p})"
                  f"  =>  P y Q son inversos, resultado = O")
        return None

    if P == Q:
        if verbose:
            print(f"  Caso: P = Q  (duplicación de punto)")
            print(f"  Fórmula: λ = (3x₁² + a) · (2y₁)⁻¹  mod p")
            print(f"           λ = (3·{x1}² + {a}) · (2·{y1})⁻¹  mod {p}")
        num = (3 * x1 * x1 + a) % p
        den = (2 * y1) % p
        if verbose:
            print(f"           numerador  = 3·{x1}² + {a} = {3*x1*x1+a} ≡ {num} (mod {p})")
            print(f"           denominador = 2·{y1} = {2*y1} ≡ {den} (mod {p})")
    else:
        if verbose:
            print(f"  Caso: P ≠ Q  (suma estándar)")
            print(f"  Fórmula: λ = (y₂ - y₁) · (x₂ - x₁)⁻¹  mod p")
            print(f"           λ = ({y2} - {y1}) · ({x2} - {x1})⁻¹  mod {p}")
        num = (y2 - y1) % p
        den = (x2 - x1) % p
        if verbose:
            print(f"           numerador  = {y2} - {y1} = {y2-y1} ≡ {num} (mod {p})")
            print(f"           denominador = {x2} - {x1} = {x2-x1} ≡ {den} (mod {p})")

    lam = (num * inverso_modular(den, p, verbose)) % p
    if verbose:
        print(f"  λ = {num} · {inverso_modular(den, p, verbose=False)} mod {p} = {lam}")

    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p

    if verbose:
        print(f"  x₃ = λ² - x₁ - x₂ = {lam}² - {x1} - {x2}"
              f" = {lam**2 - x1 - x2} ≡ {x3} (mod {p})")
        print(f"  y₃ = λ(x₁ - x₃) - y₁ = {lam}·({x1} - {x3}) - {y1}"
              f" = {lam*(x1-x3) - y1} ≡ {y3} (mod {p})")
        print(f"  => P + Q = ({x3}, {y3})")

    return (x3, y3)


def multiplicacion_escalar(k, G, a, p, verbose=True):
    """
    Calcula k·G usando el algoritmo double-and-add (MSB first).
    Complejidad: O(log k) sumas de puntos.
    """
    if verbose:
        bits = bin(k)[2:]
        print(f"\n[Multiplicación Escalar]  k = {k},  G = {G}")
        print(f"  {k} en binario = {bits}  ({len(bits)} bits)")
        print(f"  Recorro bits de izquierda a derecha:")
        print(f"    bit=0 → solo doblar R")
        print(f"    bit=1 → doblar R, luego sumar G")

    bits = bin(k)[2:]
    R = None  # punto en el infinito O

    for i, bit in enumerate(bits):
        # Doblar (siempre, excepto cuando R aún es O)
        if R is not None:
            if verbose:
                print(f"\n  ── Bit {i} = '{bit}' ──  Doblar: R ← 2·R")
            R = suma_puntos(R, R, a, p, verbose)

        # Sumar G si el bit es 1
        if bit == '1':
            if R is None:
                if verbose:
                    print(f"\n  ── Bit {i} = '{bit}' ──  R = O → R ← G = {G}")
                R = G
            else:
                if verbose:
                    print(f"\n  ── Bit {i} = '{bit}' ──  Sumar: R ← R + G")
                R = suma_puntos(R, G, a, p, verbose)

    if verbose:
        print(f"\n  => {k}·G = {R}")
    return R


def orden_punto(G, a, p):
    """Calcula el orden del punto G: el menor n > 0 tal que n·G = O."""
    Q = G
    n = 1
    while Q is not None:
        Q = suma_puntos(Q, G, a, p, verbose=False)
        n += 1
    return n


def listar_puntos(a, b, p, verbose=True):
    """
    Lista todos los puntos afines de la curva y² ≡ x³ + ax + b (mod p)
    más el punto en el infinito O.
    """
    if verbose:
        print(f"\n[Listar Puntos]  Curva: y² ≡ x³ + {a}x + {b}  (mod {p})")
        print(f"  Para cada x ∈ [0, {p-1}] se resuelve y² ≡ x³+{a}x+{b} (mod {p}):")

    puntos = []
    for x in range(p):
        rhs = (pow(x, 3, p) + a * x + b) % p
        ys = [y for y in range(p) if pow(y, 2, p) == rhs]
        if verbose:
            if ys:
                print(f"  x={x:2d}: {x}³+{a}·{x}+{b} ≡ {rhs:2d} (mod {p})"
                      f"  →  y ∈ {ys}  →  {[(x, y) for y in ys]}")
            else:
                print(f"  x={x:2d}: {x}³+{a}·{x}+{b} ≡ {rhs:2d} (mod {p})  →  sin solución")
        for y in ys:
            puntos.append((x, y))

    todos = puntos + [None]
    if verbose:
        print(f"\n  Puntos afines ({len(puntos)}): {puntos}")
        print(f"  + O (punto en el infinito)")
        print(f"  |E(Z_{p})| = {len(todos)}")
    return todos
