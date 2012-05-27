from django.conf import settings
EXCLUDED_APPS = set()
def to_test(name):
    if name in EXCLUDED_APPS or not name.startswith('film20'):
        return False
    try:
        __import__(name + '.tests')
	return True
    except ImportError, e:
        import traceback
        traceback.print_exc()

print ' '.join(sorted(app.split('.',1)[1] for app in settings.INSTALLED_APPS if to_test(app)))


