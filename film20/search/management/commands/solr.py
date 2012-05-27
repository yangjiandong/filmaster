import sys
from optparse import make_option
from django.conf import settings
from django.core.management.base import CommandError
from film20.core.management.base import BaseCommand

class Command( BaseCommand ):
    PID_FILE='/tmp/solr.pid'

    option_list = BaseCommand.option_list + (
        make_option( '--stop', dest='stop', default=False, action='store_true' ),
        make_option( '--start', dest='start', default=False, action='store_true' ),
        make_option( '--stats', dest='stats', default=False, action='store_true' ),
        make_option( '--status', dest='status', default=False, action='store_true' ),
        make_option( '--restart', dest='restart', default=False, action='store_true' ),
        make_option( '--build_schema', dest='build_schema', default=False, action='store_true' ),
    )

    def handle( self, **options ):
        try:
            from film20.search.solr_helper import build_daemon
            daemon = build_daemon()
        except Exception, e:
            raise CommandError( e )

        if options.get( 'stop' ): 
            daemon.stop()

        if options.get( 'start' ):
            daemon.start( kill_atexit=False )

        elif options.get( 'restart' ): 
            daemon.restart( kill_atexit=False )

        elif options.get( 'status' )   : 
            print "SOLR IS ACTIVE !" if daemon.is_active() else "UPS SOLR IS DEAD ..."

        elif options.get( 'stats' )   : 
            print daemon.get_stats()

        elif options.get( 'build_schema' )   : 
            print daemon.build_schema( kill_atexit=False )
