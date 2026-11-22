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

## Entrada 0 · planificación · sin PR · 2026-11-21

Esta entrada no es un PR. Casi todo lo de aquí lo hice yo: el criterio, las tablas de tests, el stack y lo que se queda fuera. La IA entró como segunda opinión, con la skill de brainstorming, y solo afinó. No hay código, no hay commit y los planes no entran al repositorio. La Entrada 2 dice que quité el borrador de esta entrada para escribirla yo al final: este texto es esa entrada.

Criterios:
- Las decisiones las cierro yo. La IA no elige por mí.
- Las tablas de tests las escribo yo: qué tiene que fallar y en qué borde. La IA agrupa y afina el nombre. No añade casos. Si cree que falta uno, lo dice aparte y yo decido.
- Los tests que bloquean y los que solo miden no se mezclan.
- Cada pieza del stack la elijo yo. La IA no rellena versiones.
- Lo que puede filtrar una clave, saltarse la autenticación, inyectar SQL, dejar pasar una respuesta manipulada o llamar al modelo real se hace despacio y conmigo.

Decisiones:
- El GET del candidato devuelve lo que lista el enunciado, `cv_text` incluido. El historial no va ahí.
- Un solo comando de arranque: `docker compose up --build`. Sin arranque por venv.
- Rúbrica 50/30/20, elegida después de ver opciones. Los tramos de años los fijé yo más tarde en 3–7 y 8 o más. Está en la Entrada 5.
- Cada dependencia va con `==`, fijada el 21 de noviembre de 2026:

| Pieza | Elegí | Descarté |
|---|---|---|
| Lenguaje | Python 3.13 | TypeScript / Node |
| API | FastAPI 0.165.0 | Node.js |
| Servidor | Uvicorn 0.54.0 | — |
| Validación | Pydantic 2.14.4 y email-validator 2.4.0 | validar a mano |
| Base de datos | `sqlite3` (3.45.3 en mi Mac) | SQLAlchemy, Alembic |
| Tests | pytest 9.0.3, pytest-cov 7.1.0, httpx 0.28.1 | — |
| Estilo | ruff 0.17.6 | — |
| Dependencias | pip, con `requirements.txt` y `requirements-dev.txt` | Poetry / uv |
| Auditoría de dependencias | pip-audit 2.10.1, desde la rama 9 | confiar en `pip install` |
| Modelo real | `google-genai` 3.6.1, opcional. El simulador es el defecto | llamarlo desde los tests |
| Empaquetado | Docker 28.0.1 y Compose v2.33.1. Imagen `python:3.13-slim` fijada por digest | arrancar con venv y uvicorn |
| CI | GitHub Actions, `actions/checkout` v7 y `actions/setup-python` v7 | — |

Mejoras con la IA:
- Ordenó mis casos por rama y les dejó un nombre estable. Los casos siguieron siendo los míos.
- En la rúbrica me puso las opciones juntas, con lo que cada una gana y lo que pierde. La elección fue mía.
- Señaló dónde un fallo sería grave y dónde solo molestaría. El semáforo lo armé yo a partir de eso.

Decisiones del brainstorming:

Tests unitarios que bloquean, escritos como mis casos:
- Configuración: sin clave, con `cambia-esto`, con menos de 32 caracteres, y con una clave válida.
- Autenticación: cada ruta sin clave y con clave incorrecta responde 401; una cabecera no ASCII no es un 500; sin clave y con JSON roto sigue siendo 401; las exenciones de `/docs` son exactamente las cuatro rutas.
- Prompt: el CV viaja solo dentro de su bloque, el nonce cambia en cada construcción, y un marcador de cierre falso no cierra el bloque.
- Salida del modelo: un `match_score` de 250 se rechaza, un JSON roto se rechaza, y también `85.5`, `"85"`, `true` y `NaN`. No se repara.
- Simulador: los bordes de la rúbrica, la palabra completa (`Java` no es `JavaScript`) y el CV malicioso puntúa igual que el limpio.
- Reintentos: solo se repite una salida inválida, como máximo 3 veces. Un timeout no se reintenta.
- Guardián: en los tests, llamar a Gemini o abrir la red falla alto.

Esos son los que protegen el enunciado. Los de rendimiento (Y1 a Y4) no entran aquí: miden y no bloquean.

Diseño del endpoint de auditoría:
- El plan base leía el historial en el GET y no quería un endpoint nuevo. Lo invertí yo. El GET se queda literal al enunciado, y mezclar ahí el historial lo habría sacado de esa lista.
- El historial es `GET /candidates/{id}/audit`, solo lectura, con la misma clave que el resto.
- Una fila por intento, también los fallidos. Nada se sustituye.
- Se ve la oferta, el proveedor, el modelo, la versión del prompt, los intentos, el estado, el resultado o el código de error, la duración y la `reference`.
- No se ve el CV ni el `error_detail`. La tabla no tiene columna para el CV, y el detalle del error no sale en la respuesta.
- Del más nuevo al más antiguo. `limit` de 1 a 100, por defecto 20. `offset` desde 0.

Límites:
- El semáforo (rojo, amarillo, verde) es el límite de cómo se trabaja, no un adorno. Rojo: un fallo podría filtrar una clave o un CV, saltarse la autenticación, inyectar SQL, colar una respuesta manipulada o llamar al modelo real. Se hace por partes, conmigo, y el commit es mío. Amarillo: los tests lo cazan, pero la decisión la defiendo yo. Verde: solo rompe herramientas, documentación o el CI. Esos commits los hace la IA, con su firma, tras `make check`. Once ramas salieron en 11 rojas, 5 amarillas y 8 verdes. El amarillo del semáforo no es el de los tests de rendimiento.
- Lo que no construí lo dejé escrito, para no presentarlo como hecho. Son los Issues #9 y #14 a #27: límite de peticiones, contraste de las skills con el CV, una clave por cliente, más auditoría, proteger `main`, no repetir un análisis idéntico, registro de los rechazos sin el cuerpo, UUID, apagar `/docs`, un segundo proveedor, el healthcheck de Compose, construir la imagen en el CI, una CSP, el listado de candidatos y tests con datos generados. El #9 ya estaba abierto. Los otros catorce se me olvidó abrirlos en cada rama: los creé al final, con el código ya fusionado.
- La cobertura se quedó informativa en esta pasada. Pasar al 80 % bloqueante solo si el número se mantenía es la Entrada 9.
- Los planes siguen fuera del repositorio. Esta entrada la escribo al cerrar, no el día de la planificación.
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

---

## Entrada 2 · chore/repo-conventions · PR #2 · 2026-11-21
Modo: B, delegado (partes: borradores de las reglas del agente, la plantilla de PR y la cabecera del registro), con mi revisión y edición antes del commit.
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor.
Objetivo del PR: fijar las convenciones del repositorio: reglas para el agente (`AGENTS.md`), plantilla de PR en español y la cabecera de este registro (reglas, modos, niveles de riesgo y plantilla de entrada).

Criterios que definí antes de pedir el código:
- Reglas cortas y comprobables para el agente: una línea por regla, sin reglas inventadas fuera de las acordadas.
- `AGENTS.md` en inglés; la plantilla de PR y este registro, en español.
- La plantilla de PR con las mismas secciones que usé en el PR #1, para que todos los PR se vean iguales.

Prompts relevantes (resumidos y traducidos del inglés):
1. "Explícame la rama 2: los pasos y cómo trabajamos según el nivel de riesgo."
2. "Redacta los borradores a partir del Apéndice A del plan."
3. "Explica brevemente al principio del registro los niveles verde, amarillo y rojo."

Qué generó la IA: borradores de `AGENTS.md` (8 reglas, en inglés), `.github/pull_request_template.md` (secciones Qué, Por qué, Cómo lo probé y Uso de IA) y la cabecera de `AI_LOG.md`. Sin código ni tests. El commit `81545d8` lo hice yo.

Cómo lo verifiqué:
- `make check` sigue en verde (`1 passed`); esta rama no toca código.
- Al abrir el PR, la descripción se rellenó sola con las secciones de la plantilla.
- Sin bug a ciegas ni revisión de la IA (modo C): son solo documentos.

Qué corregí a mano y por qué:
- `AGENTS.md` (regla 8) y las reglas del registro: permití la firma `Co-Authored-By` de la IA en los commits de las tareas verdes, porque esos commits los hace la IA y así queda claro en el propio historial.
- Quité el borrador de la Entrada 0 (planificación): prefiero escribirla yo al final del proyecto, con tiempo.
- Quité la línea "Review en el PR" de la plantilla de entrada: los comentarios ya están en GitHub y no quiero repetirlos aquí.

Límites: las reglas de `AGENTS.md` dependen de que el agente las siga; solo la de `.env` está reforzada con un bloqueo en la configuración local del agente.

---

## Entrada 3 · feat/api-base-and-auth · PR #3 · 2026-11-21
Modo: A, supervisión cercana (partes: tareas 3.1 y 3.2, por partes pequeñas con una pausa tras cada una) · B, delegado con un punto de control (parte: tarea 3.3).
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor. El resumen inicial de la rama lo hizo Sonnet 5.5.
Objetivo del PR: la base de la API: configuración que no arranca con una clave débil, formato único de errores, autenticación por `X-API-Key` en todas las rutas, `/health` y cabeceras de seguridad en todas las respuestas.

Criterios que definí antes de pedir el código:
- La app no arranca si `API_KEY` falta, es exactamente `cambia-esto`, o tiene menos de 32 caracteres. Una clave de 32 caracteres sí vale. El texto de `ConfigError` no contiene la clave.
- Los tests usan la `TEST_API_KEY` del plan (`"test-key-" + "k" * 34`). No leen `.env`.
- Cada código de error tiene una frase fija. Un 422 devuelve solo `loc`, `msg` y `type`, sin `input` ni `ctx`. Un 500 es genérico, lleva una `reference` de 16 caracteres, y el log guarda el tipo de excepción y esa referencia, nunca el mensaje.
- Toda ruta exige `X-API-Key`, salvo `/docs`, `/docs/oauth2-redirect`, `/redoc` y `/openapi.json`, comparadas por igualdad exacta. La clave se lee en bytes y se compara con `secrets.compare_digest`. Si no hay clave, el cuerpo no se lee: un JSON roto responde 401, no 422.
- `/health` exige la clave y responde `{"status": "ok"}`. Las cuatro cabeceras de seguridad van en todas las respuestas, también en el 401 y en el 500.

Prompts relevantes (traducidos del inglés):
1. "Usa la `TEST_API_KEY` del plan y proponme los mensajes de error para que yo los apruebe."
2. "Apruebo los 9 tests del plan. Añade dos: una clave de exactamente 32 caracteres se acepta, y el texto de una clave rechazada nunca aparece en el mensaje de `ConfigError`."
3. "No quites los espacios de la clave: D7 no lo pide y no hay test para eso."
4. "Añade un middleware ASGI que capture cualquier excepción, devuelva el mismo 500 genérico y no la vuelva a lanzar, para que la traza con el mensaje no llegue al log del servidor. Solo debe registrar el tipo de excepción y la referencia, nunca el mensaje ni la traza. Pruébalo con un cliente normal que espere un 500 y no una excepción."
5. "Deja `msg` en los detalles del 422, como pide D16, y apúntalo como límite."
6. "Apruebo los 13 tests de autenticación. Añade: `/docsx` sin clave da 401 y no 404 (para pillar un `startswith`), `compare_digest` recibe bytes en los dos lados, y la clave incorrecta tampoco sale en los logs."
7. "Mantén el cierre de las conexiones websocket sin clave (fail-closed)."
8. "El orden de los middlewares, de fuera hacia dentro, es: cabeceras, catch-all, autenticación. Las cabeceras siempre van por fuera para que también salgan en el 500."

Qué generó la IA:
- Código: `app/config.py`, `app/errors.py` (con `CatchAllErrorMiddleware`), `app/main.py`, `app/auth.py`, `app/middleware.py` y `app/routers/health.py`.
- Tests: `tests/conftest.py`, `tests/helpers.py` y 30 tests nuevos: 6 de configuración, 6 de errores, 14 de autenticación y 4 de `/health` y cabeceras.
- Commits `f02deca`, `89a7828` y `9baf7b7`, hechos por mí.

Cómo lo verifiqué:
- En cada tarea vi los tests en rojo antes de implementar y en verde después.
- `make check` en verde: 31 tests y 97 % de cobertura.
- El test del catch-all se pone en rojo si se quita el middleware, así que es lo único que protege contra esa fuga.
- Con scripts aparte comprobé que la autenticación responde 401 sin leer el cuerpo, que los websockets se cierran con el código 1008 y que las cabeceras de seguridad salen también en el 500 y en `/openapi.json`.
- Bug a ciegas: la IA metió un error en `app/auth.py::ApiKeyMiddleware.__call__` sin decirme dónde menos el archivo donde se puso.
  Lo encontré leyendo: sí. Era un `startswith` en la excepción de las rutas de documentación, que dejaba sin clave cualquier ruta que empezara por `/docs`.
  Lo atrapó `test_path_starting_like_docs_still_requires_key`, el test extra que pedí yo; ninguno de los tests que nombraba el plan lo detectaba. Lo deshice con `git restore` y no se commiteó.
- Revisión de la IA (modo C): no hecha. La revisión de esta rama fueron las pausas de cada parte y el bug a ciegas.

Qué corregí a mano y por qué:
- No reescribí los archivos a mano. Cuando el resultado no cumplía una regla, paré y cambié el encargo:
- `app/errors.py`: Starlette volvía a lanzar la excepción después del 500, y la traza llevaba el mensaje. Pedí un middleware que responde el mismo 500 y no relanza, en vez de apuntarlo solo como límite.
- `app/auth.py`: mantuve el cierre de websocket con código 1008. Dejar pasar la conexión habría sido una ruta sin clave.
- `app/main.py`: el orden, de fuera hacia dentro, quedó en cabeceras, catch-all y autenticación. El último `add_middleware` es el de fuera, así el 500 también lleva las cabeceras.
- No pedí recortar espacios en la clave ni quitar `msg` del 422. D7 y D16 no lo permiten.

Límites:
- El `msg` de un 422 puede citar el carácter inválido, pero nunca el valor completo enviado.
- Una clave hecha solo de espacios se acepta si llega a 32 caracteres. D7 no pide recortar.
- Si la excepción salta cuando la respuesta ya empezó, el catch-all no sustituye el cuerpo: el cliente ve la respuesta cortada y el log sigue teniendo solo el tipo y la referencia.
- `/docs`, `/docs/oauth2-redirect`, `/redoc` y `/openapi.json` no piden clave, a propósito.
- pytest no ejecuta el cierre de websocket, porque no hay rutas websocket. Lo comprobé con un script.
- Dejo el aviso de Starlette sobre `httpx` y `httpx2`. Las versiones están fijadas y los tests pasan.

---

## Entrada 4 · feat/candidates · PR #4 · 2026-11-21
Modo: A, supervisión cercana (partes: tareas 4.1 y 4.2, por partes pequeñas con una pausa tras cada una) · B, delegado con un punto de control (parte: tarea 4.3) · B, automático (parte: tarea 4.4, tests amarillos).
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor. El resumen inicial de la rama lo hizo Sonnet 5.5.
Objetivo del PR: guardar y leer candidatos: base de datos SQLite, `POST /candidates` y `GET /candidates/{id}` con todas las validaciones de entrada, límite de tamaño del cuerpo y los tests amarillos Y1 e Y2.

Criterios que definí antes de pedir el código:
- SQLite con `sqlite3`, consultas solo con `?`, y sin Docker. El contenedor llega en la rama 10. `DATABASE_PATH` es una ruta; por defecto `talentlite.db`.
- El email repetido lo rechaza `UNIQUE`, sin consulta previa. Solo `SQLITE_CONSTRAINT_UNIQUE` se convierte en duplicado. El 409 y `DuplicateEmailError` no llevan el email. El log lleva solo el id.
- El nombre se recorta antes de medir la longitud. El CV no se recorta: se guarda tal cual, y solo se rechaza si queda vacío al recortar una copia. Los tests no leen `.env` y usan datos inventados.
- El GET devuelve exactamente `id`, `name`, `email`, `cv_text`, `created_at` y `latest_analysis`. El id del path va de 1 a `2**63 - 1`, para que un id enorme sea 422 y no un 500 de SQLite.
- Cada petición abre su conexión y la cierra en `finally`. `PRAGMA foreign_keys = ON` va en cada conexión. `init_db` corre al arrancar y no borra filas.

Prompts relevantes (traducidos del inglés):
1. "Apruebo los 4 tests de la base de datos. Añade tres: una segunda conexión ve el candidato insertado (o sea, se hizo commit), un segundo `init_db` no borra la fila, y `PRAGMA foreign_keys` vale 1 en cada conexión nueva."
2. "Mantén estos añadidos: `check_same_thread=False`, solo `SQLITE_CONSTRAINT_UNIQUE` se convierte en email duplicado, y `get_candidate` nombra sus cinco columnas en vez de `SELECT *`."
3. "Apruebo los 32 tests de candidatos. Cambia el test del email de 255 caracteres por una pareja con partes de dominio válidas: 254 caracteres da 201 y 255 da 422. Añade que el GET devuelve exactamente los 6 campos del enunciado y que un CV con espacios alrededor se guarda tal cual."
4. "Deja `api_routes` leyendo el documento OpenAPI, no los objetos internos de FastAPI."
5. "El GET acepta solo ids de 1 a 2**63 − 1."
6. "Para los tests amarillos usa 50 POST y tamaños de 10, 1.000 y 10.000 candidatos."

Qué generó la IA:
- Código: `app/db.py`, `app/schemas.py`, `app/routers/candidates.py` y `BodySizeLimitMiddleware` en `app/middleware.py`, más cambios en `app/config.py` (`database_path`, `max_body_bytes`), `app/errors.py` (413) y `app/main.py` (arranque y orden de los middlewares).
- Tests: 47 nuevos (7 de base de datos, 35 de candidatos y 5 del límite de cuerpo) y 2 tests amarillos (Y1 e Y2) con su `report.py`. También `candidate_payload` en `tests/helpers.py`, y se quitó la ruta temporal `/_test/echo` de los tests de autenticación.
- Commits `5f1ad9e`, `9d51bf8` y `ea233ba`, hechos por mí. El commit `8876668` (tests amarillos) lo hizo la IA, con su firma, por ser una tarea verde.

Cómo lo verifiqué:
- En cada tarea vi los tests en rojo antes de implementar y en verde después.
- `make check` en verde: 78 tests y 98 % de cobertura.
- El test del commit se pone en rojo si se quita `conn.commit()`, así que es lo que protege contra perder escrituras.
- El test del email de 255 caracteres del plan fallaba por otro motivo (una parte del dominio demasiado larga), así que no probaba el límite de 254. Lo comprobé con la librería de emails y lo cambié por la pareja 254/255.
- La comprobación de "lista de rutas no vacía" destapó un problema real: FastAPI 0.165 envuelve los routers incluidos, así que los tests de "todas las rutas" no comprobaban `/health` desde la rama 3. Ahora leen las rutas del documento OpenAPI y cubren `/health`, `POST /candidates` y `GET /candidates/{id}`.
- Con scripts aparte comprobé que el arranque crea la base de datos, que la conexión se cierra después de cada petición y que el test de subida por trozos pasa de verdad por el contador de bytes (sin `Content-Length`).
- El cuerpo válido más grande (20.000 emojis) ocupa 240.056 bytes, por debajo del límite de 262.144.
- Tests amarillos: Y1, mediana de 1,38 ms y p95 de 2,38 ms. Y2, la búsqueda por email usa el índice `sqlite_autoindex_candidates_1` y tarda lo mismo con 10 que con 10.000 candidatos.
- Revisión de la IA (modo C): no hecha. La revisión de esta rama fueron las pausas de cada parte.

Qué corregí a mano y por qué:
- No reescribí los archivos a mano. Paré el trabajo y cambié el encargo cuando el resultado no cumplía una regla:
- El test de email de 255 caracteres del plan no medía el límite de 254: la librería lo rechazaba porque una parte del dominio pasaba de 63 caracteres. Lo cambié por una pareja con partes válidas: 254 da 201 y 255 da 422.
- `api_routes` lee el documento OpenAPI. Caminar los objetos internos de FastAPI 0.165 habría dependido de un detalle que ya cambió, y sin el cambio los bucles de autenticación no veían `/health`.
- El CV se guarda con los espacios. Recortarlo no evita una instrucción dentro del texto, y el enunciado pide conservar el CV.
- No metí Docker en esta rama. La base de datos es un archivo SQLite que el contenedor envolverá después.

Límites:
- Una instrucción dentro del CV se guarda igual que el resto del texto. La protección del prompt es la rama 5, con el nonce, no recortar el CV aquí.
- `api_routes` no lista una ruta oculta con `include_in_schema=False`. El middleware igual le exige la clave.
- El tope de 254 caracteres del email lo impone la librería, no un `max_length` mío. La pareja 254/255 lo fija.
- Un `IntegrityError` que no sea de unicidad se relanza. No hay test que lo provoque, porque una fila válida no puede generarlo.
- Los tests amarillos no afirman un umbral. Solo informan los tiempos, y Y2 muestra que la búsqueda usa `sqlite_autoindex_candidates_1`.
- `check_same_thread=False` vale porque cada conexión sirve una petición, un paso cada vez. No se comparte entre dos peticiones a la vez.

---

## Entrada 5 · feat/llm-layer · PR #5 · 2026-11-21
Modo: A, supervisión cercana (partes: tareas 5.2, 5.4 y 5.5, por partes pequeñas con una pausa tras cada una) · B, delegado con un punto de control (partes: tareas 5.1 y 5.3) · B, automático (parte: tarea 5.6, test amarillo).
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor. El resumen inicial de la rama lo hizo Sonnet 5.5.
Objetivo del PR: la capa de IA: interfaz del LLM con el mock por defecto, prompt con los datos separados de las instrucciones, validación estricta de la respuesta del modelo, mock con la rúbrica 50/30/20, reintentos limitados, proveedor Gemini opcional y el test amarillo Y3.

Criterios que definí antes de pedir el código:
- `LLM_PROVIDER` por defecto es `mock`, en minúsculas, y solo acepta `mock` o `gemini`. Gemini sin `GEMINI_API_KEY` o sin `GEMINI_MODEL` no arranca. El mensaje nombra la variable, nunca la clave. Las dos claves quedan fuera del `repr` de `Settings`.
- El timeout de Gemini es 60 segundos, salvo que `GEMINI_TIMEOUT_SECONDS` sea un número positivo y finito.
- El mensaje de sistema lleva las instrucciones, la rúbrica y el esquema. La oferta y el CV van en el mensaje de usuario, cada uno entre marcadores con un nonce de 32 caracteres hexadecimales. Lo de dentro es dato, no instrucciones.
- Rúbrica 50/30/20. Skills: mitad hacia arriba y solo la palabra completa. Años: 0 -> 0, 1–2 -> 10, 3–7 -> 20, 8 o más -> 30. Evidencia: el título completo da 20, al menos la mitad de sus palabras de 4 letras o más da 10, y si no, 0. Las skills salen en minúsculas, sin repetir y en el orden del CV.
- La salida no se repara. Un JSON inválido, un tipo mal o un campo de más se rechaza. El resumen del error lleva rutas y tipos, y el nombre de un campo inventado se enmascara. Como máximo 3 intentos, y solo se reintenta una salida inválida. Un timeout o un fallo del proveedor termina tras ese intento.
- Los tests no llaman a Gemini ni abren la red. El cliente del SDK se sustituye por uno falso. La llamada real la hago yo, con un CV inventado, y no anoto la clave ni la respuesta en bruto.

Prompts relevantes (traducidos del inglés):
1. "No te saltes la tarea de Gemini: ya tengo la clave en `.env`."
2. "El timeout de Gemini por defecto es de 60 segundos, y las dos claves se quedan fuera del `repr` de `Settings`."
3. "En los tests del prompt añade: un título o una skill con un marcador de cierre falso no cierra el bloque de la oferta, el nonce tiene 32 caracteres hexadecimales, el mensaje de sistema nombra los cuatro marcadores y dice que lo de dentro es dato, y el título de la oferta nunca aparece en el mensaje de sistema."
4. "La regla de evidencia: el título completo da 20; la mitad de sus palabras de 4 letras o más da 10; si no, 0. Las skills se devuelven en minúsculas, sin repetir y en el orden del CV."
5. "En la validación de la salida añade: años de 80 se aceptan y 81 o `True` se rechazan, un doble bloque ```json se rechaza, y el nombre de un campo inventado no aparece en el resumen del error."
6. "Cambia los tramos de años: de 3 a 7 años son 20 puntos y 8 o más son 30."
7. "En los reintentos añade: el prompt se construye una sola vez, la duración cuenta todos los intentos y los textos exactos de `error_detail`."
8. "Los tests del adaptador de Gemini se saltan el guardián con una marca propia (`real_llm_adapter`), no con `GeminiLLM.__dict__`, y la red sigue bloqueada."
9. "Los timeouts del SDK llegan como `httpx2.TimeoutException`, no como `httpx`: captúralos como timeout. Y si la respuesta no trae texto, devuelve una cadena vacía."

Qué generó la IA:
- Código: `app/llm/base.py`, `factory.py`, `mock.py`, `prompt.py`, `output.py` y `real.py`, y `app/analysis.py`, más cambios en `app/config.py` (proveedor, clave y modelo de Gemini, timeout) y `app/main.py` (`create_app` acepta un LLM).
- Tests: 67 nuevos (6 de la fábrica, 11 del prompt, 18 de la salida, 13 del mock, 10 de los reintentos, 2 del guardián y 7 del adaptador de Gemini) y el test amarillo Y3. También los 3 CV inventados de prueba, `ScriptedLLM`, `valid_output` y `read_cv` en `tests/helpers.py`, el guardián `block_real_llm` y el fixture `make_client` en `tests/conftest.py`, y la marca `real_llm_adapter` en `pytest.ini`.
- Dependencia nueva: `google-genai==3.6.1`; `pip-audit` no encontró avisos.
- Commits `4ebb4c5`, `b633ffc`, `5783eb9`, `f7661b4` y `0af056c`, hechos por mí. El commit `fb15954` (test amarillo Y3) lo hizo la IA, con su firma, por ser una tarea verde.

Cómo lo verifiqué:
- En cada tarea vi los tests en rojo antes de implementar y en verde después.
- `make check` en verde: 145 tests y 97 % de cobertura (100 % en el prompt, la validación, el servicio de análisis y el adaptador de Gemini).
- Calculé a mano las puntuaciones de los 3 CV (90, 30 y 90) y los casos de skills (13, 38 y 20), y coinciden con el mock. El CV malicioso da exactamente el mismo resultado que el limpio.
- Comprobé que ningún mensaje de error de la configuración contiene una clave, y que las claves no salen al imprimir `Settings`.
- El guardián del LLM real lo probé primero con un proveedor falso temporal y después con el `GeminiLLM` real: cualquier llamada lanza `RealLLMCalledInTests`.
- Durante la pausa se comprobó el SDK instalado: el timeout va en milisegundos y su cliente por defecto usa `httpx2`, cuyos timeouts no son `TimeoutError`. Rechacé capturar `httpx.TimeoutException`. El test del timeout de `httpx2` se pone en rojo si se quita esa captura.
- Y3: con un modelo falso de 50 ms por llamada, acertar a la primera cuesta 55 ms y 2.549 caracteres, y al tercer intento 158 ms y 7.647 caracteres: el coste crece con cada intento y el tope de 3 lo limita.
- Llamada real a Gemini, con el CV inventado del senior y la oferta de Backend Developer: `succeeded` al primer intento, en 1.033 ms, `match_score` 90 y 8 años. Las skills fueron `python`, `fastapi`, `sql` y `docker`. Es el mismo 90 que el mock. No anoté el resumen ni la clave.
- Revisión de la IA (modo C): no hecha. La revisión de esta rama fueron las pausas de cada parte.

Qué corregí a mano y por qué:
- No reescribí los archivos a mano. En cada pausa leí el resultado, lo rechacé cuando no cumplía una regla y cambié el encargo antes de seguir:
- `app/config.py`: el timeout por defecto pasó de 30 a 60 segundos, antes del commit de la tarea 5.1. Treinta segundos se queda corto para una respuesta JSON, y las dos claves siguen fuera del `repr`.
- `app/llm/mock.py`, `app/llm/prompt.py` y el test de tramos: los 30 puntos de años empiezan en 8, no en 6. De 3 a 7 años quedan en 20. Lo fijé yo para que el mock, el prompt y el test contaran la misma rúbrica.
- `app/llm/prompt.py` y `app/llm/mock.py`: la evidencia y las skills tenían que coincidir. Título completo, 20. Al menos la mitad de las palabras de 4 letras o más, 10. Si no, 0. Las skills salen en minúsculas, sin repetir y en el orden del CV.
- `tests/unit/test_gemini_adapter.py`: rechacé llegar al método real por `GeminiLLM.__dict__`. El guardián ya ha sustituido ese método, así que el test solo vería el rechazo. Los tests van con la marca `real_llm_adapter` y la red sigue bloqueada.
- `app/llm/real.py`: con esa comprobación del SDK, no acepté capturar `httpx.TimeoutException`. El cliente por defecto es `httpx2`, y un timeout real habría acabado como proveedor no disponible. También pedí que una respuesta sin texto devuelva `""`, para que sea una salida inválida y no un 500.
- La llamada real la ejecuté yo, con un CV inventado. La IA no leyó `.env` ni vio la respuesta.

Límites:
- La rúbrica se la pide el prompt a Gemini. El código no vuelve a calcular el `match_score`. La llamada real dio 90, igual que el mock, en un solo CV inventado. No prueba el resto de tramos.
- Los marcadores no obligan al modelo. La validación rechaza un JSON mal formado y no comprueba que la suma de la rúbrica sea la del `match_score`.
- No provoqué un timeout real contra Google. El mapeo de `httpx2` lo cubre un test con un cliente falso.
- Si el proceso fuerza el cliente `httpx`, ese timeout se vería como proveedor no disponible. El cliente por defecto es `httpx2`.
- `httpx2` no está fijado en `requirements.txt`. Llega porque `google-genai==3.6.1` depende de él. La versión instalada es 2.16.2.
- La comprobación de clave y modelo dentro de `make_llm` no tiene test. `load_settings` ya la hace, y esa línea queda sin cobertura. Está para que un `Settings` escrito a mano no llegue al SDK y este lea la clave del entorno.
- El test amarillo no pone un tope. El tope de 3 intentos ya está en el servicio, y solo se reintenta una salida inválida. Y3 mide el coste. Tampoco limita cuántas veces se puede pedir un análisis: el endpoint llega en la rama 6.
- La llamada real no pasó por HTTP. La hice con un script que llama a `run_analysis`. El aviso de Starlette desapareció porque el SDK instaló `httpx2` y el cliente de tests lo usa. `httpx==0.28.1` sigue fijado en las dependencias de desarrollo.
- El nivel gratuito puede usar los prompts para mejorar los productos de Google. Por eso el CV era inventado.

---

## Entrada 6 · feat/candidate-analysis · PR #6 · 2026-11-21
Modo: A, supervisión cercana (partes: tareas 6.1 y 6.2, por partes pequeñas con una pausa tras cada una).
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor. El resumen inicial de la rama lo hizo Sonnet 5.5.
Objetivo del PR: conectar el análisis con la API: guardar cada análisis en la tabla `analysis_runs`, añadir `POST /candidates/{id}/analyze` y mostrar el último análisis en `GET /candidates/{id}`.

Criterios que definí antes de pedir el código:
-Si `insert_analysis_run` recibe un fallo, `result` queda vacío. El endpoint de esta rama no la llama en ese caso.
- El último análisis correcto es el de `created_at` más reciente y, si empatan, el de `id` mayor. Solo cuenta ese candidato. Una referencia repetida la rechaza la base de datos.
- La oferta se limpia antes de medir y antes de buscar duplicados. El título tiene de 1 a 200 caracteres y las skills son de 1 a 30, cada una de 1 a 50. `["Python", " python "]` se rechaza. Un campo de más también.
- El candidato se carga antes de llamar al modelo. Si no existe, la respuesta es 404 y el modelo no se llama. El CV sale de la fila guardada, no del cuerpo. Los ids `0` y `2**63` dan 422, igual que en el GET.
- Si el análisis falla no se guarda ninguna fila. Una salida inválida o un proveedor caído dan 502, y un timeout da 504. El cuerpo lleva solo el código, el mensaje fijo y la referencia. El log es `warning`, con el id, el código, los intentos y la referencia.
- `latest_analysis` son solo los 4 campos del último resultado correcto, o `null`. No salen el proveedor, el modelo, los intentos, la referencia ni `error_detail`.

Prompts relevantes (traducidos del inglés):
1. "La tabla sigue el plan: sin columna del CV, `reference` única, `status` solo `succeeded` o `failed` y `candidate_id` apuntando a `candidates`. Las skills y el resultado se guardan como JSON, todo va con placeholders `?` y un análisis fallido guarda el resultado vacío."
2. "La fecha de cada análisis sale de `utc_now_iso()` de `app.db`, para que los tests de empate puedan sustituirla."
3. "El último análisis es: `SELECT result FROM analysis_runs WHERE candidate_id = ? AND status = 'succeeded' ORDER BY created_at DESC, id DESC LIMIT 1`, devuelto tal cual o `null`."
4. "En la oferta, el título y cada skill se limpian de espacios antes de comprobar la longitud y los duplicados: `["Python", " python "]` se rechaza."
5. "Carga primero el candidato: si no existe, 404 antes de llamar al modelo. El CV sale de la base de datos y la oferta ya limpia va al modelo."
6. "Si el análisis falla no se guarda nada: respuesta inválida o proveedor caído dan 502, timeout da 504, y el cuerpo lleva solo el código, el mensaje fijo y la referencia. El log es exactamente `analysis_failed candidate_id=… error_code=… attempts=… reference=…`, con nivel warning."
7. "`latest_analysis` en el GET tiene solo los 4 campos del resultado, o `null`; nada de proveedor, modelo, intentos, referencia ni `error_detail`."

Qué generó la IA:
- Código: en `app/db.py`, la tabla `analysis_runs`, `insert_analysis_run`, `LATEST_SUCCEEDED_SQL` y `get_latest_succeeded_result`; en `app/schemas.py`, `AnalyzeRequest` y el tipo real de `latest_analysis`; en `app/routers/candidates.py`, el endpoint de análisis y el último análisis en el GET; y `offer_payload` en `tests/helpers.py`.
- Tests: 24 escritos por la IA (3 de almacenamiento y 21 del endpoint). Los otros 6 de esta rama los escribí yo.
- Commits `e0a9c94` y `2f57e80`, hechos por mí.

Cómo lo verifiqué:
- En cada tarea vi los tests en rojo antes de implementar y en verde después.
- `make check` en verde: 175 tests y 97 % de cobertura (100 % en el router de candidatos y en los esquemas).
- Con un script aparte comprobé que la base de datos rechaza por sí misma una referencia repetida, un análisis de un candidato que no existe y un `status` distinto de `succeeded` o `failed`, y que tras cada rechazo no queda ninguna fila a medias.
- Comprobé las tres respuestas de error (502, 504 y 502) y sus líneas de log: solo llevan códigos, ids y la referencia, y no se guarda ninguna fila.
- Un candidato que no existe da 404 sin llamar al modelo (`llm.calls == 0`), y un id fuera de rango da 422 también sin llamarlo.
- El test del límite conocido muestra que una puntuación manipulada pero válida (100 en vez de 90) se acepta; queda documentado y enlazado al Issue de contraste de skills.
- Al mover mis tres tests al fichero correcto, la IA dejó fuera la última línea (no tenía salto de línea final); lo vio enseguida y la restauró tal cual.
- Revisión de la IA (modo C): no hecha. La revisión de esta rama fueron las pausas de cada parte.

Qué corregí a mano y por qué:
- No reescribí el router ni la base de datos a mano. Paré en cada pausa y cambié el encargo, y además escribí 6 tests yo:
- En `tests/unit/test_db.py`: el de la fecha más nueva frente al id más alto, el de que un candidato no ve el análisis de otro, y el de la referencia repetida. Los tres cubren reglas que los tests del plan no fijaban.
- En `tests/integration/test_analyze_api.py`: el de los ids `0` y `2**63` sin llamar al modelo, el duplicado después de quitar espacios, y el de que la oferta se guarda ya limpia. Los pegué primero en el fichero de la base de datos; la IA los movió tal cual al fichero del endpoint.
- Ejecuté `ruff format` yo en esos dos ficheros de tests. Solo cambia el formato, no lo que comprueban.
- El log de un análisis fallido se queda en `warning`. `error` queda para una excepción no controlada, e `info` para un hecho normal como crear un candidato.

Límites:
- Esta rama no guarda los análisis fallidos. Un 502 o un 504 no deja fila, así que la referencia todavía no se puede buscar en la base de datos. Eso llega en la rama 7.
- Una puntuación válida pero equivocada se acepta y el GET la devuelve. El test del 100 en el CV malicioso lo documenta y apunta al Issue 2. Ni la validación ni el GET vuelven a calcular la rúbrica.
- No probé una fila de resultado dañada. `model_validate` haría fallar el GET en vez de devolver un análisis a medias.
- `casefold()` trata `ß` y `ss` como la misma skill. No hay un test con ese par. Con los nombres normales el resultado es el de pasar a minúsculas.
- No hay un tope de cuántas veces se puede llamar a `POST /candidates/{id}/analyze`. Cada petición válida de un candidato que existe llama al modelo.

---

## Entrada 7 · feat/audit-trail · PR #7 · 2026-11-21
Modo: A, supervisión cercana (partes: tareas 7.1 y 7.2, por partes pequeñas con una pausa tras cada una) · B, automático (parte: tarea 7.3, test amarillo).
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor. El resumen inicial de la rama lo hizo Sonnet 5.5.
Objetivo del PR: la auditoría que pide el enunciado: registrar también los análisis fallidos y añadir `GET /candidates/{id}/audit`, que muestra todos los intentos de un candidato sin exponer el CV ni el detalle de los errores. Cierra el Issue #1.

Criterios que definí antes de pedir el código:
- Un análisis fallido se guarda antes de devolver el 502 o el 504, con la misma llamada que el caso de éxito. `result` queda vacío, `error_detail` es solo el resumen seguro y la referencia de la respuesta es la de la fila. El GET sigue ignorando las filas fallidas.
- Las dos consultas de la auditoría filtran con `WHERE candidate_id = ?`. La de la página ordena por `created_at DESC, id DESC` y usa `LIMIT ? OFFSET ?`. Solo se leen las 13 columnas. `error_detail` no se selecciona.
- `AuditItem` tiene exactamente esos 13 campos y ningún `error_detail`. `status` solo puede ser `succeeded` o `failed`. `result` son los 4 campos o `null`. Los dos modelos son estrictos y rechazan campos de más.
- `GET /candidates/{id}/audit` usa los mismos límites de id que el GET. Si el candidato no existe, responde 404 antes de consultar. `limit` va de 1 a 100, por defecto 20. `offset` va de 0 a 1.000.000, por defecto 0. Sin clave responde 401.

Prompts relevantes (traducidos del inglés):
1. "Antes de devolver el 502 o el 504, guarda el análisis fallido con la misma llamada que usa el caso de éxito. No cambies la respuesta, el log ni el GET."
2. "Las dos consultas de la auditoría filtran con `WHERE candidate_id = ?`; la de la página ordena por `created_at DESC, id DESC` y termina en `LIMIT ? OFFSET ?`. Todo con placeholders, y solo las 13 columnas de la auditoría: nunca `error_detail`."
3. "`AuditItem` tiene los 13 campos y ningún campo `error_detail`, ni siquiera opcional. Los dos modelos son estrictos y sin campos extra; el estado se queda como los dos valores permitidos."
4. "El endpoint usa los mismos límites de id que el GET, da 404 antes de consultar si el candidato no existe, acepta `limit` de 1 a 100 (20 por defecto) y `offset` de 0 a 1.000.000."

Qué generó la IA:
- Código: en `app/routers/candidates.py`, guardar el resultado antes de responder también en los fallos; en `app/db.py`, `AUDIT_PAGE_SQL`, `AUDIT_COUNT_SQL`, `list_analysis_runs` y `count_analysis_runs`; en `app/schemas.py`, `AuditItem` y `AuditPage`; el router nuevo `app/routers/audit.py`, registrado en `app/main.py`.
- Tests: 22 escritos por la IA (8 del registro de fallos y 14 del endpoint de auditoría) y el test amarillo Y4. Los otros 3 del registro los escribí yo.
- Commits `febf515` y `c269551`, hechos por mí. El commit `72bf327` (test amarillo Y4) lo hizo la IA, con su firma, por ser una tarea verde.

Cómo lo verifiqué:
- En cada tarea vi los tests en rojo antes de implementar y en verde después.
- `make check` en verde: 200 tests y 97 % de cobertura (100 % en el router de auditoría).
- Abrí yo una fila fallida con `sqlite3`: estado `failed`, 3 intentos, `llm_invalid_output`, `error_detail` solo con `summary: string_too_long` (sin texto del CV), resultado vacío, y la misma referencia que el log.
- Con un script aparte comprobé que las consultas de la auditoría solo leen las 13 columnas (sin `error_detail`), que cada candidato solo ve sus filas y su propio total, y que el orden y la paginación son correctos.
- Los modelos rechazan un `error_detail` que se les pase, un estado distinto de `succeeded` o `failed` y las skills como texto JSON.
- Los tests de autenticación cubren ya la ruta `/audit`: sin clave da 401.
- Y4, antes del índice: con 10.000 análisis por candidato, la primera página de la auditoría tarda 8 ms y la última 15,5 ms, y las dos consultas hacen `SCAN analysis_runs` con una ordenación temporal. Es la medida de "antes" para la rama 8.
- Revisión de la IA (modo C): no hecha. La revisión de esta rama fueron las pausas de cada parte.

Qué corregí a mano y por qué:
- No reescribí el router ni las consultas a mano. Paré en cada pausa y cambié el encargo, y escribí 3 tests yo:
- En `tests/integration/test_audit_recording.py`: la referencia del 502 es la de la fila, un fallo guarda `result` vacío y la oferta ya limpia, y un error del proveedor queda con `attempts == 1` y `provider_error:LLMUnavailableError`. El plan no cubría esos tres casos.
- Ejecuté `ruff format` yo en ese fichero. Solo cambia el formato.
- `status` se queda como `Literal["succeeded", "failed"]`. Un texto libre aceptaría un estado que la base de datos rechaza.

Límites:
- `error_detail` sigue guardado en la base de datos. El endpoint no puede mostrarlo, porque ni la consulta ni el modelo lo tienen. Quien abra el archivo sí puede leerlo.
- No hay un test del `offset` 1.000.001 ni de los ids `0` y `2**63` en `/audit`. El código los rechaza igual que en el GET y en el análisis.
- Y4 es la medida de antes del índice. Con 10.000 análisis las dos consultas todavía hacen `SCAN analysis_runs`. El índice llega en la rama 8.
- Una puntuación válida pero equivocada se guarda y la auditoría la muestra. Es el mismo límite que en la rama 6.

---

## Entrada 8 · perf/benchmarks · PR #10 · 2026-11-21
Modo: B, automático (parte: tarea 8.1, el índice y sus tests).
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor. El resumen inicial de la rama lo hizo Sonnet 5.5.
Objetivo del PR: acelerar las consultas de `analysis_runs` con un índice por candidato y demostrarlo con el plan de consulta y con el test amarillo Y4, antes y después.

Criterios que definí antes de pedir el código:
- La tarea 8.1 ya estaba en verde: un índice mal puesto solo haría las consultas más lentas, y los tests del plan de consulta lo agarran. Por eso no la partí en pausas. La IA escribe el índice y los tests, pasa `make check` y hace el commit, con su firma.
- No añadí criterios míos. Los que ya valían son estos: un solo índice, `idx_analysis_runs_candidate`, sobre `analysis_runs(candidate_id, created_at DESC, id DESC)`, con `CREATE INDEX IF NOT EXISTS`.
- Los tests comprueban el nombre del índice y que no aparezca `SCAN analysis_runs`. No fijan el texto completo del plan.
- La prueba de una tarea verde: quitar la línea del índice pone los tests en rojo, y devolverla los deja en verde.

Prompts relevantes (resumidos y traducidos del inglés):
1. "Continúa con la tarea 8.1."

Qué generó la IA: el índice `idx_analysis_runs_candidate` sobre `analysis_runs(candidate_id, created_at DESC, id DESC)` en `app/db.py`, y `tests/unit/test_query_plans.py` con 3 tests. Commit `68765eb`, hecho por la IA, con su firma, por ser una tarea verde.

Cómo lo verifiqué:
- `make check` en verde: 203 tests y 97 % de cobertura.
- Los tests miran solo el nombre del índice y que no aparezca `SCAN analysis_runs`, no el texto completo del plan, porque mi Mac, la imagen de Docker y el CI usan versiones distintas de SQLite y las describen de forma algo distinta.
- Antes del índice, el último análisis y la página de auditoría salían como `SCAN analysis_runs / USE TEMP B-TREE FOR ORDER BY`. El recuento salía como `SCAN analysis_runs`, sin esa ordenación, porque esa consulta no tiene `ORDER BY`. El tercer test fallaba porque el índice no estaba en `sqlite_master`. Con el índice, las tres consultas pasan a `SEARCH analysis_runs USING INDEX idx_analysis_runs_candidate`; las dos que ordenan ya no crean el árbol temporal, y el recuento usa un índice de cobertura.
- Al quitar la línea del índice los 3 tests se ponen en rojo, y al devolverla vuelven a verde.
- Y4, con 10.000 análisis por candidato y 5 candidatos más (mediana de 5 peticiones):

  | Petición | Antes | Después |
  |---|---|---|
  | `GET /candidates/{id}` | 4,19 ms | 1,48 ms |
  | Auditoría, primera página | 8,18 ms | 2,34 ms |
  | Auditoría, última página | 15,69 ms | 1,55 ms |

  Con 1.000 análisis la mejora es pequeña (la última página pasa de 1,95 ms a 1,11 ms), porque hay poco que recorrer.

Qué corregí a mano y por qué:
- Nada. No reescribí `app/db.py` ni los tests, y no cambié el encargo. El único prompt fue continuar la tarea 8.1. Al ser de bajo riesgo, la comprobación es `make check` y la prueba de quitar y devolver el índice, no una corrección a mano.

Límites:
- Los tiempos son de mi máquina y de peticiones sueltas: varían de una ejecución a otra, por eso lo importante es el cambio del plan y la mejora de la última página, no las cifras exactas.
- Las bases de datos que ya existían reciben el índice la próxima vez que arranca la app (`CREATE INDEX IF NOT EXISTS`); con muchos datos, crearlo la primera vez puede tardar.
- El `EXPLAIN QUERY PLAN` de los 3 tests corre sobre una base recién creada, sin las 10.000 filas. Con esas filas solo medí tiempos, no volví a pedir el plan.
- No hice revisión en modo C. En una tarea verde el control es el que queda arriba.

---

## Entrada 9 · ci/quality-gates · PR #12 · 2026-11-21
Modo: B, automático (partes: el job de auditoría de dependencias y el umbral de cobertura), con la prueba de que el job falla hecha por mí.
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor. El resumen inicial de la rama lo hizo Sonnet 5.5.
Objetivo del PR: dos controles nuevos en el CI: un job que falla si alguna dependencia tiene una vulnerabilidad conocida, y un mínimo de cobertura del 80 % en el CI y en `make check`.

Criterios que definí antes de pedir el código:
- La tarea 9.1 estaba en verde, salvo el paso 2, que es rojo y lo hago yo. El job y el umbral los escribe la IA, pasa `make check` y hace el commit, con su firma. Esa parte no la partí en pausas.
- No añadí criterios míos. Los que ya valían: un job `dependency-audit` con `pip-audit` sobre `requirements.txt` y `requirements-dev.txt`, sin cambiar los otros jobs.
- `--cov-fail-under=80` entra solo si las tres últimas ejecuciones del CI están en 80 % o más. La decisión es mía, y las tres lo estaban.
- La prueba de que el job se pone rojo es mía, en otra rama, y esa rama no se fusiona.

Prompts relevantes (traducidos del inglés):
1. "Ya actualicé la rama. Haz la tarea 9.1 y para en el paso 2."
2. "Añade `--cov-fail-under=80` al pytest del CI y de `make check`, sin tocar los ficheros de dependencias. Enséñame que con un 99 % falla en local, pasa `make check` y, si está en verde, haz el commit."

Qué generó la IA:
- En `.github/workflows/ci.yml`, el job `dependency-audit`, que ejecuta `pip-audit -r requirements.txt -r requirements-dev.txt`, y `--cov-fail-under=80` en el pytest de `lint-and-test`.
- En el `Makefile`, el mismo umbral en `make check` y un objetivo nuevo, `make audit`.
- Commit `5691cb6`, hecho por la IA, con su firma, por ser una tarea verde.

Cómo lo verifiqué:
- `pip-audit` en local no encontró vulnerabilidades en el conjunto completo de dependencias.
- Abrí la pull request #11 desde `throwaway/audit-check`, con `pyyaml==5.3.1` añadido a `requirements.txt`. `dependency-audit` se puso en rojo. `lint-and-test` y `performance` siguieron en verde. La cerré sin fusionarla y borré la rama.
- La cobertura de las tres últimas ejecuciones del CI era de al menos el 80 % (la última, 97 %).
- En local, `pytest --cov=app --cov-fail-under=99` falla ("Required test coverage of 99% not reached. Total coverage: 97.40%"), y `make check` pasa con el umbral del 80 %.
- Revisión de la IA (modo C): no hecha. La parte verde se comprueba con `make check`, y el job con la pull request desechable.

Qué corregí a mano y por qué:
- Nada en `ci.yml` ni en el `Makefile`. No cambié ese encargo: la IA lo escribió y lo commiteó en `5691cb6`.
- La prueba en rojo la hice yo, a mano, como queda arriba. Esa rama no entra en este commit.

Límites:
- `pip-audit` solo avisa de vulnerabilidades ya publicadas. Una dependencia mala sin aviso conocido pasa el job.
- El 80 % queda lejos del 97 % actual. Una bajada pequeña no hace fallar el CI.
- Esta pull request todavía no está abierta, así que aún no he visto el job y el umbral en verde sobre la rama buena.
---

## Entrada 10 · build/docker · PR #13 · 2026-11-21
Modo: B, delegado con un punto de control (parte: tarea 10.1, los tres ficheros de Docker). Las comprobaciones con mi `.env` real las hice yo.
Herramienta: Claude Code con Opus 5.5 (`claude-opus-5-5`), desde Cursor. El resumen inicial de la rama lo hizo Sonnet 5.5.
Objetivo del PR: empaquetar la app para arrancarla solo con Docker: una imagen con usuario sin privilegios y la base de datos en un volumen que sobrevive a los reinicios.

Criterios que definí antes de pedir el código:
- La tarea 10.1 estaba en amarillo: la IA escribe los tres ficheros de una vez y se para en el punto de control. Las comprobaciones con mi `.env` y el commit los hago yo.
- El puerto publicado es `127.0.0.1:8000:8000`. Las pruebas usan `localhost`, y `/docs` responde sin clave, así que el puerto no queda abierto en el resto de la red.
- No añadí `PYTHONUNBUFFERED` ni `PYTHONDONTWRITEBYTECODE`. No están en el plan, y el error del paso 5 se lee igual en los logs.
- El resto es el que ya valía: imagen fijada por el digest de M12, solo `requirements.txt` y `app/`, sin `COPY . .`, `appuser` dueño de `/data`, `USER` antes de `CMD`, `--factory`, y el volumen en `/data`.

Prompts relevantes (traducidos del inglés):
1. "Escribe el `Dockerfile`, el `docker-compose.yml` y el `.dockerignore`, y para en el punto de control. No leas mi `.env`, no hagas las comprobaciones con él y no hagas commit."
2. "El `Dockerfile` parte de `python:3.13-slim` fijado por el digest multiplataforma del paso M12, nunca por la etiqueta. Instala solo `requirements.txt`, copiado antes que `app/`, y copia solo `app/`: nada de `COPY . .`. Crea `appuser` y `/data` con ese dueño, y `USER appuser` va antes de `CMD`. El `CMD` es `uvicorn app.main:build_app --factory --host 0.0.0.0 --port 8000`."
3. "En el `docker-compose.yml`, publica el puerto solo en mi ordenador (`127.0.0.1:8000:8000`), usa `env_file: .env`, fuerza `DATABASE_PATH=/data/talentlite.db`, monta el volumen `talentlite_data` en `/data` y pon `restart: unless-stopped`."
4. "No añadas `PYTHONUNBUFFERED` ni `PYTHONDONTWRITEBYTECODE`."
5. "Cambia `__pycache__` por `**/__pycache__` en el `.dockerignore`, y deja el resto igual."

Qué generó la IA:
- `Dockerfile`: imagen fijada por digest, dependencias de producción antes que el código, solo `app/` copiado, `appuser` con su carpeta `/data` y `USER appuser` antes de `CMD`.
- `docker-compose.yml`: el servicio `api`, el puerto en `127.0.0.1`, `.env` pasado en tiempo de ejecución, `DATABASE_PATH` forzado, el volumen y la política de reinicio.
- `.dockerignore`: `.env`, `.git`, `.venv`, `**/__pycache__`, `*.db`, `.github` y `tests`.
- Antes de que yo empezara las comprobaciones, la IA repasó cinco puntos del `Dockerfile` y del compose (que `.env` no entra en la imagen, `USER` antes de `CMD`, `/data` con el dueño correcto, el volumen igual que `DATABASE_PATH`, y `--factory`) y avisó de que `__pycache__` solo ignoraba la carpeta raíz, no las de `app/`. Esas carpetas llevan la ruta de mi ordenador dentro.
- Commit `a5ec663`, hecho por mí, sin la firma de la IA.

Cómo lo verifiqué:
- `make check` en verde: 203 tests y 97 % de cobertura. Esta rama no cambia código de la app.
- Arranqué la app con `docker compose up --build -d` con mi `.env` real: con la clave, `/health` responde `{"status":"ok"}`; sin ella, 401.
- Dentro del contenedor, el usuario no es root y `/app` no tiene `.env`, `tests` ni `.git`.
- Los datos persisten: creé un candidato y lo recuperé después de `docker compose restart` y de `docker compose down` seguido de `up -d`.
- Con `API_KEY=cambia-esto` el proceso sale con `API_KEY is still the placeholder from .env.example.` y no imprime la clave. Compose lo vuelve a arrancar hasta que hago `docker compose down`.
- Repetí la comprobación desde un clon limpio de la rama `build/docker`, para confirmar que la imagen no depende de nada que solo exista en mi ordenador.
- Revisión de la IA (modo C): no hecha. La revisión de esta rama fue el punto de control, y las comprobaciones del contenedor las hice yo.

Qué corregí a mano y por qué:
- No reescribí el `Dockerfile` ni el `docker-compose.yml`.
- Tras el punto de control pedí un solo cambio: en `.dockerignore`, `__pycache__` pasó a `**/__pycache__`. La línea suelta no ignoraba las carpetas de dentro de `app/`, y esos `.pyc` guardan la ruta de mi ordenador. El cambio lo escribió la IA.
- Las comprobaciones de los pasos 2 a 5, también en un clon limpio, y el commit `a5ec663` los hice yo. Al ser amarillo, el commit no lleva la firma de la IA.

Límites:
- Lo probé en mi Mac. El CI no construye la imagen.
- `env_file: .env` mete todo el fichero en el contenedor en marcha, también una clave de Gemini si estuviera. No queda en la imagen.
- Con `restart: unless-stopped`, una clave mala reinicia el contenedor hasta que se hace `docker compose down`.
- El puerto solo escucha en este ordenador. Desde otra máquina de la red no se llega a la API.
