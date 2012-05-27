def load_i18n_urls(globals, key="urlpatterns"):
    from django.conf import settings
    lc = getattr(settings, "I18N_URLS", False) and settings.LANGUAGE_CODE or "en"
    try:
        module = __import__(lc, globals, {}, key, 1)
    except ImportError:
        # en fallback
        module = __import__("en", globals, {}, key, 1)
    return getattr(module, key)
