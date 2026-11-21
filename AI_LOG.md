## Entrada 1 · ci/pipeline-and-skeleton · PR #[N] · 2026-11-21
Modo: B, delegado (partes: esqueleto, herramientas y CI).
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor.
Objetivo del PR: dejar el repositorio listo para trabajar: esqueleto de `app/` y `tests/`, `pytest.ini` con el marcador `performance`, `ruff.toml`, `Makefile` con `check` y `perf`, `.env.example`, y CI en GitHub Actions con los jobs `lint-and-test` y `performance`.

Criterios que definí antes de pedir el código:
- El CI corre ruff, la revisión de formato y pytest en cada PR y en cada push a main.
- Ningún secreto en el repositorio. `.env` y `.venv` ignorados por Git.
- Un solo test trivial, para que pytest no falle sin tests.
- Los tests `performance` quedan fuera de la corrida normal y tienen su propio job.

Prompts relevantes (traducidos del inglés):
1. "Crea los archivos iniciales del proyecto, pidiéndome confirmación para cualquier cosa."
2. "Empieza la Tarea 1.1, paso 1."

Qué generó la IA: 8 archivos (`app/__init__.py`, `tests/__init__.py`, `tests/unit/test_smoke.py`, `pytest.ini`, `ruff.toml`, `Makefile`, `.env.example` y `.github/workflows/ci.yml`) y 1 test (`test_app_package_imports`). Commit `da1eb71`, hecho por la IA tras `make check`, por ser una tarea automática de bajo riesgo.

Cómo lo verifiqué:
- Antes de empezar, la IA comprobó mi preparación sin tocarla: rama correcta, `.env` ignorado por git y versiones instaladas iguales a las fijadas.
- `make check` en verde: `ruff check` sin errores, `ruff format --check` con 5 archivos ya formateados, y `1 passed`.
- `pytest -m performance` termina con código 5 ("no tests ran"), así que el `-m` de la línea de comandos anula el de `addopts`.
- CI en el PR: los dos jobs, `lint-and-test` y `performance`, quedaron en verde.
El job `performance` pasa porque aún no hay tests de rendimiento: pytest devuelve el código 5 y el CI lo acepta como éxito.
- Revisión de la IA (modo C): no hecha en este PR. Es un cambio de bajo riesgo (esqueleto y
  configuración, sin datos ni claves reales), y revisé yo los archivos generados y el
  resultado del CI.

Qué corregí a mano y por qué:
- No corregí código. Revisé uno a uno los 8 archivos generados, que son sobre todo el esqueleto de la aplicación.

Review en el PR: [N] comentarios de línea sobre … ([enlace]).
Límites: el CI solo prueba Python 3.13 en Linux; el test de humo solo comprueba que el paquete `app` se importa.
