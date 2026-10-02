# helpers.py
# ----------
# Módulo fachada para re-exportar constantes y lógica de validación de IA
# de forma retrocompatible.

from .defaults import (
    DEFAULT_AI_CONFIG,
    _VALID_COMPONENTS,
    _VALID_DATASETS,
    _DEFAULT_MAPPINGS,
    _DEFAULT_MAPPINGS_BY_DATASET,
    _DEFAULT_DATASETS,
)
from .validator import (
    _extract_summary_and_json,
    _validate_and_fix_config,
)
from .prompts import _DASHBOARD_DESCRIPTIONS


def build_dashboard_visual_description(dashboard_type: str, component_type: str = None, dashboard_data: str = "") -> str:
    """
    Construye una especificación visual exacta del dashboard basándose en la forma
    geométrica 3D del componente (pie, doughnut, bars, boats, cyls, barsmap, network)
    y en el dataset asociado (issues_health, pull_requests, file_metrics, etc.).
    """
    comp = (component_type or "").lower().strip()
    dash = (dashboard_type or "").lower().strip()
    
    is_pie = any(k in comp or k in dash for k in ["pie", "doughnut", "tarta", "donut", "quesito"])
    
    if is_pie:
        if "issue" in dash:
            return """Gráfico Circular de Tarta/Donut 3D ("issues_health" / "babia-pie"):
   - FORMA GEOMÉTRICA MANDATORIA: Gráfico de Tarta / Quesito 3D dividido en sectores circulares / porciones de tarta. NO TIENE EJES NI BARRAS.
   - Cada sector circular / porción de tarta representa una categoría de estado/etiqueta de incidencias (bug, feature, documentation, question, general, etc.).
   - Tamaño / Ángulo del sector: Proporción relativa de incidencias pertenecientes a esa categoría respecto al total de incidencias.
   - Color: Identificador visual por categoría de etiqueta."""
        elif "language" in dash:
            return """Gráfico Circular de Tarta/Donut 3D ("data_by_language" / "babia-pie"):
   - FORMA GEOMÉTRICA MANDATORIA: Gráfico de Tarta 3D dividido en sectores circulares / porciones. NO TIENE EJES NI BARRAS.
   - Cada sector circular representa un lenguaje de programación presente en el repositorio.
   - Tamaño del sector: Proporción porcentual de uso/archivos de dicho lenguaje respecto al total.
   - Color: Asignado por paleta temática por lenguaje."""
        else:
            return f"""Gráfico Circular de Tarta/Donut 3D ("{dash}" / "babia-pie"):
   - FORMA GEOMÉTRICA MANDATORIA: Gráfico circular de tarta 3D dividido en sectores circulares / porciones. NO TIENE EJES NI BARRAS.
   - Cada porción representa una categoría del conjunto de datos '{dash}'.
   - Tamaño del sector: Porcentaje y proporción relativa respecto al total.
   - Color: Asignado por categoría."""

    if "boat" in comp or "boat" in dash or dash in {"file_metrics", "boats"}:
        return """Ciudad de Código 3D ("file_metrics" / "babia-boats"):
   - FORMA GEOMÉTRICA MANDATORIA: Escena 3D estilo ciudad con edificios rectangulares sobre un plano.
   - Cada edificio representa un archivo de código del repositorio.
   - Altura del edificio: Líneas de código físicas (NLOC) o métrica de volumen activa.
   - Área/Base del edificio: Complejidad ciclomática (CCN) o tamaño relativo.
   - Color: Escala térmica HSL según la métrica activa."""

    if "network" in comp or "network" in dash or dash in {"file_network", "code_reviews"}:
        if "review" in dash or "reviewer" in str(dashboard_data):
            return """Red de Revisiones de Código 3D ("code_reviews" / "babia-network"):
   - FORMA GEOMÉTRICA MANDATORIA: Grafo 3D de esferas (nodos) y conexiones (enlaces). NO TIENE BARRAS NI EJES.
   - Nodos (Esferas): Colaboradores y revisores de código. Tamaño de la esfera: Volumen de revisiones de PRs. Color de la esfera: Identificador visual por desarrollador (NO indica antigüedad ni actividad).
   - Enlaces (Líneas): Revisiones cruzadas entre desarrolladores. Grosor de la línea: Cantidad de revisiones cruzadas."""
        else:
            return """Red de Colaboración de Desarrolladores 3D ("file_network" / "babia-network"):
   - FORMA GEOMÉTRICA MANDATORIA: Grafo 3D de esferas (nodos) y conexiones (enlaces). NO TIENE BARRAS NI EJES.
   - Nodos (Esferas): Desarrolladores del proyecto. Tamaño de la esfera: Cantidad total de contribuciones. Color de la esfera: Identificador visual por autor (NO representa actividad ni antigüedad).
   - Enlaces (Líneas): Archivos co-editados en común. Grosor de la línea: Cantidad de archivos co-editados."""

    if "cyl" in comp or "cyl" in dash or dash in {"age_distribution", "top_complex_files", "top_churn_files"}:
        if "age" in dash:
            return """Distribución por Antigüedad en Cilindros 3D ("age_distribution" / "babia-cyls"):
   - FORMA GEOMÉTRICA MANDATORIA: Cilindros 3D independientes en el espacio.
   - Cada cilindro representa una categoría de edad ("Active" <30d, "Maintained" 30-180d, "Legacy" >180d).
   - Altura del cilindro: Volumen total de líneas de código (NLOC). Radio del cilindro: Número de archivos en esa franja de edad."""
        elif "complex" in dash:
            return """Top 10 Archivos Más Complejos en Cilindros 3D ("top_complex_files" / "babia-cyls"):
   - FORMA GEOMÉTRICA MANDATORIA: Cilindros 3D representando los 10 archivos más complejos.
   - Altura del cilindro: Complejidad máxima de una sola función (Peak CCN). Radio del cilindro: Complejidad promedio (CCN)."""
        elif "churn" in dash:
            return """Top 10 Archivos con Mayor Churn ("top_churn_files" / "babia-cyls"):
   - FORMA GEOMÉTRICA MANDATORIA: Cilindros 3D representando los 10 archivos con más modificaciones.
   - Altura del cilindro: Frecuencia de modificación (commits). Radio del cilindro: Volumen de código (NLOC)."""
        else:
            return f"""Gráfico de Cilindros 3D ("{dash}" / "babia-cyls"):
   - FORMA GEOMÉTRICA MANDATORIA: Cilindros 3D en el espacio.
   - Altura del cilindro: Métrica principal. Radio del cilindro: Métrica secundaria."""

    if "barsmap" in comp or "barsmap" in dash or dash in {"author_activity", "file_ownership", "releases_health"}:
        if "ownership" in dash:
            return """Propiedad de Autores / Bus Factor ("file_ownership" / "babia-barsmap"):
   - FORMA GEOMÉTRICA MANDATORIA: Mapa 3D de barras rectangulares dispuestas en cuadrícula sobre dos ejes horizontales (X y Z).
   - Eje X: Autores (Desarrolladores). Eje Z: Archivos.
   - Altura de la barra: Porcentaje de propiedad del archivo (0-100%)."""
        elif "release" in dash:
            return """Salud de Lanzamientos ("releases_health" / "babia-barsmap"):
   - FORMA GEOMÉTRICA MANDATORIA: Mapa 3D de barras en cuadrícula.
   - Eje X: Versión / Tag de release. Eje Z: Índice de estabilidad.
   - Altura de la barra: Cantidad de incidencias/bugs reportados post-lanzamiento."""
        else:
            return """Actividad de Autores en Cuadrícula 3D ("author_activity" / "babia-barsmap"):
   - FORMA GEOMÉTRICA MANDATORIA: Mapa 3D de barras en cuadrícula.
   - Eje X: Autores. Eje Z: Línea temporal de actividad.
   - Altura de la barra: Frecuencia de commits o inserciones."""

    if "bar" in comp or "bar" in dash or dash in {"pull_requests", "community_activity", "evolution_data"}:
        if "pull" in dash:
            return """Pull Requests y Latencia ("pull_requests" / "babia-bars"):
   - FORMA GEOMÉTRICA MANDATORIA: Gráfico de barras 3D/2D comparativas.
   - Eje X: Título del Pull Request.
   - Altura de la barra: Tiempo de resolución y merge (latencia en horas)."""
        elif "community" in dash:
            return """Actividad de la Comunidad ("community_activity" / "babia-bars"):
   - FORMA GEOMÉTRICA MANDATORIA: Gráfico de barras 3D/2D comparativas.
   - Eje X: Colaborador de la comunidad.
   - Altura de la barra: Suma total de aportaciones (issues + PRs)."""
        else:
            return """Evolución Temporal del Repositorio ("evolution_data" / "babia-bars"):
   - FORMA GEOMÉTRICA MANDATORIA: Gráfico de barras 3D/2D a lo largo del tiempo.
   - Eje X: Mensaje del commit / Línea temporal.
   - Altura de la barra: Inserciones / Volumen de cambios."""

    return _DASHBOARD_DESCRIPTIONS.get(dash) or f"Visualización 3D para '{dash}' ({comp})."

