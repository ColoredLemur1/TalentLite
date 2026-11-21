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
