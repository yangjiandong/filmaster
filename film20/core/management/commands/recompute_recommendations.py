from film20.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--save', action='store_true', dest='save',
            help='Saves recommendations in db'),
    )

    def handle(self, *args, **opts):
        from film20.new_recommendations import recommendations_engine as engine
#        engine.init_features(save=opts.get('save'))
        engine.init_features()

