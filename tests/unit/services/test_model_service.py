from __future__ import annotations

import pytest

from src.config.constants import FREE_MODELS
from src.config.settings import settings
from src.services.model import ModelService
from src.shared.exceptions import ProviderUnavailableError


def make_service() -> ModelService:
    return ModelService()


class TestGetAvailableModels:
    def test_free_user_gets_only_free_models(self) -> None:
        svc = make_service()
        models = svc.get_available_models(is_premium=False)
        assert set(models) == set(FREE_MODELS)

    def test_premium_user_gets_all_models(self) -> None:
        svc = make_service()
        free = svc.get_available_models(is_premium=False)
        premium = svc.get_available_models(is_premium=True)
        assert len(premium) >= len(free)
        for m in free:
            assert m in premium


class TestIsPremiumModel:
    def test_free_models_are_not_premium(self) -> None:
        svc = make_service()
        for model in FREE_MODELS:
            assert svc.is_premium_model(model) is False

    def test_unknown_model_is_considered_premium(self) -> None:
        svc = make_service()
        assert svc.is_premium_model("gpt-9000-ultra") is True


class TestValidateAccess:
    def test_free_model_accessible_without_premium(self) -> None:
        svc = make_service()
        assert svc.validate_access("gpt-4o-mini", is_premium=False) is True

    def test_free_model_accessible_with_premium(self) -> None:
        svc = make_service()
        assert svc.validate_access("gpt-4o-mini", is_premium=True) is True

    def test_unknown_model_rejected(self) -> None:
        svc = make_service()
        assert svc.validate_access("not-a-real-model", is_premium=True) is False


class TestGetProviderName:
    def test_gpt_model_maps_to_openai(self) -> None:
        svc = make_service()
        assert svc.get_provider_name("gpt-4o-mini") == "openai"

    def test_gemini_model_maps_to_gemini(self) -> None:
        svc = make_service()
        assert svc.get_provider_name(settings.gemini_model) == "gemini"

    def test_unknown_model_raises(self) -> None:
        svc = make_service()
        with pytest.raises(ProviderUnavailableError):
            svc.get_provider_name("nonexistent-model")
