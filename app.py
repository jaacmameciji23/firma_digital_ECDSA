"""
Demo didáctica ECDSA — interfaz web con Streamlit.
Toda la lógica matemática vive en grupos.py / ecdsa.py / ataque.py.
La salida print() se captura con contextlib.redirect_stdout.
"""

import io
import contextlib
import random

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from grupos import listar_puntos, multiplicacion_escalar, suma_puntos, inverso_modular
from ecdsa import CURVA, generar_claves, firmar, verificar
from ataque import demostrar_ataque

# ─────────────────────────────────────────────────────────────
# Página
# ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="Demo ECDSA", page_icon="🔐", layout="wide")

# ─────────────────────────────────────────────────────────────
# Helper: capturar stdout
# ─────────────────────────────────────────────────────────────

def capturar(func, *args, **kwargs):
    """Ejecuta func capturando su stdout. Retorna (resultado, texto)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        resultado = func(*args, **kwargs)
    return resultado, buf.getvalue()


def _hash_msg(mensaje, n):
    """Hash idéntico al de ecdsa.py pero sin prints."""
    return sum(ord(c) for c in mensaje) % n


# ─────────────────────────────────────────────────────────────
# Precomputar i·G para i = 1 … n-1 (cached; la curva no cambia)
# ─────────────────────────────────────────────────────────────

@st.cache_data
def _calcular_multiplos(_curva_id: str):
    G, a, p, n = CURVA["G"], CURVA["a"], CURVA["p"], CURVA["n"]
    res = {1: G}
    P = G
    for i in range(2, n):
        P = suma_puntos(P, G, a, p, verbose=False)
        res[i] = P
    return res


MULT = _calcular_multiplos(CURVA["nombre"])   # {1: 1·G, 2: 2·G, …, 12: 12·G}

# ─────────────────────────────────────────────────────────────
# Primitivas de dibujo
# ─────────────────────────────────────────────────────────────

def _fondo(ax, afines, p, excluir=()):
    """Dibuja todos los puntos de la curva como fondo gris claro."""
    bg = [pt for pt in afines if pt not in set(excluir)]
    if bg:
        ax.scatter(
            [pt[0] for pt in bg], [pt[1] for pt in bg],
            s=38, color="#e2e8f0", edgecolors="#94a3b8", linewidths=0.5, zorder=2,
        )
    ax.set_xlim(-0.8, p - 0.2)
    ax.set_ylim(-0.8, p - 0.2)
    ax.set_xticks(range(p))
    ax.set_yticks(range(p))
    ax.set_xlabel("x", fontsize=10)
    ax.set_ylabel("y", fontsize=10)
    ax.grid(True, alpha=0.18, linestyle="--")


def _dot(ax, pt, fc, ec, marker, size, leyenda, etiqueta, off=(7, 5)):
    if pt is None:
        return
    ax.scatter(
        [pt[0]], [pt[1]], s=size, color=fc, edgecolors=ec,
        linewidths=1.8, marker=marker, zorder=6, label=leyenda,
    )
    ax.annotate(
        etiqueta, pt, textcoords="offset points", xytext=off,
        fontsize=8.5, fontweight="bold", color=ec,
    )


def _arrow(ax, p1, p2, color="#94a3b8", rad=0.28):
    if p1 is None or p2 is None or p1 == p2:
        return
    ax.annotate(
        "", xy=(p2[0], p2[1]), xytext=(p1[0], p1[1]),
        arrowprops=dict(
            arrowstyle="->", color=color, lw=1.4,
            connectionstyle=f"arc3,rad={rad}",
        ),
        zorder=4,
    )


# ─────────────────────────────────────────────────────────────
# Gráficos específicos
# ─────────────────────────────────────────────────────────────

def grafico_claves(d, Q, afines):
    """
    Cadena de adición G → 2G → … → d·G = Q.
    Intermedios en azul claro, G en dorado, Q en verde.
    """
    G = CURVA["G"]
    p = CURVA["p"]
    relevantes = {MULT[i] for i in range(1, d + 1) if MULT.get(i)}

    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    _fondo(ax, afines, p, excluir=relevantes)

    # Intermedios 2G … (d-1)G
    for i in range(2, d):
        pt = MULT.get(i)
        if pt:
            ax.scatter([pt[0]], [pt[1]], s=60, color="#bfdbfe",
                       edgecolors="#3b82f6", linewidths=1.1, zorder=3)
            ax.annotate(f"{i}G", pt, textcoords="offset points",
                        xytext=(5, 3), fontsize=7.5, color="#1d4ed8")

    # G = 1·G (estrella dorada)
    _dot(ax, G, "gold", "#b45309", "*", 300,
         f"G = 1·G = {G}", "G", off=(-16, 7))

    # Q = d·G
    if Q == G:
        ax.annotate(
            f"G = Q  (d=1)", G, textcoords="offset points",
            xytext=(7, 7), fontsize=8.5, fontweight="bold", color="#b45309",
        )
    else:
        _dot(ax, Q, "#4ade80", "#15803d", "D", 170,
             f"Q = {d}·G = {Q}", "Q", off=(7, 6))

    # Flechas de la cadena: 1G → 2G → … → d·G
    seq = [MULT.get(i) for i in range(1, d + 1)]
    for i in range(len(seq) - 1):
        _arrow(ax, seq[i], seq[i + 1])

    ax.set_title(f"d = {d}   ⟹   Q = d·G = {Q}", fontsize=11, pad=8)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.85)
    plt.tight_layout()
    return fig


def grafico_firma(G, Q, R, r, afines):
    """
    G, Q y R = k·G marcados; línea vertical en x = r.
    """
    p = CURVA["p"]
    relevantes = {pt for pt in [G, Q, R] if pt}

    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    _fondo(ax, afines, p, excluir=relevantes)

    _dot(ax, G, "gold",    "#b45309", "*", 300, f"G = {G}",       "G",  (-16, 7))
    _dot(ax, Q, "#4ade80", "#15803d", "D", 170, f"Q = {Q}",       "Q",  (7, 6))
    if R not in (G, Q):
        _dot(ax, R, "#fca5a5", "#dc2626", "o", 170, f"R = k·G = {R}", "R",  (7, 6))
    elif R == Q:
        # R coincide con Q (posible con ciertos k)
        _dot(ax, R, "#fca5a5", "#dc2626", "o", 220, f"R = Q = {R}", "R=Q", (7, -14))

    if r is not None:
        ax.axvline(x=r, color="#dc2626", linestyle=":", alpha=0.5, lw=1.7)
        ax.text(r + 0.1, p - 1.6, f"r = {r}", color="#dc2626",
                fontsize=8.5, fontstyle="italic")

    ax.set_title(f"R = k·G = {R}   →   r = R.x mod n = {r}", fontsize=10, pad=8)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.85)
    plt.tight_layout()
    return fig


def grafico_verificacion(G, Q, u1G, u2Q, X, r, afines):
    """
    G, Q, u₁·G, u₂·Q, X = u₁G + u₂Q.
    Flechas muestran la suma final hacia X.
    """
    p = CURVA["p"]
    n = CURVA["n"]
    relevantes = {pt for pt in [G, Q, u1G, u2Q, X] if pt}

    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    _fondo(ax, afines, p, excluir=relevantes)

    specs = [
        (G,   "gold",    "#b45309", "*", 300, f"G = {G}",       "G",    (-16, 7)),
        (Q,   "#4ade80", "#15803d", "D", 155, f"Q = {Q}",       "Q",    (7, 6)),
        (u1G, "#93c5fd", "#1d4ed8", "s", 120, f"u₁·G = {u1G}", "u₁G", (7, 5)),
        (u2Q, "#d8b4fe", "#6d28d9", "s", 120, f"u₂·Q = {u2Q}", "u₂Q", (7, 5)),
        (X,   "#fca5a5", "#dc2626", "P", 190, f"X = {X}",       "X",   (7, 6)),
    ]
    for pt, fc, ec, mk, sz, ley, eti, off in specs:
        _dot(ax, pt, fc, ec, mk, sz, ley, eti, off)

    # Flechas: u1G y u2Q convergen en X
    _arrow(ax, u1G, X, color="#1d4ed8", rad=0.25)
    _arrow(ax, u2Q, X, color="#6d28d9", rad=-0.25)

    # Línea r si la verificación pasa
    if r is not None and X is not None and X[0] % n == r:
        ax.axvline(x=r, color="#dc2626", linestyle=":", alpha=0.45, lw=1.5)
        ax.text(r + 0.1, p - 1.6, f"X.x = r = {r}",
                color="#dc2626", fontsize=8, fontstyle="italic")

    ax.set_title("Verificación: X = u₁·G + u₂·Q", fontsize=10, pad=8)
    ax.legend(fontsize=8, loc="upper right", framealpha=0.85)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────
# Puntos de verificación (sin prints)
# ─────────────────────────────────────────────────────────────

def _ver_puntos(mensaje, firma, Q):
    """Calcula u₁·G, u₂·Q y X para la visualización."""
    r, s = firma
    G, a, p, n = CURVA["G"], CURVA["a"], CURVA["p"], CURVA["n"]
    h  = _hash_msg(mensaje, n)
    w  = inverso_modular(s, n, verbose=False)
    u1 = (h * w) % n
    u2 = (r * w) % n
    u1G = MULT.get(u1)                                           # None si u1 = 0
    u2Q = multiplicacion_escalar(u2, Q, a, p, verbose=False) if u2 else None
    if   u1G is None: X = u2Q
    elif u2Q is None: X = u1G
    else:             X = suma_puntos(u1G, u2Q, a, p, verbose=False)
    return u1G, u2Q, X


# ─────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────

_defaults = {
    "d":               None,
    "Q":               None,
    "keygen_log":      None,
    "d_original":      None,   # d ingresado en modo libre (puede ser > n-1)
    "k_nonce":         None,   # nonce usado en la firma → para calcular R
    "firma":           None,
    "mensaje_firmado": None,
    "firma_log":       None,
    "ver_orig":        None,   # (valida, log)
    "ver_orig_pts":    None,   # (u1G, u2Q, X)
    "ver_alt":         None,
    "ver_alt_pts":     None,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────
# Datos comunes
# ─────────────────────────────────────────────────────────────

_todos  = listar_puntos(CURVA["a"], CURVA["b"], CURVA["p"], verbose=False)
AFINES  = [p for p in _todos if p is not None]   # 12 puntos afines

# ─────────────────────────────────────────────────────────────
# Encabezado
# ─────────────────────────────────────────────────────────────

st.title("🔐 Demo Didáctica: Firma Digital ECDSA")
st.markdown(
    f"**Curva:** {CURVA['nombre']} &nbsp;·&nbsp; "
    f"**G** = `{CURVA['G']}` &nbsp;·&nbsp; "
    f"**n** = `{CURVA['n']}` (primo) &nbsp;·&nbsp; "
    f"Sin librerías criptográficas externas"
)
st.divider()

# ─────────────────────────────────────────────────────────────
# Pestañas
# ─────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "📐 Puntos del grupo",
    "🔑 Generar claves",
    "✍️ Firmar y verificar",
    "r💥 Ataque por nonce",
])


# ═════════════════════════════════════════════════════════════
# PESTAÑA 1 — Puntos del grupo
# ═════════════════════════════════════════════════════════════

with tab1:
    st.subheader(f"Todos los puntos de E(Z_{CURVA['p']})")
    st.markdown(
        f"La curva **{CURVA['nombre']}** tiene exactamente "
        f"**|E| = {CURVA['n']}** puntos. Como {CURVA['n']} es primo, "
        f"el grupo es cíclico y cualquier punto no nulo puede ser generador."
    )

    col_tabla, col_grafico = st.columns([1, 2], gap="large")

    with col_tabla:
        filas = [
            {
                "Punto": f"({x},{y})",
                "x": x, "y": y,
                "Nota": "⭐ G" if (x, y) == CURVA["G"] else "",
            }
            for x, y in AFINES
        ]
        filas.append({"Punto": "O", "x": "∞", "y": "∞", "Nota": "Neutro"})
        df = pd.DataFrame(filas)
        df.index = range(1, len(df) + 1)
        st.dataframe(df, use_container_width=True, height=440)
        st.caption(f"{len(AFINES)} puntos afines + O = **|E| = {len(_todos)}** ✓")

    with col_grafico:
        G_pt = CURVA["G"]
        normales = [p for p in AFINES if p != G_pt]
        fig, ax = plt.subplots(figsize=(6.5, 6.5))
        ax.scatter([p[0] for p in normales], [p[1] for p in normales],
                   s=90, color="steelblue", zorder=3, label="Punto de E")
        ax.scatter([G_pt[0]], [G_pt[1]], s=350, color="gold",
                   edgecolors="darkorange", linewidths=2, marker="*",
                   zorder=5, label=f"G = {G_pt}")
        for x, y in AFINES:
            ax.annotate(f"({x},{y})", (x, y), textcoords="offset points",
                        xytext=(6, 8 if (x, y) == G_pt else 5), fontsize=8, color="#111")
        ax.set_xlim(-0.8, CURVA["p"] - 0.2)
        ax.set_ylim(-0.8, CURVA["p"] - 0.2)
        ax.set_xticks(range(CURVA["p"]))
        ax.set_yticks(range(CURVA["p"]))
        ax.set_xlabel("x", fontsize=12)
        ax.set_ylabel("y", fontsize=12)
        ax.set_title(f"E(Z_{{{CURVA['p']}}}): {CURVA['nombre']}", fontsize=13)
        ax.grid(True, alpha=0.2, linestyle="--")
        ax.legend(fontsize=10)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with st.expander("🔍 Cálculo detallado punto a punto"):
        _, log_pts = capturar(listar_puntos, CURVA["a"], CURVA["b"], CURVA["p"], verbose=True)
        st.code(log_pts, language=None)


# ═════════════════════════════════════════════════════════════
# PESTAÑA 2 — Generar claves
# ═════════════════════════════════════════════════════════════

with tab2:
    st.subheader("Generación de par de claves")
    st.markdown(
        "Elige la clave privada **d ∈ [1, n-1]** y se calcula **Q = d·G** "
        "con el algoritmo double-and-add. "
        "El gráfico muestra la cadena de adición paso a paso."
    )

    # ── Selección de d ───────────────────────────────────────
    modo = st.radio(
        "Modo de selección de d:",
        ["🎲 Aleatoria", "🎚️ Slider (1 … n-1)", "🔢 Número libre"],
        horizontal=True,
        key="modo_keygen",
    )

    def _reset_firma():
        """Invalida la firma almacenada cuando cambia la clave."""
        st.session_state.firma           = None
        st.session_state.mensaje_firmado = None
        st.session_state.firma_log       = None
        st.session_state.k_nonce         = None
        st.session_state.ver_orig        = None
        st.session_state.ver_orig_pts    = None
        st.session_state.ver_alt         = None
        st.session_state.ver_alt_pts     = None

    def _set_d(d_new, d_original=None, log_new=None):
        """Actualiza d, Q y d_original en session_state e invalida la firma."""
        Q_new = MULT[d_new]
        changed = (st.session_state.d != d_new or
                   st.session_state.d_original != d_original)
        if changed:
            st.session_state.d          = d_new
            st.session_state.Q          = Q_new
            st.session_state.d_original = d_original
            st.session_state.keygen_log = log_new
            _reset_firma()
        elif log_new is not None:
            st.session_state.keygen_log = log_new

    n_curva = CURVA["n"]

    if modo == "🎲 Aleatoria":
        if st.button("🎲 Generar clave privada aleatoria", type="primary", key="btn_rand"):
            (d_new, Q_new), log_new = capturar(generar_claves, CURVA, True)
            st.session_state.d          = d_new
            st.session_state.Q          = Q_new
            st.session_state.d_original = None
            st.session_state.keygen_log = log_new
            _reset_firma()

    elif modo == "🎚️ Slider (1 … n-1)":
        d_init = st.session_state.d if (
            st.session_state.d and 1 <= st.session_state.d <= n_curva - 1
        ) else 1
        d_slider = st.slider(
            f"Elige d  (rango: 1 … {n_curva - 1}):",
            min_value=1, max_value=n_curva - 1, value=d_init, key="slider_d",
        )
        _set_d(d_slider, None)
        if st.button("📋 Ver log detallado de Q = d·G", key="btn_log_slider"):
            _, log_s = capturar(
                multiplicacion_escalar, d_slider, CURVA["G"], CURVA["a"], CURVA["p"], True
            )
            st.session_state.keygen_log = log_s

    else:  # 🔢 Número libre
        st.markdown(
            f"Puedes escribir **cualquier entero positivo**. "
            f"Como el grupo tiene orden **n = {n_curva}**, "
            f"solo importa **d mod {n_curva}** — igual que en ECDSA real con n de 77 dígitos."
        )
        d_libre = st.number_input(
            "Ingresa d (cualquier entero ≥ 1):",
            min_value=1, value=1, step=1, key="d_libre",
        )
        d_libre = int(d_libre)
        d_efec  = d_libre % n_curva

        if d_efec == 0:
            st.warning(
                f"**{d_libre}** es múltiplo exacto de n = {n_curva} → "
                f"d mod n = 0 (elemento neutro, inválido como clave). "
                f"Prueba con {d_libre + 1}."
            )
        else:
            # Mostrar la reducción modular de forma visual
            ca, cb, cc = st.columns(3)
            ca.metric("d ingresado",  d_libre)
            cb.metric(f"mod n  (n={n_curva})", f"mod {n_curva}")
            cc.metric("d efectivo",   d_efec,
                      help=f"{d_libre} mod {n_curva} = {d_efec}")
            st.caption(
                f"{d_libre} ≡ {d_efec} (mod {n_curva})  →  "
                f"Q = {d_efec}·G  (mismo punto), pero **todas las operaciones usan d = {d_libre}**."
            )
            _set_d(d_efec, d_libre)
            if st.button("📋 Ver log detallado de Q = d·G", key="btn_log_libre"):
                _, log_l = capturar(
                    multiplicacion_escalar, d_libre, CURVA["G"], CURVA["a"], CURVA["p"], True
                )
                st.session_state.keygen_log = log_l

    # ── Explicación del ECDLP ─────────────────────────────────
    with st.expander("💡 ¿Por qué en ECDSA real d puede ser enormemente grande?"):
        st.markdown(f"""
La seguridad de ECDSA no viene de que n sea secreto, sino de que n sea **astronómicamente grande**.

| Parámetro | Esta demo | secp256k1 (Bitcoin / Ethereum) |
|-----------|-----------|-------------------------------|
| Primo p   | 11        | ~2²⁵⁶ ≈ 1,16 × 10⁷⁷          |
| Orden n   | **{n_curva}**       | ~2²⁵⁶ (número de 77 dígitos)  |
| Claves posibles | {n_curva - 1} | ≈ 10⁷⁷                  |

**El problema:** dado Q = d·G (pública), encontrar d (privada) es el
**Problema del Logaritmo Discreto en Curvas Elípticas (ECDLP)**.

- En esta demo con n = {n_curva}, un atacante prueba los {n_curva - 1} valores posibles en microsegundos.
- Con n ≈ 2²⁵⁶, el número de intentos supera los átomos del universo observable (~10⁸⁰).
  El mejor algoritmo conocido (Pollard's rho) tardaría ~10³⁸ años.

**La reducción modular no es un problema:** si alguien elige d = 10⁵⁰ + 7,
el resultado es el mismo que d = (10⁵⁰ + 7) mod n, pero nadie puede descubrir
el original porque ni siquiera puede recorrer todos los residuos en tiempo razonable.
        """)


    # ── Resultados ───────────────────────────────────────────
    if st.session_state.d is not None:
        d_act = st.session_state.d
        Q_act = st.session_state.Q

        st.divider()
        col_info, col_plot = st.columns([1, 1.2], gap="large")

        with col_info:
            st.success("✓ Claves activas en todas las pestañas")
            d_orig = st.session_state.d_original
            c1, c2, c3 = st.columns(3)
            if d_orig is not None:
                c1.metric("🔒 d  (privada)", d_orig,
                          help=f"d ingresado = {d_orig} ≡ {d_act} (mod {n_curva})")
            else:
                c1.metric("🔒 d  (privada)", d_act, help="Mantener en secreto")
            c2.metric("Q.x (pública)", Q_act[0])
            c3.metric("Q.y (pública)", Q_act[1])
            if d_orig is not None:
                st.caption(
                    f"d = {d_orig} ≡ {d_act} (mod {n_curva}) &nbsp;—&nbsp; "
                    f"Q = {Q_act} &nbsp;—&nbsp; todas las operaciones usan d = {d_orig}."
                )
            else:
                st.caption(
                    f"Q = {Q_act} &nbsp;—&nbsp; puede publicarse.  \n"
                    f"d = {d_act} &nbsp;—&nbsp; **nunca compartir**."
                )
            if st.session_state.keygen_log:
                with st.expander("📋 Log completo: Q = d·G paso a paso"):
                    st.code(st.session_state.keygen_log, language=None)

        with col_plot:
            fig = grafico_claves(d_act, Q_act, AFINES)
            st.pyplot(fig)
            plt.close(fig)

    else:
        st.info("Selecciona una clave privada para comenzar.")


# ═════════════════════════════════════════════════════════════
# PESTAÑA 3 — Firmar y verificar
# ═════════════════════════════════════════════════════════════

with tab3:
    st.subheader("Firma y Verificación de mensajes")

    if st.session_state.d is None:
        st.warning("⚠️ Primero genera un par de claves en la pestaña **Generar claves**.")
        st.stop()

    d_t3          = st.session_state.d
    Q_t3          = st.session_state.Q
    d_original_t3 = st.session_state.d_original
    d_para_firmar = d_original_t3 if d_original_t3 is not None else d_t3
    if d_original_t3 is not None:
        st.caption(
            f"Claves activas:  d = {d_original_t3} ≡ {d_t3} (mod {CURVA['n']}),  Q = {Q_t3}"
        )
    else:
        st.caption(f"Claves activas:  d = {d_t3},  Q = {Q_t3}")
    st.divider()

    # ── FIRMA ─────────────────────────────────────────────────
    st.markdown("### ✍️ Paso 1 — Firmar")

    col_sig, col_sig_plot = st.columns([1, 1.1], gap="large")

    with col_sig:
        msg_input = st.text_input("Mensaje a firmar:", "Hola Mundo ECDSA", key="txt_msg")

        if st.button("✍️ Firmar", type="primary", key="btn_firmar"):
            k_gen = random.randint(1, CURVA["n"] - 1)
            (r_f, s_f), log_f = capturar(firmar, msg_input, d_para_firmar, CURVA, k_gen, True)
            st.session_state.k_nonce         = k_gen
            st.session_state.firma           = (r_f, s_f)
            st.session_state.mensaje_firmado = msg_input
            st.session_state.firma_log       = log_f
            st.session_state.ver_orig        = None
            st.session_state.ver_orig_pts    = None
            st.session_state.ver_alt         = None
            st.session_state.ver_alt_pts     = None

        if st.session_state.firma is not None:
            r_act, s_act = st.session_state.firma
            k_act = st.session_state.k_nonce
            R_act = MULT.get(k_act)

            cm1, cm2 = st.columns(2)
            cm1.metric("r", r_act)
            cm2.metric("s", s_act)
            st.caption(
                f"k (nonce, secreto) = {k_act} &nbsp;·&nbsp; "
                f"R = k·G = {R_act}"
            )
            if st.session_state.firma_log:
                with st.expander("📋 Log completo de la firma"):
                    st.code(st.session_state.firma_log, language=None)

    with col_sig_plot:
        if st.session_state.firma is not None:
            k_v = st.session_state.k_nonce
            R_v = MULT.get(k_v)
            r_v = st.session_state.firma[0]
            fig = grafico_firma(CURVA["G"], Q_t3, R_v, r_v, AFINES)
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("El gráfico de firma aparecerá aquí después de firmar.")

    # ── VERIFICACIÓN ──────────────────────────────────────────
    if st.session_state.firma is not None:
        st.divider()
        st.markdown("### 🔍 Paso 2 — Verificar")

        col_orig, col_alt = st.columns(2, gap="large")

        # Mensaje original
        with col_orig:
            st.markdown("#### Mensaje original")
            st.code(st.session_state.mensaje_firmado)

            if st.button("✅ Verificar original", key="btn_ver_orig"):
                valida_o, log_o = capturar(
                    verificar,
                    st.session_state.mensaje_firmado,
                    st.session_state.firma, Q_t3, CURVA, True,
                )
                pts_o = _ver_puntos(
                    st.session_state.mensaje_firmado,
                    st.session_state.firma, Q_t3,
                )
                st.session_state.ver_orig     = (valida_o, log_o)
                st.session_state.ver_orig_pts = pts_o

            if st.session_state.ver_orig is not None:
                valida_o, log_o = st.session_state.ver_orig
                if valida_o:
                    st.success("✅ FIRMA VÁLIDA")
                else:
                    st.error("❌ FIRMA INVÁLIDA")

                # Gráfico de verificación (original)
                if st.session_state.ver_orig_pts:
                    u1G_o, u2Q_o, X_o = st.session_state.ver_orig_pts
                    r_o = st.session_state.firma[0]
                    fig = grafico_verificacion(
                        CURVA["G"], Q_t3, u1G_o, u2Q_o, X_o, r_o, AFINES
                    )
                    st.pyplot(fig)
                    plt.close(fig)

                with st.expander("📋 Log de verificación"):
                    st.code(log_o, language=None)

        # Mensaje alterado
        with col_alt:
            st.markdown("#### Mensaje alterado")
            msg_alt = st.text_input(
                "Edita el mensaje:",
                value=st.session_state.mensaje_firmado + " [modificado]",
                key="txt_alt",
            )

            if st.button("🔍 Verificar alterado", key="btn_ver_alt"):
                valida_a, log_a = capturar(
                    verificar, msg_alt,
                    st.session_state.firma, Q_t3, CURVA, True,
                )
                pts_a = _ver_puntos(msg_alt, st.session_state.firma, Q_t3)
                st.session_state.ver_alt     = (valida_a, log_a)
                st.session_state.ver_alt_pts = pts_a

            if st.session_state.ver_alt is not None:
                valida_a, log_a = st.session_state.ver_alt
                if valida_a:
                    st.success("✅ FIRMA VÁLIDA")
                else:
                    st.error("❌ FIRMA INVÁLIDA — alteración detectada")

                # Gráfico de verificación (alterado)
                if st.session_state.ver_alt_pts:
                    u1G_a, u2Q_a, X_a = st.session_state.ver_alt_pts
                    r_a = st.session_state.firma[0]
                    fig = grafico_verificacion(
                        CURVA["G"], Q_t3, u1G_a, u2Q_a, X_a, r_a, AFINES
                    )
                    st.pyplot(fig)
                    plt.close(fig)

                with st.expander("📋 Log de verificación"):
                    st.code(log_a, language=None)


# ═════════════════════════════════════════════════════════════
# PESTAÑA 4 — Ataque por nonce reutilizado
# ═════════════════════════════════════════════════════════════

with tab4:
    st.subheader("Ataque: Recuperación de clave privada por nonce reutilizado")
    st.markdown(
        "Si el mismo **k** se usa en dos firmas distintas, r₁ = r₂. "
        "Con solo los mensajes y firmas (datos públicos) el atacante recupera **d**:"
    )

    c_eq1, c_eq2 = st.columns(2)
    with c_eq1:
        st.latex(r"k = (h_1 - h_2)\cdot(s_1 - s_2)^{-1} \pmod{n}")
    with c_eq2:
        st.latex(r"d = (s_1 \cdot k - h_1)\cdot r^{-1} \pmod{n}")

    st.divider()

    if st.button("💥 Ejecutar ataque", type="primary", key="btn_ataque"):
        _, log_atq = capturar(demostrar_ataque, CURVA)
        lineas = log_atq.split("\n")

        idx_comp = next((i for i, l in enumerate(lineas) if "¡COMPROMETIDA!" in l), None)
        idx_exit = next((i for i, l in enumerate(lineas) if "ATAQUE EXITOSO" in l), None)

        if idx_comp is None:
            st.code(log_atq, language=None)
        else:
            with st.expander("📋 Log del ataque — Pasos 1, 2 y 3", expanded=True):
                st.code("\n".join(lineas[:idx_comp]), language=None)

            linea_k = lineas[idx_comp - 1].strip() if idx_comp > 0 else ""
            linea_d = lineas[idx_comp].strip()
            st.error(
                f"🚨 **Clave privada recuperada**\n\n`{linea_k}`\n\n`{linea_d}`"
            )

            if idx_exit is not None:
                log_final = "\n".join(lineas[idx_exit:]).strip()
                if log_final:
                    st.markdown("#### Resultado final")
                    st.code(log_final, language=None)
                    st.error(
                        "⚠️ **Lección:** Reutilizar k compromete d por completo. "
                        "En producción, k debe ser criptográficamente aleatorio y único en cada firma."
                    )
