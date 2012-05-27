from django import forms
from django.utils.safestring import mark_safe
from django.conf import settings
    
class ReCaptcha(forms.widgets.Widget):
        recaptcha_challenge_name = 'recaptcha_challenge_field'
        recaptcha_response_name = 'recaptcha_response_field'
    
        def render(self, name, value, attrs=None):
            try:
                from recaptcha.client import captcha
            except ImportError:
                return ''
            if not settings.RECAPTCHA_PUBLIC_KEY:
                return ''
            html = """
            <div id="%(name)s_widget"></div>
            <script type="text/javascript" src="http://www.google.com/recaptcha/api/js/recaptcha_ajax.js"></script>
            <script>
                Recaptcha.create("%(key)s", "%(name)s_widget", {theme:"red"});
            </script>
            """ % {'key': settings.RECAPTCHA_PUBLIC_KEY, 'name': name}
            return mark_safe(html)
    
        def value_from_datadict(self, data, files, name):
            return [data.get(self.recaptcha_challenge_name, None), 
                data.get(self.recaptcha_response_name, None)]

