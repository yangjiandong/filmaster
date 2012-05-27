from settings import INSTALLED_APPS
import os
def test():
    for app in INSTALLED_APPS:
        app = app.replace("film20.", "")
        os.system('coverage run manage.py test '+app)
        os.system('coverage xml --omit=/usr/')

test()