from __future__ import annotations

from src.services.localization import LocalizationService


def make_service() -> LocalizationService:
    return LocalizationService()


class TestGet:
    def test_known_key_english(self) -> None:
        svc = make_service()
        result = svc.get("common.back", "en")
        assert isinstance(result, str)
        assert len(result) > 0
        assert result != "common.back"

    def test_known_key_russian(self) -> None:
        svc = make_service()
        ru = svc.get("common.back", "ru")
        assert isinstance(ru, str)
        assert len(ru) > 0

    def test_missing_key_returns_key_itself(self) -> None:
        svc = make_service()
        key = "nonexistent.key.that.does.not.exist"
        result = svc.get(key, "en")
        assert result == key

    def test_unsupported_language_falls_back_to_english(self) -> None:
        svc = make_service()
        en_result = svc.get("common.back", "en")
        xx_result = svc.get("common.back", "xx")
        assert xx_result == en_result

    def test_template_variable_substitution(self) -> None:
        svc = make_service()
        result = svc.get("chat.limit_reached", "en", limit=40)
        assert "40" in result

    def test_template_missing_variable_returns_unformatted(self) -> None:
        svc = make_service()
        # Pass no kwargs for a key that needs {limit}; should not raise
        result = svc.get("chat.limit_reached", "en")
        assert isinstance(result, str)

    def test_premium_plan_monthly_with_price(self) -> None:
        svc = make_service()
        result = svc.get("premium.plan_monthly", "en", price=200)
        assert "200" in result

    def test_all_supported_languages_load(self) -> None:
        svc = make_service()
        langs = svc.get_supported_languages()
        assert "en" in langs
        for lang in langs:
            result = svc.get("common.back", lang)
            assert isinstance(result, str)
            assert len(result) > 0
