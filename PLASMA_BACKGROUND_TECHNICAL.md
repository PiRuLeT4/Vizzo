# Documentación Técnica: Integración del Fondo Animado Plasma (WebGL + React 18) en ViZzo

Este documento proporciona una especificación técnica completa sobre la arquitectura, implementación, sistema de capas CSS, canal de renderizado WebGL 2 y solución a problemas de caché e importación ESM en relación al fondo animado **Plasma** en la plataforma **ViZzo**.

---

## 1. Arquitectura de Integración

La integración combina una arquitectura **Django Monolítica SSR** (Server-Side Rendering) con componentes modernos de **React 18** y aceleración por GPU **WebGL 2** sin requerir un pipeline de compilación de Node.js (Vite, Webpack, Babel).

```
                      +------------------------------------------+
                      |         Django SSR (templates/base.html) |
                      +------------------------------------------+
                                           |
                                           v
                       <div id="plasma-bg" class="plasma-bg-container">
                                           |
                                           v
                    +----------------------------------------------+
                    | static/js/PlasmaReact.js (ES Module Script) |
                    +----------------------------------------------+
                               /           |           \
                              /            |            \
                             v             v             v
                    esm.sh/react@18   esm.sh/react-dom  esm.sh/ogl@1.0.8
                                           |
                                           v
                                ReactDOM.createRoot()
                                           |
                                           v
                             <Plasma /> Component (useRef + useEffect)
                                           |
                                           v
                             GPU Canvas WebGL 2 (Raymarching GLSL)
```

---

## 2. Especificación de Componentes y Archivos

### 2.1 `static/js/PlasmaReact.js`
Es el módulo JavaScript principal (ESM) que encapsula tanto el componente React como la lógica matemática del shader y el código de automontaje DOM.

* **Importación de Módulos ES**:
  ```javascript
  import React, { useEffect, useRef } from "https://esm.sh/react@18";
  import { createRoot } from "https://esm.sh/react-dom@18/client?deps=react@18";
  import { Renderer, Program, Mesh, Triangle } from "https://esm.sh/ogl@1.0.8";
  ```
  - `deps=react@18`: Garantiza que `react-dom` comparta la misma instancia de memoria de React 18 que la importada en la línea 1.

* **Pipeline de Renderizado WebGL (Shaders GLSL 3.00 es)**:
  - **Vertex Shader**: Instancia una geometría de triángulo clip-space (`Triangle(gl)`) que cubre las coordenadas de pantalla de `[-1, -1]` a `[3, 3]`.
  - **Fragment Shader (`buildFragment`)**:
    - **Raymarching Loop**: Ejecuta hasta 60 iteraciones sobre el espacio 3D generando ondas armónicas mediante combinaciones sinusoidales `sin(S.y + p.z * 0.5 + S.z - length(S - p))`.
    - **Sanitización Numérica (`sanitize` & `finite1`)**: Previene la propagación de valores `NaN` o `Inf` en hardware con drivers DirectX/ANGLE.
    - **Colorimetría**: Convierte el color hexadecimal (por defecto `#59041A` / `#8B0A2E`) a RGB normalizado `[0.0 - 1.0]` y aplica un escalado de intensidad cromática `intensity * uCustomColor * 2.5` para resaltar sobre el tema oscuro de ViZzo.

* **Ciclo de Vida del Componente React (`Plasma`)**:
  - `containerRef`: Captura el elemento contenedor del DOM.
  - `useEffect`:
    1. Instancia el contexto `WebGL2RenderingContext` mediante `OGL.Renderer`.
    2. Registra eventos de movimiento de ratón en `window` si `mouseInteractive` está habilitado.
    3. Inicializa un `ResizeObserver` para recalcular el drawing buffer (`gl.drawingBufferWidth` / `gl.drawingBufferHeight`) según la proporción `renderScale` (optimización a resolución 75%-80% reescalada por GPU).
    4. Inicializa un `IntersectionObserver` y un listener de `visibilitychange` para suspender el bucle `requestAnimationFrame` cuando la ventana o el elemento no están visibles, reduciendo el consumo de GPU/CPU a 0%.
    5. Renderiza un frame estático sin loop si el usuario tiene configurada la preferencia `prefers-reduced-motion`.
    6. En la función de desmontaje (cleanup), cancela el `raf`, remueve los event listeners e invalida el contexto WebGL.

* **Automontaje DOM (`mountPlasmaReact`)**:
  ```javascript
  function mountPlasmaReact() {
    const rootEl = document.getElementById("plasma-bg");
    if (rootEl) {
      try {
        const root = createRoot(rootEl);
        root.render(
          React.createElement(Plasma, {
            color: "#8B0A2E",
            speed: 0.8,
            direction: "forward",
            scale: 1.2,
            opacity: 1,
            mouseInteractive: true,
            renderScale: 0.8,
            maxDpr: 2,
            targetFps: 60,
            iterations: 60,
          })
        );
      } catch (err) {
        console.error("Error al montar PlasmaReact:", err);
      }
    }
  }
  ```

---

### 2.2 Capa de Estilos y Posicionamiento (`static/css/plasma.css`)

```css
.plasma-bg-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
  opacity: 1;
  background: transparent;
}

.plasma-bg-container canvas {
  display: block;
  width: 100% !important;
  height: 100% !important;
  pointer-events: none;
}
```

* `position: fixed`: Fija el canvas a la ventana del navegador.
* `z-index: 0`: Coloca el lienzo sobre el elemento `html` pero por debajo del contenido principal.
* `pointer-events: none`: Permite que todos los eventos de interacción (clics, selecciones, desplazamientos) atraviesen el canvas transparente y lleguen a los botones y elementos de la UI.

---

### 2.3 Jerarquía de Stacking Context en CSS (`static/css/global.css`)

Para evitar que el lienzo WebGL sea tapado por fondos sólidos:

1. **Fondo Raíz (`html`)**:
   ```css
   html {
     scroll-behavior: smooth;
     background-color: var(--bg-primary, #0A0A0F);
   }
   ```
2. **Cuerpo Transparente (`body`)**:
   ```css
   body {
     font-family: var(--font-sans);
     background-color: transparent; /* Permite ver la capa z-index: 0 */
     color: var(--text-primary);
     min-height: 100vh;
   }
   ```
3. **Contenido Principal (`.main-content`)**:
   ```css
   .main-content {
     position: relative;
     z-index: 1; /* Posiciona la interfaz por encima de z-index: 0 */
     padding-top: var(--navbar-height);
     min-height: 100vh;
   }
   ```

---

### 2.4 Configuración del Servidor de Archivos Estáticos (`ViZo/settings.py`)

Se añadió la directiva:
```python
WHITENOISE_USE_FINDERS = True
```
**Razonamiento Técnico**: Por defecto, `WhiteNoiseMiddleware` en Django lee los archivos desde la carpeta compilada `STATIC_ROOT` (`staticfiles/`). Al habilitar `WHITENOISE_USE_FINDERS = True`, en modo desarrollo local Django y WhiteNoise buscan directamente en la carpeta de trabajo `STATICFILES_DIRS` (`static/`), permitiendo reflejar cambios inmediatos en el código sin requerir la ejecución de `python manage.py collectstatic`.

---

### 2.5 Integración en la Plantilla Base (`templates/base.html`)

Se añadieron los nodos de estructura y la importación de script tipo módulo:

```html
<!-- En <head> -->
<link rel="stylesheet" href="{% static 'css/plasma.css' %}?v=2" />

<!-- Al inicio de <body> -->
<div id="plasma-bg" class="plasma-bg-container"></div>

<!-- Antes de cerrar </body> -->
<script type="module" src="{% static 'js/PlasmaReact.js' %}?v=3"></script>
```

---

## 3. Resolución de Problemas Frecuentes (Troubleshooting Guide)

1. **Error `TypeError: Cannot read properties of undefined (reading 'createRoot')`**:
   - *Causa*: Importar `import ReactDOM from "https://esm.sh/react-dom@18/client"`. En los módulos ES de React 18, `createRoot` es una exportación nombrada, no una propiedad del objeto por defecto.
   - *Solución*: Utilizar `import { createRoot } from "https://esm.sh/react-dom@18/client?deps=react@18"`.

2. **El fondo no refleja cambios tras editar `PlasmaReact.js`**:
   - *Causa*: Caché persistente de ES Modules en navegadores Chromium/Firefox cuando la URL tiene un parámetro estático `?v=N`.
   - *Solución*: Incrementar el parámetro de versión `?v=N+1` en `base.html` o forzar la recarga ignorando la caché con `Ctrl + F5` / `Shift + F5`.

3. **Incompatibilidad de variables uninitialized en GLSL en Windows (ANGLE)**:
   - *Causa*: Leer variables `out vec4` antes de ser asignadas dentro de un bucle de raymarching.
   - *Solución*: Inicializar explícitamente todas las variables locales (`vec3 O = vec3(0.0)`, `o = vec4(0.0)`) al inicio de la función del shader.
