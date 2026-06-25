from __future__ import annotations

from src.config.constants import FREE_MODELS, MODEL_PROVIDERS
from src.shared.exceptions import ProviderUnavailableError


class ModelService:
    def get_available_models(self, is_premium: bool) -> list[str]:
        if is_premium:
            return list(MODEL_PROVIDERS.keys())
        return list(FREE_MODELS)

    def is_premium_model(self, model_name: str) -> bool:
        return model_name not in FREE_MODELS

    def validate_access(self, model_name: str, is_premium: bool) -> bool:
        if model_name not in MODEL_PROVIDERS:
            return False
        return is_premium or not self.is_premium_model(model_name)

    def get_provider_name(self, model_name: str) -> str:
        provider = MODEL_PROVIDERS.get(model_name)
        if provider is None:
            raise ProviderUnavailableError(f"Unknown model: {model_name}")
        return provider
