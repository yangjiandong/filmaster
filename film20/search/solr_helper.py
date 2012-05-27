import os
import time
import shutil
import signal
import atexit
import subprocess

import logging
logger = logging.getLogger( __name__ )

from urlparse import urlparse
from xml.dom import minidom
from urllib2 import urlopen, URLError
from xml.etree import ElementTree as ET

from django.conf import settings
from django.core.management import call_command


SELF_PATH = os.path.abspath( os.path.dirname( __file__ ) )
SELF_RESOURCES_PATH = os.path.join( SELF_PATH, 'resources' )
SELF_TMP_DIR = os.path.join( SELF_RESOURCES_PATH, 'tmp' )

# -- -- -- -- -- --
SEARCH_ENGINE  = getattr( settings, 'HAYSTACK_SEARCH_ENGINE', None )
SOLR_URL       = getattr( settings, 'HAYSTACK_SOLR_URL', 'http://127.0.1:8983/solr' )

parsed = urlparse( SOLR_URL )
SOLR_PORT      = parsed.port if parsed and parsed.port else 8983

SOLR_ARGS      = getattr( settings, 'SOLR_ARGS', '' )
SOLR_JAVA_ARGS = getattr( settings, 'SOLR_JAVA_ARGS', '-server -Xmx600m -Xms600m -XX:+UseParallelGC -XX:+AggressiveOpts -XX:NewRatio=5 -Djetty.port=%s' % SOLR_PORT )
SOLR_VERSION   = getattr( settings, 'SOLR_VERSION', '3.5.0' )
SOLR_HOME      = getattr( settings, 'SOLR_HOME', os.path.join( SELF_RESOURCES_PATH, 'apache-solr-%s/server' % SOLR_VERSION ) )
SOLR_COMMAND   = getattr( settings, 'SOLR_COMMAND', 'java %s -jar start.jar %s' % ( SOLR_JAVA_ARGS, SOLR_ARGS ) )
SOLR_PIDFILE   = getattr( settings, 'SOLR_PIDFILE', os.path.join( SELF_TMP_DIR, 'solr.pid' ) )
SOLR_LOGFILE   = getattr( settings, 'SOLR_LOGFILE', os.path.join( SELF_TMP_DIR, 'solr.log' ) )
SOLR_LOCKFILE  = getattr( settings, 'SOLR_LOCKFILE', os.path.join( SELF_TMP_DIR, 'solr.lock' ) )
SOLR_SCHEMA    = getattr( settings, 'SOLR_SCHEMA', os.path.join( SOLR_HOME, 'solr/conf/schema.xml' ) )
# -- -- -- -- -- --


configuration = {
    'engine'   : SEARCH_ENGINE,
    'url'      : SOLR_URL,
    'home'     : SOLR_HOME,
    'command'  : SOLR_COMMAND,
    'pidfile'  : SOLR_PIDFILE,
    'logfile'  : SOLR_LOGFILE,
    'lockfile' : SOLR_LOCKFILE,
    'schema'   : SOLR_SCHEMA,
}

def is_supported():
    return SEARCH_ENGINE == 'film20.search.backends.custom_solr'

def is_testing_mode():
    from django.core import mail
    return hasattr( mail, 'outbox' )

class SolrDaemon( object ):

    def __init__( self, pidfile=SOLR_PIDFILE, command=SOLR_COMMAND, homedir=SOLR_HOME, url=SOLR_URL, logfile=SOLR_LOGFILE, lockfile=SOLR_LOCKFILE ):
        if not is_supported():
            raise Exception( "Solr is not configured ..." )

        self.url = url
        self.pidfile = pidfile
        self.command = command
        self.homedir = homedir
        self.lockfile = lockfile
        self.logfile = open( logfile, 'a' )

    def __store_lock( self ):
        open( self.lockfile, 'w' ).close()

    def __store_pid( self, pid ):
        f = open( self.pidfile, 'w' )
        f.write( str( pid ) )
        f.close()

    def __get_pid( self ):
        if os.path.exists( self.pidfile ):
            f = open( self.pidfile, 'r' )
            pid = f.read()
            f.close()
            return int( pid )
        return None

    def __is_runing( self, pid ):
        try:
            os.kill( pid, 0 )
        except OSError:
            return False
        return True

    @property
    def is_locked( self ):
        return os.path.exists( self.lockfile )

    def remove_lock( self ):
        os.remove( self.lockfile )

    def is_runing( self ):
        pid = self.__get_pid()
        return pid and self.__is_runing( pid )

    def __run( self, force=False, waiting_time=20, kill_atexit=True ):
        if not self.is_locked:
            if force or not self.is_runing():
                self.__store_lock()
                logger.info( "running command: %s" % self.command )
                self.process = subprocess.Popen( self.command.split(), cwd=self.homedir, 
                                                    preexec_fn=os.setsid, stdout=self.logfile, stderr=self.logfile  )
                self.__store_pid( self.process.pid )

                if self.wait( self.is_active, waiting_time ):
                    logger.info( "Solr started" )
                    if kill_atexit:
                        logger.info( "registered stop at exist signal" )
                        atexit.register( self.stop )

                # TODO if not ???
                self.remove_lock()
            else:
                logger.warning( "Solr instance already running - SKIPPING" )
        else:
            logger.warning( "Solr instance is locked - WAITING FOR START" )
            if self.wait( self.is_active, waiting_time ):
                logger.info( "Solr is now active" )

    def wait( self, fn, waiting_time=20 ):
        for t in range( waiting_time ):
            if fn(): return True
            logger.debug( " ... <%s> steel waiting %s" %( fn.__name__, t ) )
            time.sleep( 1 )
        return False

    def __ping( self ):
        response = urlopen( "%s/admin/ping" % self.url )
        return response.read()

    def start( self, force=False, kill_atexit=True ):
        logger.info( "STARTING ..." )
        self.__run( force, kill_atexit=kill_atexit )

    def stop( self, waiting_time=20 ):
        logger.info( "STOPING ..." )
        if self.is_runing():
            process = getattr( self, 'process', False )
            if process:
                process.kill()
                process.wait()
            else:
               os.kill( self.__get_pid(), signal.SIGTERM )
               if not self.wait( lambda: not self.is_runing(), waiting_time/2 ):
                    os.kill( self.__get_pid(), signal.SIGKILL )
                    self.wait( lambda: not self.is_runing(), waiting_time/2 )

    def restart( self, force=False, kill_atexit=True ):
        self.stop()
        self.start( force, kill_atexit=kill_atexit )

    def build_schema( self, kill_atexit=True ):
        if self.is_runing():
            self.stop()

        logger.info( "saving schema to %s" % SOLR_SCHEMA )
        call_command( 'build_solr_schema', filename=SOLR_SCHEMA )

        self.start( kill_atexit=kill_atexit )

        call_command( 'rebuild_index', interactive=False )

    def update_queue( self, kill_atexit=True ):
        if not self.is_runing():
            self.start( kill_atexit=kill_atexit )

        call_command( 'update_index_queue' )

    def is_active( self ):
        try:
            result = self.__ping()
            xml = ET.XML( result )
            for child in xml:
                if child.attrib.get( 'name' ) == 'status':
                    return child.text == 'OK'
        except Exception, e:
            logger.debug( 'Checking activity status exception: %s', e )
            return False

    def get_stats( self ):
        stats = {}
        try:
            response = urlopen( "%s/admin/stats.jsp" % self.url )
            parsed = minidom.parseString( response.read().encode( 'utf-8' ).decode( 'utf-8' ) )

            for entry in parsed.getElementsByTagName( 'entry' ):
                name = entry.getElementsByTagName( 'name' )[0].childNodes[0].data.strip()
                stats[name] = stats.get( name, {} )
                for stat in entry.getElementsByTagName( 'stat' ):
                    k = stat.getAttribute( 'name' )
                    v = stat.childNodes[0].data.strip()
                    stats[name][k] = v
        except URLError, e:
            logger.debug( 'Checking stats exception: %s', e )

        return stats


class DaemonWrapper( object ):
    cached_daemon = None
    
    @staticmethod
    def build_daemon():
        if DaemonWrapper.cached_daemon is None:
            if is_supported():
                if is_testing_mode():
                    test_data_dir = os.path.join( SELF_TMP_DIR, 'test-data' )
                    logger.debug( "removing test-data dir %s" % test_data_dir )
                    shutil.rmtree( test_data_dir )

                    settings.SOLR_JAVA_ARGS = '-Dsolr.data.dir=%s -Djetty.port=%s' % ( test_data_dir, SOLR_PORT )
                    DaemonWrapper.cached_daemon = SolrDaemon( command='java %s -jar start.jar' % settings.SOLR_JAVA_ARGS )
                else:
                    DaemonWrapper.cached_daemon = SolrDaemon()
        return DaemonWrapper.cached_daemon

build_daemon = DaemonWrapper.build_daemon
