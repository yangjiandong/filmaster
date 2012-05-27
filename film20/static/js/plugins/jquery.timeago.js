/** 
 * BASED ON
 *
 * timeago: a jQuery plugin, version: 0.9.3 (2011-01-21)
 * @requires jQuery v1.2.3 or later
 *
 * Copyright (c) 2008-2011, Ryan McGeary (ryanonjavascript -[at]- mcgeary [*dot*] org)
 */
(function( $ ) {

    $.timeago = function( timestamp ) {
        if ( timestamp instanceof Date ) {
            return inWords( timestamp );
        } 
    
        if ( typeof timestamp === "string" ) {
            return inWords( $.timeago.parse( timestamp ) );
        }

        return inWords( $.timeago.datetime( timestamp ) );
    };

    var $t = $.timeago;

    $.extend( $.timeago, {
        settings : {
            refreshMillis: 60000,
            allowFuture  : false,
            strings      : {
                prefixAgo    : null,
                prefixFromNow: gettext( "in" ),
                suffixAgo    : gettext( "ago" ),
                suffixFromNow: null,
                now          : gettext( "now" ),
                minute       : gettext( "a minute" ),
                hour         : gettext( "an hour" ),
                today        : gettext( "today" ),
                yesterday    : gettext( "yesterday" ),
                day_before   : gettext( "day before" ),
                last_week    : gettext( "last week" ),
                last_month   : gettext( "last month" ),
                last_year    : gettext( "last year" ),
                numbers      : []
            }
        },
        
        inWords: function( distanceMillis ) {
            var $l     = this.settings.strings,
                prefix = $l.prefixAgo,
                suffix = $l.suffixAgo
            ;
      
            if ( this.settings.allowFuture ) {
                if ( distanceMillis < 0 ) {
                    prefix = $l.prefixFromNow;
                    suffix = $l.suffixFromNow;
                }
                distanceMillis = Math.abs(distanceMillis);
            }

            var seconds = distanceMillis / 1000;
            var minutes = seconds / 60;
            var hours = minutes / 60;
            var days = hours / 24;
            var years = days / 365;

            function substitute( stringOrFunction, number ) {
                var string = $.isFunction( stringOrFunction ) ? stringOrFunction( number, distanceMillis ) : stringOrFunction;
                var value = ( $l.numbers && $l.numbers[number] ) || number;

                return string.replace( /%d/i, value );
            }

            function wrap( words ) {
                return $.trim( [prefix, words, suffix].join(" ") )
            }

            // ...
            if ( seconds < 10 )
                return $l.now;

            if ( seconds < 60 ) {
                 seconds = Math.round( seconds );
                 return wrap( substitute( "%d " + ngettext( 'seconds', 'seconds', seconds ), seconds ) );
            }

            if ( seconds < 120 )
                return wrap( substitute( $l.minute, 1 ) );

            if ( minutes < 60  ) {
                minutes = Math.round( minutes );
                return wrap( substitute( "%d " + ngettext( 'minutes', 'minutes', minutes ), minutes ) );
            }

            if ( minutes < 120  )
                return wrap( substitute( $l.hour, 1 ) );

            if ( hours < 24 ) {
                hours = Math.round( hours );
                return wrap( substitute( "%d " + ngettext( 'hours', 'hours', hours ), hours ) );
            }

            if ( days < 1 ) 
                return $l.today

            if ( days < 2 )
                return $l.yesterday;

            if ( days < 3 )
                return $l.day_before;

            if ( days < 7 ) {
                days = Math.round( days );
                return wrap( substitute( "%d " + ngettext( 'days', 'days', days ), days ) );
            }

            if ( days < 14 )
                return $l.last_week;

            if ( days < 31 ) {
                var weeks = Math.round( days / 7 );
                return wrap( substitute( "%d " + ngettext( 'weeks', 'weeks', weeks ), weeks ) );
            }

            if ( days < 61 )
                return $l.last_month;

            if ( days < 365 ) {
                var months = Math.round( days / 30 );
                return wrap( substitute( "%d " + ngettext( 'months', 'months', months ), months ) );
            }

            if ( days < 730 )
                return $l.last_year;

            years = Math.floor( years );
            return wrap( substitute( "%d " + ngettext( 'years', 'years', years ), years ) );
        },
    
        parse: function( iso8601 ) {
            var s = $.trim( iso8601 );
                s = s.replace( /\.\d\d\d+/,"" ); // remove milliseconds
                s = s.replace( /-/,"/" ).replace(/-/,"/" );
                s = s.replace( /T/," " ).replace(/Z/," UTC" );
                s = s.replace( /([\+\-]\d\d)\:?(\d\d)/," $1$2" ); // -04:00 -> -0400

            return new Date( s );
        },

        datetime: function( elem ) {
            // jQuery's `is()` doesn't play well with HTML5 in IE
            var isTime = $( elem ).get( 0 ).tagName.toLowerCase() === "time"; // $(elem).is("time");
            var iso8601 = isTime ? $( elem ).attr( "datetime" ) : $( elem ).attr( "title" );
      
            return $t.parse( iso8601 );   
        }
    });

    $.fn.timeago = function() {
        var self = this;
        self.each( refresh );

        var $s = $t.settings;
        if ( $s.refreshMillis > 0 ) {
            setInterval( function() { self.each( refresh ); }, $s.refreshMillis );
        }
        
        return self;
    };

    function refresh() {
        var data = prepareData( this );
        if ( !isNaN( data.datetime ) ) {
            $( this ).text( inWords( data.datetime ) );
        }
        
        return this;
    }

    function prepareData( element ) {
        element = $( element );
        if ( !element.data( "timeago" ) ) {
            element.data( "timeago", { datetime: $t.datetime( element ) });
        }
    
        return element.data( "timeago" );
    }

    function inWords( date ) {
        return $t.inWords( distance( date ) );
    }

    function distance( date ) {
        return ( new Date().getTime() - date.getTime() );
    }

    // fix for IE6 suckage
    document.createElement( "abbr" );
    document.createElement( "time" );

}( jQuery ) );
