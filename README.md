# AI Telegram Bot

A production-ready AI assistant Telegram bot with multi-model support, streaming responses, context memory, and Telegram Stars subscriptions.

## Features

- Multi-model AI: GPT-4o mini and Gemini 1.5 Flash (free), extensible to premium models
- Streaming responses with real-time message editing
- Per-chat context memory with automatic summarization
- Multiple chats with history, rename, archive, delete
- Telegram Stars payment for Premium subscription (unlimited messages)
- Daily free message limit (configurable)
- Multi-language UI: English, Russian, Ukrainian, Czech
- User settings: model, language, style, creativity, context toggle

## Requirements

- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker + Docker Compose (for deployment)

## Quick Start

### 1. Clone and install

```bash
git clone <repo-url>
cd ai-telegram-bot
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your tokens and API keys
```

Required variables:

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `CHANNEL_ID` | Telegram channel for subscription check (`@username` or numeric ID) |
| `DATABASE_URL` | PostgreSQL async URL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis URL (`redis://...`) |
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Google Gemini API key |

Optional variables (with defaults):

| Variable | Default | Description |
|---|---|---|
| `FREE_DAILY_LIMIT` | `40` | Free messages per user per day |
| `PREMIUM_MONTHLY_STARS` | `200` | Monthly plan price in Telegram Stars |
| `PREMIUM_QUARTERLY_STARS` | `500` | Quarterly plan price |
| `PREMIUM_YEARLY_STARS` | `1800` | Yearly plan price |
| `LOG_JSON` | `false` | Set to `true` for JSON log output (production) |

### 3. Run database migrations

```bash
uv run alembic upgrade head
```

### 4. Start the bot

```bash
uv run python -m src.main
```

## Docker Deployment

```bash
cp .env.example .env
# Fill in .env

docker compose up -d
```

The bot container automatically runs `alembic upgrade head` before starting.

To view logs:
```bash
docker compose logs -f bot
```

## Development

### Run tests

```bash
uv run pytest
```

### Lint and format

```bash
uv run ruff check src/ tests/
uv run black src/ tests/
```

### Type check

```bash
uv run mypy src/
```

### Generate a new migration

After changing models, generate a migration:
```bash
uv run alembic revision --autogenerate -m "describe the change"
```

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Start the bot, select language |
| `/new` | Create a new chat |
| `/history` | View chat history |
| `/settings` | Adjust preferences |
| `/premium` | View and purchase Premium |

## Architecture

```
src/
├── bot/            # Telegram layer (handlers, routers, middlewares)
├── config/         # Settings and constants
├── core/           # Startup: logging, Redis
├── database/       # Models, repositories, migrations
├── features/       # Business features (chats, users, settings, subscriptions)
├── providers/      # AI provider clients (OpenAI, Gemini)
├── services/       # Shared services (AI, context, prompt, localization)
└── shared/         # Exceptions, helpers, types
```

Dependency flow: `Handler → Service → Repository → Database`

- Business logic lives only in services
- Database access only in repositories
- AI access only through providers
- Handlers never touch the database or AI directly

## Project Structure

```
ai-telegram-bot/
├── src/
│   ├── bot/
│   │   ├── middlewares/    # Error, Logging, Localization, DI
│   │   └── routers/        # Route registration
│   ├── features/
│   │   ├── chats/          # Chat management + AI conversation
│   │   ├── settings/       # User settings
│   │   ├── subscriptions/  # Premium + Telegram Stars payments
│   │   └── users/          # Registration + language selection
│   ├── providers/
│   │   ├── openai.py       # OpenAI streaming
│   │   └── gemini.py       # Gemini streaming
│   └── services/
│       ├── ai.py           # Orchestrates generation + context + limits
│       ├── context.py      # Chat context and summarization
│       └── prompt.py       # System prompt and message building
├── tests/
│   └── unit/services/      # 64 unit tests, no DB required
├── scripts/
│   └── entrypoint.sh       # Migrate then start (used in Docker)
├── Dockerfile
├── docker-compose.yml
└── .env.example
```
