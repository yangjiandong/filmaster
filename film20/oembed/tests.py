from film20.utils.test import TestCase
from film20.oembed.core import replace
from django.conf import settings
from django.utils import unittest

class OEmbedTests(TestCase):
    noembed = ur"This is text that should not match any regex."
    end = ur"There is this great video at %s"
    start = ur"%s is a video that I like."
    middle = ur"There is a movie here: %s and I really like it."
    trailing_comma = ur"This is great %s, but it might not work."
    trailing_period = ur"I like this video, located at %s."
    
    loc = u"http://www.viddler.com/explore/SYSTM/videos/49/"
    
    embed = u'<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" width="300" height="211" id="viddlerplayer-e5cb3aac"><param name="movie" value="http://www.viddler.com/player/e5cb3aac/" /><param name="allowScriptAccess" value="always" /><param name="wmode" value="transparent" /><param name="allowFullScreen" value="true" /><embed src="http://www.viddler.com/player/e5cb3aac/" width="300" height="211" type="application/x-shockwave-flash" wmode="transparent" allowScriptAccess="always" allowFullScreen="true" name="viddlerplayer-e5cb3aac" ></embed></object>\n'
    
    loc = u'http://www.youtube.com/watch?v=WRQ3rwoqdeA'
    
    embed = u'<object width="300" height="169"><param name="movie" value="http://www.youtube.com/v/WRQ3rwoqdeA?version=3&feature=oembed"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/WRQ3rwoqdeA?version=3&feature=oembed" type="application/x-shockwave-flash" width="300" height="169" allowscriptaccess="always" allowfullscreen="true"></embed></object>\n'
    
    @unittest.skipIf(not settings.INTEGRATION_TESTS, "disabled test which needs internet connection")
    def testNoEmbed(self):
        self.assertEquals(
            replace(self.noembed),
            self.noembed
        )

    @unittest.skipIf(not settings.INTEGRATION_TESTS, "disabled test which needs internet connection")
    def testEnd(self):
        for text in (self.end, self.start, self.middle, self.trailing_comma, self.trailing_period):
            self.assertEquals(
                replace(text % self.loc),
                text % self.embed
            )
    
    @unittest.skipIf(not settings.INTEGRATION_TESTS, "disabled test which needs internet connection")
    def testManySameEmbeds(self):
        text = " ".join([self.middle % self.loc] * 2) 
        resp = " ".join([self.middle % self.embed] * 2)
        self.assertEquals(replace(text), resp)
