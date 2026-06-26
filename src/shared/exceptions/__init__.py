class AppError(Exception):
    pass


class DailyLimitExceededError(AppError):
    pass


class PremiumRequiredError(AppError):
    pass


class ProviderUnavailableError(AppError):
    pass


class GeminiQuotaError(ProviderUnavailableError):
    pass


class ChatNotFoundError(AppError):
    pass


class UserNotFoundError(AppError):
    pass
