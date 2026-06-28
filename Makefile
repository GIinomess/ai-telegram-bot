.PHONY: build test

build:
	docker compose build bot

test: build
	docker compose run --rm --entrypoint sh bot -c "uv sync --dev --frozen && uv run pytest"
