# Registro de uso de IA

Reglas:
- Una entrada por PR, escrita el mismo día, no al final.
- Los criterios se escriben antes de pedir el código.
- Los prompts se copian literalmente (o recortados con […]), sin claves ni datos reales.
- "Qué corregí" recoge solo cambios reales hechos por mí, con su motivo.
- Cada entrada dice qué no verifiqué.
- El uso de IA se explica en este registro. Los documentos de planificación no se suben al repositorio. Solo los commits de las tareas verdes llevan la firma de la IA (`Co-Authored-By`).
- Los commits los hago yo a mano, salvo las tareas automáticas de bajo riesgo, que la IA confirma tras `make check`.

Modos:
- A · supervisión cercana: yo defino los criterios, la IA escribe por partes pequeñas y reviso cada parte.
- B · delegado y verificable: la IA escribe la tarea completa y lo compruebo con tests y `make check`.
- C · IA como revisora: la IA revisa un diff sin cambiar código y yo decido qué hallazgos son reales.

Niveles de riesgo (cada tarea tiene uno, según lo grave que sería un error que pasara desapercibido):
- 🔴 Rojo, alto: podría filtrar secretos o datos personales, saltarse la autenticación o corromper la base de datos. La IA escribe por partes pequeñas y se para tras cada una. El commit lo hago yo.
- 🟡 Amarillo, medio: un error sutil, pero que los tests detectan. La IA hace la tarea entera y se para una vez para que la revise. El commit lo hago yo.
- 🟢 Verde, bajo: solo rompería herramientas, documentación o el CI, y se nota enseguida. La IA hace la tarea, pasa `make check` y hace el commit con su firma.

(No hay que confundirlos con los "tests amarillos", que son los tests de rendimiento: miden, pero nunca bloquean.)

## Plantilla de entrada

```markdown
## Entrada N · <rama> · PR #N · AAAA-MM-DD
Modo: A, supervisión cercana (partes: …) · B, delegado (partes: …) · C, revisión.
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`).
Objetivo del PR: …

Criterios que definí antes de pedir el código:
- …

Prompts relevantes:
1. "…"

Qué generó la IA: archivos y número de tests.

Qué corregí a mano y por qué:
- `archivo`: qué estaba mal → qué cambié → por qué.

Cómo lo verifiqué:
- `make check` en verde.
- Pruebas manuales (curl, sqlite3, …).
- Bug a ciegas: la IA metió un error en `<archivo>::<función>` sin decirme dónde.
  Lo encontré leyendo: sí/no. Lo atrapó `<test>`. No se commiteó.
- Revisión de la IA (modo C): N hallazgos, acepté X, descarté Y porque …

Límites: qué no verifiqué.
```

---

## Entrada 1 · ci/pipeline-and-skeleton · PR #1 · 2026-11-21
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

Límites: el CI solo prueba Python 3.13 en Linux; el test de humo solo comprueba que el paquete `app` se importa.
