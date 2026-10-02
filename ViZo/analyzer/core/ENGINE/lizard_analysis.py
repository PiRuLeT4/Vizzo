# lizard_analysis.py
# ──────────────────
# Lógica dedicada a la ejecución estática de Lizard en ViZzo.

import logging
import os
import time
import threading
import lizard

from .helpers import (
    is_minified_or_obfuscated,
    is_generated_or_test_file,
    _LIZARD_EXCLUDE_PATTERNS,
    _LIZARD_INCLUDE_FOLDERS
)

logger = logging.getLogger(__name__)
_LIZARD_TIMEOUT = 60.0
_MAX_LIZARD_FILES = 800


def _run_lizard(target_dir: str) -> list:
    """Ejecuta Lizard sobre target_dir y devuelve la lista de resultados por archivo."""
    logger.info("Analizando métricas con Lizard...")
    
    # Exclusión de carpetas de dependencias y temporales ruidosas para optimizar el rendimiento en repos grandes
    exclude_patterns = _LIZARD_EXCLUDE_PATTERNS
    
    threads_count = min(os.cpu_count() or 2, 4)

    # Expandir directorios a archivos individuales para realizar filtros preventivos
    files_to_analyze = []
    has_resolved = os.path.exists(target_dir)

    if os.path.isfile(target_dir):
        files_to_analyze.append(target_dir)
    elif os.path.isdir(target_dir):
        for root, dirs, filenames in os.walk(target_dir):
            # Filtrar dirs IN-PLACE para evitar que os.walk descienda a carpetas de dependencias / build / tests
            dirs[:] = [
                d for d in dirs 
                if d.lower() not in {
                    "node_modules", "vendor", "3rdparty", "third_party", 
                    "bin", "build", "dist", "target", ".git", "venv", 
                    "env", ".venv", ".env", "htmlcov", "out", ".github", 
                    ".gitlab", "cmake", "coverage", "deps", ".idea", ".vscode",
                    "test", "tests", "spec", "specs", "testing", "e2e", "fixtures", "mock", "mocks"
                }
            ]
            for f in filenames:
                files_to_analyze.append(os.path.join(root, f))

    _SUPPORTED_EXTENSIONS = (
        ".js", ".ts", ".tsx", ".jsx", 
        ".py", ".go", ".java", 
        ".c", ".cpp", ".h", ".hpp", ".cc", ".cxx", ".hh",
        ".swift", ".kt", ".cs", ".rb", ".php", 
        ".rs", ".lua", ".scala"
    )

    # Extensiones que son soportadas pero se excluyen por ser definiciones de tipo / autogeneradas
    _SKIP_SUFFIXES = (".d.ts", ".d.mts", ".d.cts")

    # Filtrar archivos: omitimos no soportados, grandes (>45KB), minificados u autogenerados
    filtered_files = []
    skipped_large_files = []
    skipped_minified_files = []
    skipped_generated_files = []

    if not has_resolved:
        # Si las rutas no existen en disco (caso de pruebas unitarias), pasamos las rutas originales directamente
        filtered_files = [target_dir]
    else:
        for f in files_to_analyze:
            # 0. Ignorar definiciones de tipo TypeScript (.d.ts) que son autogeneradas
            if f.lower().endswith(_SKIP_SUFFIXES):
                skipped_generated_files.append(f)
                continue

            # 1. Ignorar archivos que no sean de código fuente de lenguajes soportados
            if not f.lower().endswith(_SUPPORTED_EXTENSIONS):
                continue

            # 2. Ignorar archivos de código fuente muy grandes (>45KB)
            try:
                size_kb = os.path.getsize(f) / 1024.0
                if size_kb > 45.0:
                    skipped_large_files.append((f, size_kb))
                    continue
            except Exception:
                pass
                
            # 3. Exclusión de archivos minificados/ofuscados
            if is_minified_or_obfuscated(f):
                skipped_minified_files.append(f)
                continue

            # 4. Exclusión de archivos autogenerados o de test
            if is_generated_or_test_file(f):
                skipped_generated_files.append(f)
                continue

            filtered_files.append(f)

    if skipped_large_files:
        logger.warning(f"  - Omitidos {len(skipped_large_files)} archivos grandes (>45KB)")
    if skipped_minified_files:
        logger.warning(f"  - Omitidos {len(skipped_minified_files)} archivos minificados/ofuscados")
    if skipped_generated_files:
        logger.warning(f"  - Omitidos {len(skipped_generated_files)} archivos autogenerados o de prueba")

    # Muestreo representativo si el volumen de archivos sigue siendo extremadamente grande
    if len(filtered_files) > _MAX_LIZARD_FILES:
        logger.info(f"  - Repositorio extenso detectado ({len(filtered_files)} archivos). Muestreando {_MAX_LIZARD_FILES} archivos representativos.")
        step = len(filtered_files) / float(_MAX_LIZARD_FILES)
        filtered_files = [filtered_files[int(i * step)] for i in range(_MAX_LIZARD_FILES)]

    # Ejecutar Lizard directamente en el hilo actual (sin multiprocessing.Process).
    # El análisis ya se ejecuta dentro de un ThreadPoolExecutor (orchestrator.py),
    # por lo que crear un subproceso adicional con spawn en Windows causaba deadlocks
    # por la combinación de ThreadPoolExecutor → multiprocessing.Process(spawn) → lizard threads.
    analysis = []
    logger.info(f"  - Ejecutando Lizard sobre {len(filtered_files)} archivos (threads={threads_count}, timeout={_LIZARD_TIMEOUT}s)...")

    error_holder = [None]

    def _lizard_worker():
        """Ejecuta lizard.analyze() en un hilo daemon para poder aplicar timeout."""
        try:
            results = list(
                lizard.analyze(
                    filtered_files,
                    exclude_pattern=exclude_patterns,
                    threads=threads_count
                )
            )
            analysis.extend(results)
        except Exception as e:
            error_holder[0] = e

    worker_thread = threading.Thread(target=_lizard_worker, daemon=True)
    start_time = time.time()
    worker_thread.start()
    worker_thread.join(timeout=_LIZARD_TIMEOUT)

    elapsed = time.time() - start_time
    if worker_thread.is_alive():
        logger.warning(
            f"  - Lizard alcanzó el límite de tiempo de {_LIZARD_TIMEOUT}s ({elapsed:.1f}s transcurridos). "
            f"Conservando {len(analysis)} archivos analizados de forma parcial."
        )
        # El hilo daemon morirá automáticamente cuando el proceso principal termine o
        # cuando el ThreadPoolExecutor recicle el worker. No se puede matar un thread
        # de Python de forma forzada, pero al ser daemon no bloquea la terminación.
    elif error_holder[0]:
        logger.error(f"  - Error en Lizard: {error_holder[0]}")
    else:
        logger.info(f"  - Lizard finalizó correctamente en {elapsed:.1f}s.")

    logger.info(f"Análisis Lizard completado: {len(analysis)} archivos analizados exitosamente.")
    for file in analysis:
        logger.debug(
            f"  {os.path.basename(file.filename)} | CCN: {file.average_cyclomatic_complexity:.2f} | NLOC: {file.nloc}"
        )
    return analysis

