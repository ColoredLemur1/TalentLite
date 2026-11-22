# TalentLite

API REST en FastAPI y SQLite que registra candidatos ficticios, analiza su CV contra una oferta de trabajo con un modelo de lenguaje (un simulador por defecto, Gemini de forma opcional) y guarda un registro de auditoría de cada análisis. Es mi prueba técnica para B-Green. Todos los datos del repositorio son inventados.

Índice: [Inicio](#inicio-en-menos-de-5-minutos) · [Ejemplos con curl](#ejemplos-con-curl) · [Pruebas](#pruebas) · [Gemini](#activar-gemini) · [Decisiones](#decisiones) · [Rúbrica](#rúbrica-de-puntuación) · [Auditoría](#auditoría) · [Rendimiento](#rendimiento) · [Límites](#límites-conocidos) · [Seguridad](#seguridad) · [Despliegue](#despliegue) · [Fuera de alcance](#qué-queda-fuera)

## Inicio en menos de 5 minutos

Se necesita Docker. Python solo se usa para generar la clave.

```bash
cp .env.example .env
```

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Pega el resultado como valor de `API_KEY` en `.env`. La app no inicia con la clave de ejemplo (`cambia-esto`), ni sin clave, ni con menos de 32 caracteres. Después:

```bash
docker compose up --build
```

La API queda en `http://localhost:8000`, publicada solo en tu computadora. La documentación interactiva está en `http://localhost:8000/docs` y se abre sin clave; para probar las rutas desde ahí, el botón **Authorize** pide la clave.

Para detenerlo: `docker compose down`. Los datos están en un volumen y sobreviven. `docker compose down -v` borra el volumen y los datos con él.

| Variable de `.env` | Para qué sirve |
|---|---|
| `API_KEY` | La clave que piden todas las rutas en la cabecera `X-API-Key` |
| `LLM_PROVIDER` | `mock` (por defecto) o `gemini` |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Solo si se usa Gemini |
| `GEMINI_TIMEOUT_SECONDS` | Espera máxima a Gemini; 60 si está vacía |
| `DATABASE_PATH` | Ruta del archivo SQLite. `docker-compose.yml` la fija en `/data/talentlite.db` |

## Ejemplos con curl

Usa la misma clave que pusiste en `.env`:

```bash
export API_KEY=pega-aqui-la-clave
```

Comprobar que la API responde:

```bash
curl -s -H "X-API-Key: $API_KEY" http://localhost:8000/health
```

```json
{"status":"ok"}
```

Sin la clave, cualquier ruta responde 401 y no dice nada más:

```bash
curl -s http://localhost:8000/health
```

```json
{"error":{"code":"unauthorized","message":"Missing or invalid API key."}}
```

Crear un candidato (`POST /candidates`):

```bash
curl -s -X POST http://localhost:8000/candidates -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" -d '{"name": "Ana Torres", "email": "ana.torres@example.com", "cv_text": "Backend Developer con 3 años de experiencia en Python, FastAPI y SQL."}'
```

```json
{"id":1,"name":"Ana Torres","email":"ana.torres@example.com","cv_text":"Backend Developer con 3 años de experiencia en Python, FastAPI y SQL.","created_at":"2026-11-22T00:06:20Z","latest_analysis":null}
```

Leer un candidato (`GET /candidates/{id}`):

```bash
curl -s http://localhost:8000/candidates/1 -H "X-API-Key: $API_KEY"
```

Analizar el CV contra una oferta (`POST /candidates/{id}/analyze`). Recibe solo el título y las skills; el CV se lee de la base de datos:

```bash
curl -s -X POST http://localhost:8000/candidates/1/analyze -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" -d '{"job_title": "Backend Developer", "required_skills": ["Python", "FastAPI", "SQL", "Docker", "Kubernetes"]}'
```

```json
{"skills":["python","fastapi","sql"],"years_experience":3.0,"summary":"3 años de experiencia; cumple 3 de 5 skills requeridas para Backend Developer.","match_score":70}
```

Después de analizar, el `GET` del candidato trae ese resultado en `latest_analysis`. El historial completo está en la auditoría (`GET /candidates/{id}/audit`, con `limit` y `offset`):

```bash
curl -s "http://localhost:8000/candidates/1/audit?limit=20&offset=0" -H "X-API-Key: $API_KEY"
```

Un email repetido da un 409 y no repite el email en la respuesta:

```json
{"error":{"code":"conflict","message":"Resource already exists."}}
```

Todos los errores tienen el mismo formato, `{"error": {"code", "message", ...}}`:

| Código HTTP | `code` | Cuándo |
|---|---|---|
| 401 | `unauthorized` | Falta la clave o es incorrecta |
| 404 | `not_found` | El candidato no existe |
| 405 | `method_not_allowed` | Método no permitido en esa ruta |
| 409 | `conflict` | El email ya está registrado |
| 413 | `payload_too_large` | El cuerpo supera 256 KiB |
| 422 | `validation_error` | Entrada inválida (sin repetir el valor enviado) |
| 500 | `internal_error` | Error inesperado, con una `reference` |
| 502 | `llm_invalid_output`, `llm_unavailable` | El modelo respondió mal o no está disponible, con una `reference` |
| 504 | `llm_timeout` | El modelo no respondió a tiempo, con una `reference` |

## Pruebas

Las pruebas no necesitan `.env`, no llaman a Gemini ni usan la red. Para ejecutarlas se necesita un entorno virtual con Python 3.13:

```bash
python3.13 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements-dev.txt
```

| Comando | Qué hace |
|---|---|
| `make check` | `ruff check`, `ruff format --check` y `pytest` con cobertura. Falla por debajo del 80 % |
| `make perf` | Ejecuta los tests amarillos de rendimiento (miden, no fallan) |
| `make audit` | `pip-audit` sobre las dependencias |

El CI repite las mismas comprobaciones en una máquina limpia, ejecuta la auditoría de dependencias y los tests amarillos en un job que no bloquea.

## Activar Gemini

Por defecto se usa el simulador (`mock`): es gratis, determinista y no usa la red. Para probar Gemini:

1. En `.env`, pon `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=<tu clave>` y `GEMINI_MODEL=<el ID del modelo, copiado de AI Studio>`. Opcionalmente, `GEMINI_TIMEOUT_SECONDS`.
2. Recrea el contenedor para que lea el `.env`: `docker compose up -d --force-recreate`.
3. Cuando termines, vuelve a poner `LLM_PROVIDER=mock`.

Usa el plan gratuito solo con CVs inventados: ese plan puede usar el contenido enviado para mejorar los productos de Google. Si `LLM_PROVIDER=gemini` y falta la clave o el modelo, la app no inicia. Los tests nunca llaman a Gemini.

## Decisiones

Cada decisión tiene un identificador (`Dxx`). Las marcadas con *cambió* se decidieron distinto al implementarlas.

### Plataforma y estructura

- **D1.** Python 3.13 con FastAPI: la validación con Pydantic viene incluida y `/docs` sale gratis.
- **D2.** SQLite con `sqlite3`, consultas parametrizadas y sin ORM: pocas consultas, fáciles de explicar línea a línea y sin inyección SQL.
- **D3.** `requirements.txt` y `requirements-dev.txt` con versiones fijadas con `==`: simple, y el CI instala directamente de ahí.
- **D14.** IDs enteros autoincrementales, no UUID: simple, y enumerarlos es poco riesgo con una sola clave compartida. Los UUID quedan como mejora.
- **D32.** Fechas en UTC, ISO 8601 acabadas en `Z`, generadas en Python: SQLite no guarda zona horaria y así se pueden probar.
- **D33.** Fábrica `create_app(settings)`; se inicia con `app.main:build_app --factory`. Cada test crea su app con una base temporal y una clave de prueba, y el entorno solo se lee en `build_app`. *Cambió:* el plan decía `app.main:app`.
- **D34.** Una conexión `sqlite3` por petición, con `PRAGMA foreign_keys = ON`, y las tablas se crean al iniciar con `CREATE TABLE IF NOT EXISTS`: las rutas síncronas corren en hilos y compartir una conexión es un error clásico de SQLite.
- **D35.** Sin migraciones: si cambia el esquema, se borra el archivo de la base de datos. Límite documentado.

### Autenticación y capa HTTP

- **D4.** Una clave en la cabecera `X-API-Key`, leída del entorno y sin login: es lo que pide el enunciado. No identifica a cada persona.
- **D5.** La clave se comprueba en un middleware ASGI puro, antes que nada. Solo `/docs`, `/docs/oauth2-redirect`, `/redoc` y `/openapi.json` quedan exentos, por coincidencia exacta de ruta. Con una dependencia de FastAPI, el cuerpo se decodificaría antes y una petición sin clave y con JSON roto daría 422 en vez de 401.
- **D6.** La clave se compara con `secrets.compare_digest` sobre bytes: con `str`, una cabecera no ASCII daría un 500.
- **D7.** La app no inicia si falta `API_KEY`, es `cambia-esto` o tiene menos de 32 caracteres. Mejor fallar al empezar que avisar y seguir.
- **D8.** `/health` exige la clave y responde `{"status": "ok"}` (solo comprueba que el proceso vive, no la base de datos): el enunciado dice que todo endpoint pide token.
- **D9.** `/docs` queda abierto, útil para probar y defender. Es un límite documentado; apagarlo con una variable queda como mejora.
- **D13.** Límite de cuerpo en el servidor de 256 KiB (262.144 bytes). Se mira `Content-Length` y, si falta, se cuentan los bytes mientras se lee. Responde 413. El peor CV válido (20.000 emojis escritos como `\uXXXX`) ocupa unos 240.000 bytes, así que nunca rechaza un CV válido.
- **D36.** Cabeceras de seguridad en todas las respuestas, también en los errores: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` y `Cache-Control: no-store`. No hay CSP, porque rompería `/docs`.
- **D37.** Orden de los middlewares, de fuera a dentro: cabeceras -> captura de errores -> autenticación -> límite de cuerpo -> app. *Cambió:* se añadió la captura de errores (ver abajo).

### Errores

- **D15.** Un solo formato de error, `{"error": {"code", "message", "reference"?, "details"?}}`, con los códigos de la tabla de arriba. Lo usan también los middlewares.
- **D16.** El 422 lleva `details` con `loc`, `msg` y `type`, y quita `input` y `ctx`, que Pydantic incluye por defecto: nunca devuelve el valor enviado.
- **D25.** Los 502 y 504 llevan un mensaje genérico y una `reference` aleatoria (`secrets.token_hex(8)`) guardada en la fila de auditoría, no el id de la fila.
- Una excepción no controlada devuelve un 500 genérico con una `reference`. El log lleva la referencia y el tipo de la excepción, no su mensaje.

### Candidatos

- **D10.** Email repetido -> 409. El email se normaliza con `strip()` y `lower()`. La garantía es `UNIQUE` en la base de datos: no hay consulta previa, se captura el `IntegrityError`.
- **D11.** `POST /candidates` recibe `name`, `email` y `cv_text`. `POST /candidates/{id}/analyze` recibe solo `job_title` y `required_skills`; el CV se lee de la base por `id`.
- **D12.** Límites de entrada, todos con campos extra prohibidos y tipos estrictos:

| Campo | Regla |
|---|---|
| `name` | texto sin espacios alrededor, de 1 a 100 caracteres |
| `email` | email válido, máximo 254 caracteres, normalizado |
| `cv_text` | de 1 a 20.000 caracteres tal cual, no vacío tras quitar espacios; se guarda sin recortar |
| `job_title` | texto sin espacios alrededor, de 1 a 200 caracteres |
| `required_skills` | lista de 1 a 30 elementos de 1 a 50 caracteres sin espacios alrededor; sin repetidos, ignorando mayúsculas |
| `limit` (auditoría) | entero de 1 a 100, 20 por defecto |
| `offset` (auditoría) | entero de 0 a 1.000.000, 0 por defecto |
| `id` en la ruta | entero de 1 a 2^63 − 1 |

### Capa de IA

- **D17.** `skills` son las skills encontradas en el CV. El simulador las busca entre las requeridas y un vocabulario fijo de unas 30, sin distinguir mayúsculas y como palabra completa (`Java` no coincide con `JavaScript`, `C++` funciona). Las devuelve en minúsculas, sin repetir y en orden de aparición en el CV.
- **D18.** `years_experience` es 0 si el CV no dice nada. El simulador toma el mayor de patrones como `5 years`, `5+ years` o `5 años`, con un tope de 50.
- **D19.** Rúbrica 50/30/20 por tramos (ver [Rúbrica de puntuación](#rúbrica-de-puntuación)). *Cambió:* los tramos de años no son los del plan.
- **D20.** El simulador (`mock-keyword-v1`) lee el prompt que recibe y extrae la oferta y el CV de sus bloques. Así usa el constructor real del prompt, y si el formato se rompe, sus tests fallan.
- **D21.** Interfaz `LLMClient.complete(system, user) -> str` con texto crudo. Los proveedores lanzan `LLMTimeoutError` o `LLMUnavailableError`. La validación está fuera de los proveedores: un solo camino para el simulador y para Gemini.
- **D22.** Todas las instrucciones y el esquema de salida van en el mensaje de sistema. El de usuario lleva dos bloques de datos, la oferta y el CV, entre marcadores con un nonce aleatorio de 32 caracteres por petición (`BEGIN-CV-<nonce>`, `END-CV-<nonce>`). El de sistema dice que lo que hay entre marcadores es dato y que sus instrucciones no se siguen. `PROMPT_VERSION = "v1"`.
- **D23.** La respuesta del modelo se valida con un esquema estricto: `skills` de 0 a 50 textos de 1 a 100 caracteres; `years_experience` de 0 a 80; `summary` de 1 a 400; `match_score` entero estricto de 0 a 100 (rechaza `85.5`, `"85"` y `true`); sin campos extra. `NaN` e `Infinity` se rechazan al leer el JSON. Se tolera un único bloque ```` ```json ````. Cualquier otro texto alrededor la invalida.
- **D24.** Máximo 3 intentos en total, solo si la salida es inválida y con el mismo prompt. Un timeout da 504 y un error del proveedor da 502, ambos sin reintento: repetirlos solo añade espera y coste.
- **D39.** Gemini solo en un proyecto sin facturación y con CVs inventados, con timeout. `LLM_PROVIDER` se pasa a minúsculas y solo acepta `mock` o `gemini`. `gemini` sin clave o sin modelo no inicia. *Cambió:* el timeout por defecto es de 60 s.

### Análisis, historial y auditoría

- **D26.** Cada llamada a `analyze` crea una fila nueva y nada se sustituye: cada fila conserva su oferta.
- **D27.** La auditoría es la tabla `analysis_runs`, que se lee con un cuarto endpoint, `GET /candidates/{id}/audit`. Es de solo lectura, pide la clave como todo y está paginado. Si el candidato no existe, 404. *Cambió:* el plan base no tenía endpoint nuevo.
- **D28.** `GET /candidates/{id}` devuelve solo lo que lista el enunciado: `id`, `name`, `email`, `cv_text`, `created_at` y `latest_analysis` con exactamente `skills`, `years_experience`, `summary` y `match_score`. Nada del modelo, la oferta ni los intentos fallidos. *Cambió:* el plan base leía el historial en el `GET` del candidato, sin endpoint nuevo.
- **D29.** `error_detail` guarda solo rutas de campo y tipos de error (por ejemplo `match_score: less_than_equal`), con un máximo de 500 caracteres. Nunca la salida cruda del modelo, que puede repetir el CV.
- **D30.** `latest_analysis` es el análisis **correcto** más reciente, o `null` antes del primero. Un intento fallido nunca sustituye a uno bueno.
- **D31.** La auditoría va del más nuevo al más antiguo, con `id` descendente como desempate. `total` cuenta los intentos correctos y los fallidos.
- **D40.** `POST /candidates/{id}/analyze` responde 200 con el análisis. 201 también sería defendible.

### Tests y CI

- **D38.** La cobertura mínima es del 80 %, y bloquea el CI y `make check`. Es lo que pretendía el plan; la real es del 97 %.
- **D41.** El marcador `performance` está registrado, y `pytest` por defecto lo excluye. El CI lo ejecuta en un job que no bloquea (`continue-on-error`) y que da por bueno el código de salida 5 (ningún test seleccionado).
- **D42.** Los tests amarillos no afirman nada. Un ayudante escribe una tabla en el resumen del CI (`$GITHUB_STEP_SUMMARY`) o la imprime en local.
- **D43.** Un guardián, activo en todos los tests, sustituye `GeminiLLM.complete` por una función que lanza `RealLLMCalledInTests`, y otro bloquea las conexiones de red. *Cambió:* bloquea todas, no todas menos `localhost`.
- **D44.** Los tests se llaman `test_<unidad>_<condición>_<resultado>`, y las tablas de casos las escribo yo antes de que la IA escriba el código.

### Decisiones tomadas al implementar


- **Captura de errores.** Starlette relanza una excepción después de su propio 500 para que el servidor la registre, y esa traza llevaría el mensaje de la excepción. Un middleware la captura, responde el 500 genérico y no la relanza.
- **Websockets cerrados.** Una conexión websocket sin clave se cierra con el código 1008 y nunca llega a la app. Hoy no hay rutas websocket.
- **Respuesta de Gemini sin texto.** Se trata como salida vacía, es decir, inválida: se reintenta y acaba en 502. Los timeouts del cliente HTTP del SDK (`httpx2`) se traducen a 504.
- **Claves fuera de `repr`.** `Settings` no muestra ninguna clave al imprimirse o registrarse.
- **Tests de planes de consulta.** Solo comprueban el nombre del índice y que no aparezca `SCAN analysis_runs`, no el plan entero: mi Mac, la imagen de Docker y el CI usan versiones distintas de SQLite.
- **Docker.** El puerto se publica solo en `127.0.0.1`, la imagen base está fijada por su digest y el usuario del contenedor es `appuser`.
- **CI.** Un job `dependency-audit` falla la pull request si alguna dependencia tiene una vulnerabilidad conocida. Lo vi ponerse en rojo con una rama desechable.

## Rúbrica de puntuación

`match_score` es un entero de 0 a 100. Es la suma de tres partes:

| Parte | Puntos | Regla |
|---|---|---|
| Skills | 0–50 | `50 × skills requeridas encontradas ÷ skills requeridas`, redondeado hacia arriba en .5 |
| Años | 0 / 10 / 20 / 30 | 0 años (o no indicados) -> 0; 1-2 -> 10; 3-7 -> 20; 8 o más -> 30 |
| Evidencia | 0 / 10 / 20 | 20 si el título completo de la oferta aparece en el CV, sin distinguir mayúsculas; 10 si aparece al menos la mitad de sus palabras de 4 letras o más; 0 en cualquier otro caso. Un título sin ninguna palabra de 4 letras o más (por ejemplo "QA") solo puede dar 20 o 0 |

El redondeo hacia arriba en .5 es a propósito: `round()` de Python redondea el .5 al número par, y `round(12.5)` da 12. Eso no se puede explicar fácil. Con esta rúbrica, 1 de 4 skills da 13 puntos y 3 de 4 dan 38.

Ejemplo con los comandos de arriba: 3 de las 5 skills de la oferta dan 30; 3 años dan 20; el título "Backend Developer" aparece completo en el CV y da 20. Total: 70.

**Por qué esta rúbrica:**

1. Las skills pesan más porque son lo único que la oferta pide de forma explícita. Usar una proporción permite comparar una oferta de 3 skills con una de 10.
2. Los años van por tramos porque la oferta no pide años. Solo miden la experiencia en general, y un tramo absorbe lo impreciso de leer años en un texto libre: "5 years" y "casi 6" no deben mover 3 puntos. Los cortes los cambié yo. El plan daba 20 puntos de 3 a 5 años y 30 de 6 en adelante. Dejé 20 de 3 a 7 y 30 de 8 en adelante, para que el simulador, el prompt y los tests usen la misma rúbrica.
3. Los años tienen un tope de 30: una carrera de 20 años no puede compensar unas skills que no encajan.
4. La evidencia es la señal más débil, y por eso pesa menos: los títulos cambian ("Python Developer" frente a "Backend Developer") y el crédito parcial evita penalizar una redacción distinta.
5. El orden de los pesos sigue qué tan confiable es cada señal: primero las skills declaradas, luego la experiencia y al final el título.
6. Es fácil de probar: cada corte de un tramo y la regla de la mitad del título son pruebas de frontera, y cada número se puede calcular a mano.

La misma rúbrica va en el mensaje de sistema que recibe Gemini, para que el modelo real dé la misma puntuación. El código no recalcula el `match_score` que devuelve el modelo: solo comprueba que sea un entero de 0 a 100.

## Auditoría

El enunciado pide poder "auditar fácilmente qué hizo la IA con cada candidato". Las dudas y las suposiciones están en el Issue [#8](https://github.com/ColoredLemur1/TalentLite/issues/8), con estas cinco preguntas y lo que se construyó:


| Pregunta | Lo que se construyó |
|---|---|
| ¿Historial de cada candidato o registro general? | Historial **por candidato**: `GET /candidates/{id}/audit` |
| ¿Qué se guarda de cada análisis? | La oferta (título y skills), el proveedor, el modelo, la versión del prompt, los intentos, el estado, el resultado o el código de error, la duración y la `reference`. Además, un `error_detail` interno |
| ¿Quién puede leerlo? | Cualquiera que tenga la clave de la API: no hay roles |
| ¿Cuánto se conserva y se puede borrar? | Se conserva sin límite y no hay endpoint para borrar. Para vaciarlo hay que borrar la base de datos (`docker compose down -v`) |
| ¿Qué pasa con los datos personales del CV? | El CV **no se copia** a la auditoría: la tabla `analysis_runs` no tiene columna para él, y `error_detail` nunca guarda la respuesta cruda del modelo. El CV vive solo en `candidates`, como pide el enunciado |

**Por qué un endpoint nuevo.** El plan base la leía a través del `GET` del candidato, sin endpoint nuevo. Pero `GET /candidates/{id}` sigue literalmente el enunciado (nombre, email y texto del CV, más el resultado), y mezclar ahí un historial paginado con datos internos de la IA lo habría desbordado. La auditoría tiene su propio endpoint, en su propia rama y su propia pull request.

**Qué muestra por intento:** `id`, `created_at`, `job_title`, `required_skills`, `status` (`succeeded` o `failed`), `result` (o `null`), `error_code` (o `null`), `provider`, `model`, `prompt_version`, `attempts`, `duration_ms` y `reference`. Va del más nuevo al más antiguo y se pagina con `limit` (1–100, por defecto 20) y `offset`.

```json
{
  "candidate_id": 1,
  "items": [
    {
      "id": 1, "created_at": "2026-11-22T00:06:20Z",
      "job_title": "Backend Developer", "required_skills": ["Python", "FastAPI", "SQL", "Docker", "Kubernetes"],
      "status": "succeeded",
      "result": {"skills": ["python", "fastapi", "sql"], "years_experience": 3.0, "summary": "3 años de experiencia; cumple 3 de 5 skills requeridas para Backend Developer.", "match_score": 70},
      "error_code": null, "provider": "mock", "model": "mock-keyword-v1", "prompt_version": "v1",
      "attempts": 1, "duration_ms": 0, "reference": "1311758622917a2a"
    }
  ],
  "total": 1, "limit": 20, "offset": 0
}
```

**Qué nunca muestra:** el `error_detail` y el texto del CV. No es un campo que se oculte: la consulta no lo lee, el modelo de respuesta no tiene ese campo y la tabla no guarda el CV. Los intentos fallidos también quedan registrados, y la `reference` de un 502 o un 504 corresponde a una fila de la auditoría.

**Qué muestra la auditoría y no el `GET`:** el proveedor, el modelo, la versión del prompt, los intentos y la duración, que `GET /candidates/{id}` no enseña.

**Qué queda fuera:** filtros por fecha o estado, exportación y un rol de auditor con permisos propios (necesita una clave por cliente). Está en el Issue [#16](https://github.com/ColoredLemur1/TalentLite/issues/16).

## Rendimiento

Hay cuatro tests amarillos. Miden y no afirman nada; sus tablas salen en el resumen de cada ejecución del CI. Las cifras son de mi Mac, con peticiones sueltas y medianas de pocas repeticiones, así que sirven para comparar, no como valores absolutos.

- **Y1, crear un candidato con un CV de 19.999 caracteres** (50 peticiones): mediana de 1,38 ms y p95 de 2,38 ms.
- **Y2, buscar un email entre muchos candidatos:** tarda lo mismo con 10 que con 10.000 candidatos. El plan de consulta usa el índice que crea `UNIQUE` (`sqlite_autoindex_candidates_1`). No anoté los milisegundos.
- **Y3, coste de los reintentos** (modelo falso de 50 ms por llamada): acertar a la primera cuesta 55 ms y 2.549 caracteres de prompt; al tercer intento, 158 ms y 7.647. El coste crece con cada intento y el tope de 3 lo limita. El segundo intento no quedó anotado.
- **Y4, candidato con muchos análisis, antes y después del índice** `idx_analysis_runs_candidate` sobre `analysis_runs(candidate_id, created_at DESC, id DESC)`, con 5 candidatos más y la mediana de 5 peticiones. Con 10.000 análisis:

| Petición | Antes | Después |
|---|---|---|
| `GET /candidates/{id}` | 4,19 ms | 1,48 ms |
| Auditoría, primera página | 8,18 ms | 2,34 ms |
| Auditoría, última página | 15,69 ms | 1,55 ms |

Con 1.000 análisis solo anoté la última página: pasa de 1,95 ms a 1,11 ms.

El plan pasó de `SCAN analysis_runs / USE TEMP B-TREE FOR ORDER BY` a `SEARCH analysis_runs USING INDEX idx_analysis_runs_candidate`. Sin índice, SQLite leía y ordenaba toda la tabla; con él lee solo las filas del candidato, ya ordenadas. La mejora grande está en la última página de los 10.000, que pasa de 15,69 ms a 1,55 ms.

## Límites conocidos

**Acceso y datos**
- Una sola clave compartida: no identifica a cada persona, y no hay rotación automática.
- `/docs`, `/docs/oauth2-redirect`, `/redoc` y `/openapi.json` no piden clave, a propósito.
- Una clave hecha solo de espacios se acepta si llega a 32 caracteres: D7 no pide recortar.
- No hay límite de peticiones. Nada limita cuántas veces se puede llamar a `POST /candidates/{id}/analyze`: cada petición válida de un candidato que existe llama al modelo, hasta 3 veces si la salida es inválida.
- `error_detail` sigue guardado en la base de datos: la API no puede mostrarlo, pero quien abra el archivo sí.
- El `msg` de un 422 puede citar el carácter inválido, pero nunca el valor completo enviado.
- Si la excepción salta cuando la respuesta ya empezó, el cliente ve la respuesta cortada, y el log sigue teniendo solo el tipo de la excepción y la referencia.

**Capa de IA**
- Una puntuación válida pero equivocada se acepta, se guarda y se muestra. Si un modelo real se deja convencer por un CV malicioso y responde un 100, la validación no lo detecta. Contrastar las skills con el CV queda en el Issue [#9](https://github.com/ColoredLemur1/TalentLite/issues/9).
- Los marcadores y la regla de datos hacen más difícil la inyección, pero no obligan al modelo. La validación rechaza un JSON mal formado, no comprueba que la suma de la rúbrica sea la del `match_score`.
- Gemini solo se probó una vez a mano, con un CV inventado: dio 90, igual que el simulador. No prueba el resto de tramos, ni se provocó un timeout real.
- El simulador puntúa por palabras clave: un CV que enumera todas las skills recibe los 50 puntos de skills. Los años se leen solo de patrones como `N years`, `N+ years` o `N años`, y el título no reconoce sinónimos ("Backend" frente a "Server-side").
- `years_experience` es 0 cuando el CV no dice nada: 0 significa "no indicado".
- `casefold()` trata `ß` y `ss` como la misma skill. Con los nombres normales equivale a pasar a minúsculas.

**Infraestructura**
- SQLite funciona con un solo proceso: no sirve para varias réplicas.
- No hay migraciones: si cambia una tabla, se borra el archivo de la base de datos.
- `docker compose down -v` borra el volumen y los datos con él.
- Con `restart: unless-stopped`, una clave mala reinicia el contenedor sin detenerse hasta que se hace `docker compose down`.
- `env_file: .env` mete todo el archivo en el contenedor en marcha, también una clave de Gemini si estuviera. No queda en la imagen.
- El CI no construye la imagen: la probé solo en mi Mac.
- Tres versiones de parche de Python: 3.13.2 en mi Mac, 3.13.18 en la imagen y la última 3.13 en el CI. Son la misma versión menor, y su comportamiento debería coincidir.
- Tres versiones de SQLite: la de mi Mac, la de la imagen (Debian) y la del CI. Por eso los tests de planes de consulta no comparan el texto completo.
- Solo están fijadas las dependencias directas. Las indirectas (Starlette, `pydantic-core`, `httpx2` y otras) las resuelve pip al instalar, y `pip-audit` revisa el conjunto ya resuelto. Si un aviso cae en una indirecta, arreglarlo obliga a añadir una fijación.
- La imagen base está fijada por digest (`python:3.13-slim@sha256:…`): la etiqueta sola se mueve, y el digest garantiza que lo que se probó es lo que se construye. Para actualizarla se cambia el digest a propósito y se explica el motivo en la pull request.
- `pip-audit` solo avisa de vulnerabilidades ya publicadas.
- El 80 % de cobertura queda lejos del 97 % actual: una bajada pequeña no hace fallar el CI.

## Seguridad

Los riesgos que vi, lo que hice con cada uno y lo que queda sin resolver.

| Riesgo | Qué se hace | Límite conocido |
|---|---|---|
| Entradas inválidas o enormes | Validación estricta con Pydantic y límites de tamaño (ver D12), incluido un tope de 256 KiB para todo el cuerpo en el servidor, que responde 413 (nueva) | El tope de 256 KiB es fijo; cambiarlo exige tocar el código |
| Acceso sin permiso | Clave en la cabecera `X-API-Key` en todas las rutas, salvo cuatro de documentación, comparada con `secrets.compare_digest` y con un 401 genérico, idéntico con la clave ausente o incorrecta | Una sola clave compartida, que no identifica a cada persona |
| Clave filtrada | Solo vive en `.env` (ignorado por Git), nunca en logs ni respuestas, y `Settings` no la muestra al imprimirse. Si se filtra, se cambia por otra: borrarla no basta | Sin rotación automática |
| Inyección SQL | Consultas parametrizadas: ningún texto SQL se construye con datos del usuario | Ninguno que importe |
| Instrucciones maliciosas dentro del CV (inyección de prompt) | Las instrucciones van aparte de los datos; el CV va solo dentro de un bloque con un nonce aleatorio por petición; y la salida se valida | Se reduce, no se elimina: una puntuación inventada pero válida (por ejemplo, 100) pasa el esquema. Contrastar las skills con el CV queda en el Issue [#9](https://github.com/ColoredLemur1/TalentLite/issues/9) |
| Respuesta extraña del modelo | La salida es entrada no fiable: esquema estricto, hasta 3 intentos y un error claro | El resultado puede ser válido pero equivocado |
| Datos personales en los logs | Los logs van a la consola y no llevan cuerpos, CVs, prompts, claves ni el mensaje de una excepción: solo el tipo y una referencia. Los tests lo comprueban para crear candidatos, analizar, autenticar y errores 500 | Solo están cubiertos esos caminos. Los logs de acceso de uvicorn incluyen las rutas, con ids de candidato |
| Errores que revelan detalles | El 422 no devuelve el valor enviado, y los 502 y 504 son genéricos con una `reference`. El detalle del error se queda en la base de datos y la auditoría no lo muestra | La auditoría sí muestra a quien tenga la clave el proveedor, el modelo, la versión del prompt y los intentos. El `msg` de un 422 puede citar un carácter |
| Abuso y coste | El simulador es el valor por defecto, no hay llamadas reales en los tests ni en el CI, y cada análisis hace como mucho 3 llamadas al modelo | No hay límite de peticiones: con Gemini real, un uso intenso costaría dinero |
| Datos de personas reales | Solo CVs inventados en el repositorio, en los tests y en Gemini | El plan gratuito de Gemini usa el contenido para mejorar los productos de Google |
| Dependencias con fallos conocidos | `pip-audit` en el CI, que falla la pull request. Lo comprobé con una rama desechable con una versión vulnerable | Solo detecta fallos ya publicados; las dependencias indirectas no están fijadas |
| Contenedor | Usuario sin privilegios (`appuser`), secretos por variables de entorno y no dentro de la imagen, `.env` fuera del contexto de construcción, imagen base fijada por digest y puerto publicado solo en `127.0.0.1` (nueva) | SQLite implica un solo proceso |
| Cabeceras de seguridad (nueva) | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` y `Cache-Control: no-store` en todas las respuestas, también en los errores | Sin política de seguridad de contenido (CSP): rompería `/docs` |
| Documentación abierta (nueva) | `/docs`, `/redoc` y `/openapi.json` se abren sin clave; las rutas de la API la siguen pidiendo | Cualquiera que llegue al puerto ve el contrato de la API |
| Errores inesperados (nueva) | Un middleware captura cualquier excepción, devuelve un 500 genérico con una referencia y no la relanza: así su mensaje no acaba en la traza del servidor | Si salta con la respuesta ya empezada, el cliente la ve cortada |

**Reglas de trabajo para evitar filtraciones.** Antes del primer commit, `git config user.name` y `user.email` usan la dirección `noreply` de GitHub, con "Keep my email addresses private" activado. Las claves reales nunca van al repositorio, a un Issue, a una pull request ni a un prompt. Los agentes de IA no leen `.env` (está en `AGENTS.md`). Si una clave se subiera por error, se cambia en ese mismo momento y después se limpia el historial.

## Despliegue

Esta parte es opcional y explica cómo iría a producción, sin hacerlo:

- Cambiar SQLite por un PostgreSQL gestionado, para tener varias réplicas y copias de seguridad.
- Ejecutar el contenedor en un servicio de contenedores gestionado.
- Guardar las claves en un gestor de secretos, no en archivos `.env`.
- Poner HTTPS por delante y limitar las peticiones por clave.
- Usar un plan de pago de Gemini si se procesan CVs reales, por las condiciones de uso de los datos.
- Añadir logs centralizados y monitorización.

Para un servicio nuevo en producción usaría Python 3.14: la rama 3.13 solo recibe parches de seguridad desde octubre de 2026 (hasta 2029). Me quedé en 3.13 porque era la versión instalada y probada con todas las dependencias.

## Qué queda fuera

Las mejoras que no caben en el tiempo, ordenadas por impacto. Cada una es un Issue.

Se me olvidó abrirlas mientras hacía las ramas. Las creé al final, con el código ya integrado a `main`. Hasta entonces esta lista ponía `#PENDIENTE`, y ninguna pull request pudo cerrarlas. La excepción es el contraste de skills: el Issue [#9](https://github.com/ColoredLemur1/TalentLite/issues/9) ya estaba abierto.

1. Límite de peticiones por clave o IP ([#14](https://github.com/ColoredLemur1/TalentLite/issues/14)). Es el principal riesgo de abuso y de coste cuando se active Gemini de verdad.
2. Contrastar las skills con el CV ([#9](https://github.com/ColoredLemur1/TalentLite/issues/9)): rechazar las skills que no aparecen en el CV y recalcular la puntuación. Reduce el límite de la "puntuación válida pero equivocada".
3. Una clave de API por cliente ([#15](https://github.com/ColoredLemur1/TalentLite/issues/15)), para saber quién hizo qué y poder rotarlas.
4. Más para la auditoría ([#16](https://github.com/ColoredLemur1/TalentLite/issues/16)): filtros por fecha o estado, exportación (CSV o JSON) y un rol de auditor con permisos propios.
5. Proteger `main` en GitHub ([#17](https://github.com/ColoredLemur1/TalentLite/issues/17)): exigir CI en verde antes de integrar el cambio a `main`.
6. Evitar repetir un análisis idéntico ([#18](https://github.com/ColoredLemur1/TalentLite/issues/18)): mismo candidato, misma oferta y misma `prompt_version` reutilizan el resultado.
7. Registro de las peticiones rechazadas, sin el cuerpo ([#19](https://github.com/ColoredLemur1/TalentLite/issues/19)). Falta decidir qué hacer con la IP: completa, truncada o con hash.
8. IDs con UUID ([#20](https://github.com/ColoredLemur1/TalentLite/issues/20)), para que no se puedan enumerar.
9. Apagar `/docs` con una variable de entorno ([#21](https://github.com/ColoredLemur1/TalentLite/issues/21)).
10. Un segundo proveedor real ([#22](https://github.com/ColoredLemur1/TalentLite/issues/22)), como Groq u OpenRouter.
11. Un healthcheck en `docker-compose.yml` ([#23](https://github.com/ColoredLemur1/TalentLite/issues/23)), con `/health` y la clave.
12. Construir la imagen de Docker en el CI ([#24](https://github.com/ColoredLemur1/TalentLite/issues/24)).
13. Una política de seguridad de contenido (CSP) ([#25](https://github.com/ColoredLemur1/TalentLite/issues/25)) que no rompa `/docs`.
14. Listado de candidatos con paginación ([#26](https://github.com/ColoredLemur1/TalentLite/issues/26)).
15. Datos de prueba aleatorios generados ([#27](https://github.com/ColoredLemur1/TalentLite/issues/27)), con tests basados en propiedades.

## Registro de IA

El uso de IA en este proyecto, entrada a entrada y pull request a pull request, está en [`AI_LOG.md`](AI_LOG.md). Las reglas para los agentes están en [`AGENTS.md`](AGENTS.md).
