import warnings
warnings.simplefilter('ignore')

from urllib2 import urlopen
import subprocess
from django.conf import settings

class Test(object):
    order = 0
    @classmethod
    def do_tests(cls):
        tests = []
        for name, obj in globals().copy().items():
            if isinstance(obj, type) and issubclass(obj, Test) and obj!=Test:
                test = obj()
                try:
	            if test.is_enabled():
        	        test.test()
                	tests.append(test)
		except:
		    pass
        
        any_failed = any(not t.result for t in tests)

        if any_failed:
            print
            for t in sorted(tests, key=lambda t:t.order):
                print unicode(t)
	    print
            import os
            os.system("uptime")

        return any_failed
                    
    def test(self):
        try:
            self.result = self.do_test()
        except Exception, e:
            self.result = False

    def is_enabled(self):
        return True
    
    def __unicode__(self):
        return u"%-10s: %s" % (self.__class__.__name__, self.result and "OK" or "FAILED")

class WWW(Test):
    order = 1
    def do_test(self):
        response = urlopen(settings.FULL_DOMAIN + '/ping/?a=1')
        return response.getcode()==200 and response.read()=='pong'

class RabbitMQ(Test):
    order = 2
    def is_enabled(self):
        return subprocess.call(['rabbitmqctl'], stdout=subprocess.PIPE) == 0
    
    def do_test(self):
        return subprocess.call(['rabbitmqctl', 'status'], stdout=subprocess.PIPE) == 0

class Celery(Test):
    order = 3

    def is_enabled(self):
        from celery.task.control import ping as celery_ping
        return True
    
    def do_test(self):
        from celery.task.control import ping as celery_ping
        return bool(celery_ping())

class Cache(Test):
    order = 4
    def is_enabled(self):
        return True
    
    def do_test(self):
        from django.core.cache import cache
        cache.set('filmaster_status_cache_test', 'ok')
        return cache.get('filmaster_status_cache_test') == 'ok'

class Solr(Test):
    order = 5
    
    def is_enabled(self):
        return getattr(settings, 'HAYSTACK_SEARCH_ENGINE', '') == 'solr'
    
    def do_test(self):
        import pysolr
        conn = pysolr.Solr(settings.HAYSTACK_SOLR_URL)
        return bool(conn.search('Tarantino'))

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = "shows filmaster services status"
    
    def handle_noargs(self, **options):
	import sys
	sys.exit(Test.do_tests())
