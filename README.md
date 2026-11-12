MCQ Agent — Multi-agent Quiz Tutor (FastAPI + LangGraph)

FastAPI backend that exposes a chat-style endpoint and routes the request through a LangGraph/LangChain agent that can:

1. **Classify** if the user is asking for a quiz (and whether the request is complete).
2. **Generate** an MCQ quiz via `quiz_generator_tool`.
3. **Review** the user’s answers via `quiz_reviewer_tool`.

The app persists:

* **Users + sessions (threads)** in Postgres (`users`, `users_thread`).
* **Errors** in Postgres (`err_logs`).
* **Agent checkpoints** (LangGraph checkpointer) in Postgres.

> Repo/module name in `pyproject.toml` is `multi-agent`.

## What runs where

* **API server**: `mcp_client/main.py` (FastAPI + Uvicorn)
* **HTTP router**: `mcp_client/src/routers/router.py`
* **Business logic**: `mcp_client/src/services/tutor_service.py`
* **Orchestrator agent**: `mcp_client/src/services/orchestration_service.py`
* **Tools**: `mcp_client/src/tools/tool.py`
* **Database + tables**: `mcp_client/src/repositories/**` and `mcp_client/src/migrations/create_tables.py`
* **Middleware (dynamic tool selection)**: `mcp_client/src/middlewares/agent_middleware.py`
* **Prompts**: `mcp_client/src/prompts/*.py`



### Terminal-style flow diagram (no Mermaid)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 /api/chat                                   │
└─────────────────────────────────────────────────────────────────────────────┘
		     │
		     ▼
┌─────────────────────────┐
│ FastAPI app              │
│ mcp_client/main.py       │
└─────────────────────────┘
		     │
		     ▼
┌─────────────────────────┐
│ Router                   │
│ src/routers/router.py    │
└─────────────────────────┘
		     │
		     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TutorService.tutor_service                                                   │
│ src/services/tutor_service.py                                                │
│  - check_user(user_id)         -> Postgres.users                             │
│  - check_thread(user_id, sid)  -> Postgres.users_thread                      │
│  - if missing thread: add_user_thread() -> Postgres.users_thread             │
└─────────────────────────────────────────────────────────────────────────────┘
		     │
		     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ OrchestratorService.run_agent                                                │
│ src/services/orchestration_service.py                                        │
└─────────────────────────────────────────────────────────────────────────────┘
		     │
		     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1) Intent classification (LLM)                                               │
│    CLASSIFIER_PROMPT  -> returns JSON: {"context":"reject|incomplete|valid"} │
└─────────────────────────────────────────────────────────────────────────────┘
		     │
	┌──────────┼───────────────────────────────┐
	│          │                               │
	▼          ▼                               ▼
┌───────────┐  ┌────────────────┐      ┌──────────────────────────────────────┐
│ reject     │  │ incomplete      │      │ valid                                │
│ (off-topic)│  │ (topic missing) │      │ (topic present)                       │
└───────────┘  └────────────────┘      └──────────────────────────────────────┘
	│                 │                           │
	│                 │                           ▼
	│                 │            ┌────────────────────────────────────────┐
	│                 │            │ Agent runtime (LangGraph + LangChain)   │
	│                 │            │ - create_agent(...)                     │
	│                 │            │ - apply_step_config middleware           │
	│                 │            │ - AsyncPostgresSaver checkpoints -> DB   │
	│                 │            └────────────────────────────────────────┘
	│                 │                           │
	│                 │                           ▼
	│                 │            ┌────────────────────────────────────────┐
	│                 │            │ Tool #1: quiz_generator_tool             │
	│                 │            │ - QUIZ_AGENT_PROMPT                      │
	│                 │            │ - outputs: generated_questions + answer_key│
	│                 │            │ - sets current_state = "review_tool"      │
	│                 │            └────────────────────────────────────────┘
	│                 │                           │
	│                 │                           ▼
	│                 │            ┌────────────────────────────────────────┐
	│                 │            │ HITL: Human-in-the-loop                  │
	│                 │            │ - HumanInTheLoopMiddleware interrupt     │
	│                 │            │ - current code collects answers via input()│
	│                 │            └────────────────────────────────────────┘
	│                 │                           │
	│                 │                           ▼
	│                 │            ┌────────────────────────────────────────┐
	│                 │            │ Tool #2: quiz_reviewer_tool(user_answer) │
	│                 │            │ - REVIEW_AGENT_PROMPT                    │
	│                 │            │ - returns structured QuizToolResponse    │
	│                 │            │ - updates review_result                  │
	│                 │            └────────────────────────────────────────┘
	│                 │                           │
	└──────────────┬──┴───────────────┬───────────┘
			   │                  │
			   ▼                  ▼
	  ┌──────────────────────┐  ┌──────────────────────────────────────────┐
	  │ Reply (no tools)     │  │ Reply with results                         │
	  │ OffContextResponse   │  │ APIResponse.data = review_result / structured│
	  └──────────────────────┘  └──────────────────────────────────────────┘
```


## Key domain concepts

* **User**: a row in `users` (`src/repositories/schemas/user_schema.py`).
* **Thread / session**: a row in `users_thread`. Used as LangGraph `thread_id` so the agent can checkpoint/resume.
* **Agent state**: `CommonState` in `src/models/user_model.py`.
	* `current_state` is used by middleware to decide which tool is allowed.
* **Tools**:
	* `quiz_generator_tool(user_query, runtime)` → generates questions + answer key.
	* `quiz_reviewer_tool(user_answer, runtime)` → returns `QuizToolResponse`.

## Configuration

Loaded from environment via `mcp_client/settings.py` (uses `python-dotenv`).

Required / important env vars:

* `REGION`
* `AWS_ACCESS_KEY_ID`
* `AWS_SECRET_ACCESS_KEY`
* `MODEL_ID` (Bedrock model id)
* `PROVIDER` (defaults to `amazon`)
* `DB_NAME`, `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`

Optional (present in settings, may be unused in current flow):

* `DUCKDUCKGO_MCP_SERVER_URL`
* `PEP8_MCP_SERVER_URL`

## Run locally

### 1) Install

This repo uses a `pyproject.toml`. Install with whichever tool you prefer (uv/pip/poetry). The runtime requires Python **3.11+**.

### 2) Start Postgres

You need a running Postgres and to set the DB env vars to match.

On startup, the app will:

* create tables (`create_tables()`), and
* seed a few users (only if the `users` table is empty).

### 3) Start the API

From the `mcp_client/` directory, the module entry is `main:app`:

```bash
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

### 4) Call the API

Endpoint: `POST /api/chat`

Body schema (`RequestModel`):

```json
{
	"user_id": "<uuid>",
	"user_query": "Generate a 5 question medium quiz on World War II",
	"session_id": "<optional uuid>"
}
```

Other endpoint: `GET /api/users/{user_id}`.

## Notes about Human-in-the-loop (HITL)

`OrchestratorService.run_agent()` is configured with `HumanInTheLoopMiddleware`, and the current implementation also uses `input()` to capture answers when an interrupt happens.

That means:

* In a real HTTP server scenario, `input()` will block the worker process.
* If you want HITL over HTTP, you typically split it into:
	* **start** request → returns quiz + checkpoint id / thread id
	* **resume** request → posts answers and resumes from checkpoint

If you want, I can refactor the flow to be fully HTTP-friendly (no blocking stdin) while keeping the checkpointing.

## Test

Tests are configured under `mcp_client/tests/` via `mcp_client/pytest.ini`.

Run from the `mcp_client/` directory:

```bash
pytest
```

### What’s covered

The current test suite focuses on **service/repository/router units** using mocks (no real DB/LLM calls):

* `mcp_client/tests/repositories/test_repository.py`
	* `UserRepository.check_user()` happy path + DB error path
* `mcp_client/tests/services/test_service.py`
	* `TutorService.get_user()` success, 404 (not found), and 500 (unexpected exception)
* `mcp_client/tests/routers/test_router.py`
	* `GET /api/users/{user_id}` uses dependency overrides to inject mocked `TutorService` + `ErrorRepository`

### Markers and defaults

`mcp_client/pytest.ini` defines:

* `asyncio_mode = auto`
* `testpaths = tests`
* default opts: `-v -s --cov=src --cov-report=term-missing`
* markers:
	* `unit`
	* `integration`

### Useful pytest commands

Run only unit tests:

```bash
pytest -m unit
```

Run a single file:

```bash
pytest tests/services/test_service.py
```

Run a single test:

```bash
pytest tests/services/test_service.py -k test_get_user_success
```

Run with a different coverage report (HTML):

```bash
pytest --cov=src --cov-report=html
```

## Folder structure

```text
mcp_client/
	main.py                # FastAPI app + lifespan (DB init + migrations)
	settings.py            # env → Settings dataclass
	src/
		routers/             # API routes
		services/            # TutorService, OrchestratorService
		middlewares/         # LangChain agent middleware (dynamic tools)
		tools/               # quiz_generator_tool, quiz_reviewer_tool
		prompts/             # PROMPT strings
		repositories/        # DB session, repositories
		repositories/schemas # SQLAlchemy models
		migrations/          # create_tables + seed
		models/              # Pydantic request/response + agent state
		utils/               # logger + CustomAppException
	tests/                 # pytest tests
```

## Troubleshooting

* **`Failed to initialise LLM client`**: check `REGION`, `MODEL_ID`, AWS credentials.
* **DB connection errors**: verify the DB env vars and that Postgres is reachable.
* **`input()` hangs server**: see HITL section above.
