# Demo Didáctica: Firma Digital ECDSA

Demo educativa de ECDSA (Elliptic Curve Digital Signature Algorithm) implementada desde cero en Python, sin librerías criptográficas externas. Desarrollada para el curso de **Matemáticas Discretas**.

## Características

- Aritmética de curvas elípticas sobre Z_p (suma de puntos, multiplicación escalar double-and-add)
- Generación de claves, firma y verificación ECDSA paso a paso con fórmulas explícitas
- Ataque por reutilización de nonce: recuperación de la clave privada desde dos firmas con el mismo k
- Interfaz web interactiva con Streamlit: gráficos cartesianos, logs detallados, modo número libre
- Curva: y² ≡ x³ + 4x + 7 (mod 11) — |E| = 13 (primo), G = (1,1), n = 13

## Archivos

| Archivo | Contenido |
|---------|-----------|
| `grupos.py` | Euclides extendido, inverso modular, suma de puntos, multiplicación escalar, orden de punto |
| `ecdsa.py` | Parámetros de la curva, hash educativo, generación de claves, firma, verificación |
| `ataque.py` | Ataque por reutilización de nonce |
| `demo.py` | Interfaz de consola interactiva (menú 0-6) |
| `app.py` | Aplicación web Streamlit con 4 pestañas y visualizaciones |

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit matplotlib pandas
```

## Uso

**Interfaz web:**
```bash
streamlit run app.py
```

**Consola:**
```bash
python3 demo.py
```

## Curva elegida

Se usa y² ≡ x³ + 4x + 7 **(mod 11)** en lugar de mod 23 porque con p = 23 el orden del grupo |E| = 24 no es primo, lo que impide calcular inversos modulares para todos los nonces posibles y rompe ECDSA. Con p = 11, |E| = 13 (primo) y el algoritmo funciona correctamente para todos los valores.
