from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_assistant"

    def ready(self):
        """
        Import signals when the app is ready.
        This enables automatic RAG updates when content is modified.
        """
        try:
            import ai_assistant.signals  # noqa: F401
        except ImportError:
            pass
