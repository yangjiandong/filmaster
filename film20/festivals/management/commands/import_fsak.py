# -!- coding: utf-8 -!-
from .base import BaseFestivalImporter
import re
import pytz

class Command(BaseFestivalImporter):

    THEATERS_MAP = {
            u'KRAKÓW': u'Pod Baranami',
            u'GDAŃSK': u'Żak',
            u'POZNAŃ': u'Muza',
            u'WROCŁAW': u'Helios',
            }

    def _parse(self, filename, column):
        import csv
        date = None
        reader = csv.reader(self.open_file(filename))
        header = reader.next()
        theater_name = re.sub(r'\s+\d+-\d+$', '', header[column+1]).strip().decode('utf-8')

        theater = self.THEATERS_MAP.get(theater_name, theater_name).lower()
        theater = self.theaters_map.get(theater)

        for row in reader:
            date = row[0] or date
            t = row[column].strip()
            title = row[column+1].strip().decode('utf-8')
            title = re.sub(r'\+.*$', '', title).strip()
            if title in (u'OTWARCIE', u'ZAMKNIĘCIE'): continue
            if date and t and title:
                h, m = map(int, re.match('(\d+).(\d+)', t).groups())
                day = re.match('\d+', date).group(0)
                t = self.get_screening_datetime(h, m, day)
                t = pytz.timezone(theater.timezone_id).localize(t)
                yield {
                        'title':title,
                        'times':[(theater, t, '')],
                        'tag': self.festival.tag,
                }

    def films(self):
        self.theaters_map = dict((t.name.lower(), t) for t in self.theaters)
        for fn in ('fsak-pl.csv', 'fsak-waw.csv'):
            for col in (2, 4, 6):
                for film in self._parse(fn, col):
                    yield film

