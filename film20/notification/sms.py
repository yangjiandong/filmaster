# -!- coding: utf-8 -!-
from django.utils import simplejson as json
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import os
import logging
logger = logging.getLogger(__name__)

import urllib2

from media import BaseMedium
class SMS(BaseMedium):
    display = _("SMS")
    name = "sms"
    id = "sms"

    BASE_URL = "http://panel.isender.pl/"
    ENDPOINT_URL = BASE_URL + "webservices/sms2?wsdl"

    MSG_TEMPLATE = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ema="http://sms2.webservices.multikomunikator.arise.pl/">
   <soapenv:Header/>
   <soapenv:Body>
      <ema:wyslijKampanieSMS>
         <!-- Wymagane: nazwa kampanii-->
         <nazwa>%(name)s</nazwa>
         <!-- Opcjonalne: opis kampanii-->
         <opis></opis>
         <!-- Opcjonalne: data uruchomienia kampanii ( puste pole oznacza wysyłke natychmiastową )-->
         <dataUruchomienia></dataUruchomienia>
         <!--Wymagane: personalizacja ( true, false )-->
         <personalizacja>false</personalizacja>
         <!--Wymagane: treść SMS-->
         <tresc>%(content)s</tresc>
         <!--Opcjonalne: true - wiadomość typu flash ( tylko dla smsa bez nadawcy )-->
         <flash></flash>
         <!--Opcjonalne: jeżeli podane wysyłany będzie sms z polem nadawcy-->
         <nadawca>%(sender)s</nadawca>
         <!--Opcjonalne: adres wapurl dla wiadomości sms ( tylko dla smsa z nadawcą )-->
         <wapUrl></wapUrl>
         <!--Opcjonalne: email na który ma zostać wysłane potwierdzenie zakończenia kampanii-->
         <emailPotwierdzajacy></emailPotwierdzajacy>
         <!--Opcjonalne: do jakiej grupy prowadzone jest wysyłka (NOWA, ISTNIEJACA) jezeli nie podane to wysyłka jest prowadzona tylko do kontaktów podanych w zapytaniu-->
         <typGrupy></typGrupy>
         <!--Opcjonalne: kontakty do wysyłki-->
         <kontakty>
            <imie></imie>
            <nazwisko></nazwisko>
            <nazwa></nazwa>
            <ulica></ulica>
            <kodPocztowy></kodPocztowy>
            <miasto></miasto>
            <wojewodztwo></wojewodztwo>
            <powiat></powiat>
            <gmina></gmina>
            <telefonStacjonarny></telefonStacjonarny>
            <telefonKomorkowy>%(phone_number)s</telefonKomorkowy>
            <numerFax></numerFax>
            <email></email>
            <typWlasnosci></typWlasnosci>
            <formaPrawna></formaPrawna>
            <paramValue1></paramValue1>
            <paramValue2></paramValue2>
            <paramValue3></paramValue3>
            <paramValue4></paramValue4>
            <paramValue5></paramValue5>
            <paramValue6></paramValue6>
            <paramValue7></paramValue7>
            <paramValue8></paramValue8>
            <paramValue9></paramValue9>
            <paramValue10></paramValue10>
            <paramValue11></paramValue11>
            <paramValue12></paramValue12>
            <paramValue13></paramValue13>
            <paramValue14></paramValue14>
            <paramValue15></paramValue15>
            <!-- Wymagane: typ kontaktu: 0 - B2B, 1 - B2C-->
            <typ>B2C</typ>
         </kontakty>
         <!--Opcjonalne: nazwa grupy nowej lub istniejącej w zależności od wartości parametru typGrupy-->
         <nazwaGrupy></nazwaGrupy>
         <!--Opcjonalne: opis nowej grupy-->
         <opisGrupy></opisGrupy>
         <!--Opcjonalne: wykorzystywane dla parametru typGrup=ISTNIEJACE, jezeli true to duplikaty kontaktów z grupy podane w zapytaniu są ignorowane, jeżeli false to duplikaty kontaktów z grupy podane w zapytaniu zastępują kontakty w grupie, jeżeli puste kontakty są ignorowane-->
         <ignorujDuplikaty></ignorujDuplikaty>
      </ema:wyslijKampanieSMS>
   </soapenv:Body>
</soapenv:Envelope>
"""

    def is_enabled(self, user):
        return bool(user.get_profile().phone_number)

    @classmethod
    def format(cls, txt):
        from film20.utils.texts import deogonkify
        return str(deogonkify(txt)[0:160])

    def send_notice_impl(self, user, type, context):
        data = self.render_template(type, 'sms.txt', context)
        
        import time, random

        unique_name = "filmaster_%x%x" % (time.time()*1000, random.randrange(65536))

        content = self.format(data)

        msg = self.MSG_TEMPLATE % {
            'name':unique_name,
            'phone_number':user.get_profile().phone_number,
            'content': content,
            'sender': 'Info',
        }
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.BASE_URL, settings.SMS_PROVIDER_USERNAME, settings.SMS_PROVIDER_PASSWORD)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        # urllib2.install_opener(opener)

        req = urllib2.Request(self.ENDPOINT_URL)
        req.add_header('Content-Type', 'text/xml; charset=utf-8')
        data = opener.open(req, msg).read()

        logger.info("SMS (len: %d): msg: %r, sent: %r, reply:%r", len(content), content, msg, data)

    # how spam-sensitive is the medium
    def get_spam_sensitivity(self):
        return 2

    def supports(self, notice_type):
        return notice_type.label in ("showtimes_weekly_recommendations",)

    def description(self):
        return _("In order to enable notifications on your phone, enter your number in your profile")
