# Demo Didáctica: Firma Digital ECDSA

Demo educativa de ECDSA (Elliptic Curve Digital Signature Algorithm) implementada desde cero en Python, sin librerías criptográficas externas. Desarrollada para el curso de **Matemáticas Discretas**.

## 🌐 Aplicación desplegada

Accede a la demo directamente en el navegador, sin instalar nada:

**https://jaacmameciji23-firma-digital-ecdsa-app-itfeze.streamlit.app**

---

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

---

## Instalación local

### macOS

```bash
# 1. Clona el repositorio
git clone https://github.com/jaacmameciji23/firma-digital-ecdsa.git
cd firma-digital-ecdsa

# 2. Crea y activa el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Ejecuta la aplicación web
streamlit run app.py
```

### Windows

```powershell
# 1. Clona el repositorio
git clone https://github.com/jaacmameciji23/firma-digital-ecdsa.git
cd firma-digital-ecdsa

# 2. Crea y activa el entorno virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Ejecuta la aplicación web
streamlit run app.py
```

La app se abrirá automáticamente en el navegador   
Si prefieres la interfaz de consola, ejecuta `python3 demo.py` (macOS) o `python demo.py` (Windows).

---


## Integrantes

- Juan Andres Alvarez Cifuentes
- Nicolas Caucali Junco
- Gabriel Santiago Velez Gonzales
- Gracias por visitar nuestro proyecto :)
