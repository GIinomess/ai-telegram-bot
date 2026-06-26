from __future__ import annotations

from src.services.prompt import PromptService
from tests.conftest import make_message, make_settings


def make_service() -> PromptService:
    return PromptService()


class TestBuildSystemPrompt:
    def test_english_no_language_instruction(self) -> None:
        svc = make_service()
        settings = make_settings(language="en")
        prompt = svc.build_system_prompt(settings)
        assert "language" not in prompt.lower()

    def test_non_english_includes_language_instruction(self) -> None:
        svc = make_service()
        settings = make_settings(language="ru")
        prompt = svc.build_system_prompt(settings)
        assert "ru" in prompt

    def test_balanced_style(self) -> None:
        svc = make_service()
        settings = make_settings()
        settings.conversation_style = "balanced"
        prompt = svc.build_system_prompt(settings)
        assert "helpful" in prompt.lower() or "balanced" in prompt.lower()

    def test_creative_style(self) -> None:
        svc = make_service()
        settings = make_settings()
        settings.conversation_style = "creative"
        prompt = svc.build_system_prompt(settings)
        assert "creative" in prompt.lower()

    def test_precise_style(self) -> None:
        svc = make_service()
        settings = make_settings()
        settings.conversation_style = "precise"
        prompt = svc.build_system_prompt(settings)
        assert "precise" in prompt.lower()

    def test_unknown_style_falls_back_to_balanced(self) -> None:
        svc = make_service()
        settings = make_settings()
        settings.conversation_style = "unknown_style"
        prompt = svc.build_system_prompt(settings)
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestBuildMessages:
    def test_always_starts_with_system_message(self) -> None:
        svc = make_service()
        messages = svc.build_messages("Be helpful.", [], "Hello")
        assert messages[0] == {"role": "system", "content": "Be helpful."}

    def test_user_message_is_last(self) -> None:
        svc = make_service()
        messages = svc.build_messages("", [], "My question")
        assert messages[-1] == {"role": "user", "content": "My question"}

    def test_history_inserted_between_system_and_user(self) -> None:
        svc = make_service()
        history = [
            make_message(role="user", content="First"),
            make_message(role="assistant", content="Second"),
        ]
        messages = svc.build_messages("sys", history, "New")
        assert messages[0]["role"] == "system"
        assert messages[1] == {"role": "user", "content": "First"}
        assert messages[2] == {"role": "assistant", "content": "Second"}
        assert messages[3] == {"role": "user", "content": "New"}

    def test_empty_history(self) -> None:
        svc = make_service()
        messages = svc.build_messages("sys", [], "hi")
        assert len(messages) == 2
