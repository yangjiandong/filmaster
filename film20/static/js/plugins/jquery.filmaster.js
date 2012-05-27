
/**
 * Generate unique object id
 */
var NEXT_ID = 0;
var PREFIX='auto___'
function uniqueId() {
    var id = PREFIX + ++NEXT_ID; 
    if ( document.getElementById( id ) ) {
        return uniqueId();
    }
    return id;
}

( function( $ ) {
    $.fn.emptyFn = function() {}

    /* http://henrik.nyh.se/2008/07/jquery-double-submission */
    $.fn.preventDoubleSubmit = function() {
        this.submit(function() {
            if (this.beenSubmitted) {
                console.log('double submit, cancelled');
                return false;
            } else
                this.beenSubmitted = true;
        });
        return this;
    }

    $.fn.setButtonDisabled = function( val ) {
        return this.each( function() {
            if ( val == true ) $( this ).attr( "disabled", "true" );
            else $( this ).removeAttr( "disabled" );
        });
    }

    $.fn.ajaxWindow = function( options ) {
        var id = uniqueId();

        var settings = {
            'el'          : '<div id="' + id + '" class="content loading"></div>',
            'title'       : undefined,
            'url'         : undefined,
            'width'       : '560',
            'loadCallback': $.fn.emptyFn,
        };
        
        return this.each( function() {
            var $this = $( this );
            
            if ( options ) {
                $.extend( settings, options );
            }

            if ( !settings.url ) {
                settings.url = $( this ).attr( 'href' );
            }
            
            if ( !settings.title ) {
                settings.title = $( this ).html();
            }
            
            $this.click( function( e ) {
                FM.toplayer({
                    headline: settings.title,
                    content: settings.el,
                    width: settings.width
                });
                
                var $content = $( "#" + id );
                if ( settings.url ) {
                    $content.load( settings.url, function() {
                        $content.removeClass( 'loading' );

                        // center toplayer ...
                        // TODO: FM.toplayer.setPosition( x, y);
                        var height = $content.height();
                        var position_top = $( "#toplayer" ).position().top - height / 2;
                        position_top = position_top < 0 ? '0px' : position_top + 'px';
                        $( '#toplayer' ).css( 'top', position_top );
                        
                        // bind cancel button
                        // TODO: FM.toplayer.close
                        $( '[href="#cancel"]', $content ).click( function() {
                            $( "#toplayer" ).remove();
                            $( "#overlay" ).remove();
                            return false;
                        });
                        
                        settings.loadCallback.apply( this, [$content] );
                    });
                }
                // ..
                return false;
            })
        });
    };

    /*
     * add photo widget
     */
    $.fn.addPhoto = function( options ) {
        var loadCallback = function( content ) {
            $( '#form__add_person_photo', content ).submit( function() {
                var $form = $( this ),
                    $loader = $( '<div class="ajax-loader"></div>' ).appendTo( $form ).show(),
                    $button = $( 'input[type="submit"]', $form );

                $button.setButtonDisabled( true );
                $( '.upload-errors', content ).remove();
                
                $.post( $form.attr( 'action' ), $form.serialize(), function( json ) {
                    if ( json.success ) {
                        location = location
                    } else {

                        $loader.remove();
                        $button.setButtonDisabled( false );
                        var $errorlist = $( '<ul class="upload-errors errorlist"><ul>' )
                            .append( '<li>' + json.message + '</li>' )
                            .prependTo( $form.prev() );
                    }
                }, "json" );

                return false;
            });
        };
        return $( this ).ajaxWindow( $.extend( options || {}, { loadCallback: loadCallback } ) );
    };

    /*
     * add video widget
     */
    $.fn.addVideo = function( options ) {
        var loadCallback = function( content ) {
            $( 'form', content ).submit( function() {
                var $form = $( this ),
                    $loader = $( '<div class="ajax-loader"></div>' ).appendTo( $form ).show(),
                    $button = $( 'input[type="submit"]', $form );

                $( '.upload-errors', content ).remove();
                $button.setButtonDisabled( true );
                
                $.post( $form.attr( 'action' ), $form.serialize(), function( json ) {
                    if ( json.success ) {
                        $form.html( '<div class="success">' + json.message + '</div>' )
                        if ( !json.need_moderate ) {
                            location = location
                        }
                    } else {
                        $loader.remove();
                        $button.setButtonDisabled( false );
                        for ( var key in json.errors ) {
                            var $errorlist = $( '<ul class="upload-errors errorlist"><ul>' )
                            for ( var i = 0; i < json.errors[key].length; i++ ) {
                                $errorlist.append( '<li>' + json.errors[key][i] + '</li>' )
                            }

                            if ( key == '__all__' ) {
                                $errorlist.prependTo( $form )
                            } else {
                                $errorlist.prependTo( $( '#id_' + key ).prev() )
                            }
                        }
                    }
                }, "json" );

                return false;
            });
        };
        return $( this ).ajaxWindow( $.extend( options || {}, { loadCallback: loadCallback } ) );
    };

    /*
     * remove video
     */
    $.fn.removeVideo = function( options ) {

        var settings = {
            'url'      : undefined,
            'onLoad'   : undefined,
            'onError'  : undefined,
            'onSuccess': undefined
        };

        return this.each( function() {
            var $this = $( this );
            
            if ( options ) {
                $.extend( settings, options );
            }

            if ( !settings.url ) {
                settings.url = $( this ).attr( 'href' );
            }
            
            $this.click( function( e ) {

                if ( settings.onLoad != undefined ) {
                    settings.onLoad.apply( this, [$this] );
                }

                $.ajax({
                    method  : 'POST',
                    dataType: 'json',
                    url     : settings.url,
                    success : settings.onSuccess,
                    error   : settings.onError
                });
                // ..
                return false;
            });
        });
    };

    /*
     * edit box
     *
     * @param url
     * @param options
     */
    $.fn.editBox = function( url, options ) {
        var settings = {
            'input'    : '<input type="text">',
            'multiBox' : false,
            'container': undefined,
            'onLoad'   : undefined,
            'onSuccess': undefined
        };
        
        return this.each( function() {
            var $this = $( this );
            
            if ( options ) {
                $.extend( settings, options );
            }

            var $container = $( settings.container || $( '<div>' ).insertAfter( $( this ) ).hide() )
       
            $this.click( function() {
                $this.addClass( 'loading' )

                $.get( url, function( data ) {
                    var value = data['value'];

                    $this.removeClass( 'loading' )
                    if ( settings.multiBox ) {
                        var $input = $( '<div></div>' )
                        for ( var i = 0, len=value.length; i < len; i++ ) {
                            $input.append( $( settings.input )
                                                .addClass( 'input' )
                                                .attr( 'name', value[i].name )
                                                .val( value[i].value ) );
                        }
                    } else {
                        var $input = $( settings.input ).addClass( 'input' ).val( value )
                    }

                    var $box = $( '<div class="edit-box"></div>' )
                        .append( $( '<h1>' + $this.html() + '</h1>' ) )
                        .append( $input );

                    var $message = $( '<div class="message"></div>' );

                    if ( settings.onLoad != undefined ) {
                        settings.onLoad.apply( this, [$input, $this] );
                    }

                    if ( settings.container ) {
                        var $content = $container.contents().detach();
                    }

                    var close = function() {
                        $box.hide();
                        $this.show();
                        if ( settings.container ) {
                            $container.append( $content );
                        }
                    };

                    $( '<button>' )
                        .text( 'OK' )
                        .addClass( 'ok' )
                        .appendTo( $box )
                        .click( function() {
                            // if value is not changed 
                            //    just close edit box
                            var changes = false;
                            if ( settings.multiBox ) {
                                for( var i = 0, len = value.length; i < len; i++ ) {
                                    if ( value[i].value != $input.find( 'input.input[name=' + value[i].name + ']' ).val() ) {
                                        changes = true;
                                    }
                                }
                            } else if ( $input.val() != value ) {
                                changes = true;
                            }
    
                            if ( !changes ) {
                                return close();
                            }

                            $message.addClass( 'loading' );
                            $message.removeClass( 'error' );
                            $message.html( 'Sending data please wait ...' );
                            
                            // save data
                            var data = { 'value': '' }
                            if ( settings.multiBox ) {
                                for( var i = 0, len = value.length; i < len; i++ ) {
                                    data['v_' + value[i].name ] = $input.find( 'input.input[name=' + value[i].name + ']' ).val();
                                }
                            } else {
                                data['value'] = $input.val();
                            }

                            $.post( url, data, function( data ) {
                                if ( data.success ) {
                                    $message.addClass( 'success' );
                                    $message.removeClass( 'loading' );
                                    if ( data['message'] ) {
                                        $message.html( data['message'] );
                                    }

                                    setTimeout( function() {
                                        $box.fadeOut();
                                        $this.show();

                                        if ( settings.onSuccess != undefined ) {
                                            settings.onSuccess.apply( this, [data, $this] );
                                        } else if ( settings.container ) {
                                            $container.append( $content );
                                        }
                                    }, data['need_moderate'] ? 3000 : 1000 )
                                } else {
                                    $message.addClass( 'error' );
                                    $message.removeClass( 'loading' );
                                    $message.html( data['message'] );
                                }
                            }, "json" )
                                .error( function() {
                                    $message.addClass( 'error' );
                                    $message.removeClass( 'loading' );
                                    $message.html( 'Error, please try again' );
                                })
                        });
            
                    $( '<button>' )
                        .text( 'cancel' )
                        .addClass( 'x' )
                        .appendTo( $box )
                        .click( close );

                    $this.hide();
                    $box.append( $message );
                    $container
                        .append( $box )
                        .show();

                }, "json" )
                    .error( function( data ) {
                        $this.removeClass( 'loading' )
                        // TODO: implement if needed
                    });
                // prevent default
                return false;
            });
        });
    };

    /**
     * closes toplayer
     */
    $.closeTopLayer = function() {
        $( "#toplayer" ).remove();
        $( "#overlay" ).remove();
    };

    /**
     * Confirm window
     */
    $.confirmWindow = function( options ) {
        var id = uniqueId();

        var settings = {
            'id'         : id,
            'message'    : undefined,
            'title'      : undefined,
            'successText': gettext( 'Ok' ),
            'cancelText' : gettext( 'Cancel' ),
            'width'      : '310',
            'onOk'       : $.fn.emptyFn,
            'onCancel'   : function() {
                $.closeTopLayer();

                return false;
            },
        };
        
        if ( options ) {
            $.extend( settings, options );
        }

        var content = '<div id="' + settings.id + '" class="confirm-window">'
                    +    '<div id="main">'
                    +        '<p>' + settings.message + '</p>'
                    +        '<div class="buttons">'
                    +            '<input type="button" class="ok" value="' + settings.successText + '" />'
                    +            '<span>'
                    +                ' ' + gettext( 'or' ) + ' <a href="#cancel" class="cancel">' + settings.cancelText + '</a>'
                    +            '</span>'
                    +            '<div class="ajax-loader"></div>'
                    +        '</div>'
                    +    '</div>'
                    +  '</div>';

        FM.toplayer({
            content : content,
            headline: settings.title,
            width   : settings.width
        });
        
        var $content = $( "#" + settings.id );

        // on ok click
        $content.find( 'input.ok' ).click( settings.onOk );

        // on cancel click
        $content.find( 'a.cancel' ).click( settings.onCancel );
    };

    /*
     * remove blog post widget
     */
    $.fn.removeBlogPost = function( options ) {
        return this.each( function() {
            var $this = $( this );
            
            var defaults = {
                'id'         : uniqueId(),
                'title'      : gettext( 'Removing entry' ),
                'message'    : gettext( 'Do you want to remove this entry?' ),
                'successText': gettext( 'Remove entry' ),
                'onOk'       : function() {
                    this.disabled = true;
                    
                    var uri_part = $this.attr( 'href' ).replace( '#remove-', '' );
                    var $progress = $( "#" + defaults.id ).find( '.ajax-loader' ).show();
                    
                    $.ajax({
                        type   : 'DELETE',
                        url    : "http://" + location.host + "/api/" + FM.API_VERSION + "/user/" + uri_part + "/",
                        success: function( msg ) {
                            
                            $.closeTopLayer();
                            var $article = $this.closest( 'section' );
                            $article.animate( { opacity: 0. }, 1000, function() {
                                $article.slideUp( "slow" );
                            });

                        }
                    });
                    //..
                    return false;
                }
            };
          
            $this.click( function() {  
                $.confirmWindow( $.extend( options || {}, defaults ) );
                // ..
                return false;
            });
        });
    };

    /*
     * remove demot widget
     */
    $.fn.removeDemot = function( options ) {
        return this.each( function() {
            var $this = $( this );
            
            var defaults = {
                'id'         : uniqueId(),
                'title'      : gettext( 'Removing demot' ),
                'message'    : gettext( 'Do you want to remove this demot?' ),
                'successText': gettext( 'Remove demot' ),
                'onOk'       : function() {
                    this.disabled = true;
                    
                    $.ajax({
                        type   : 'POST',
                        url    : $this.attr( 'href' ),
                        success: function( msg ) {
                            
                            $.closeTopLayer();
                            window.location = msg
                        }
                    });
                    //..
                    return false;
                }
            };
          
            $this.click( function() {  
                $.confirmWindow( $.extend( options || {}, defaults ) );
                // ..
                return false;
            });
        });
    };

    /*
     * ajax form
     */
    $.fn.flmAjaxForm = function( options ) {
        var loadCallback = function( content ) {
            $( 'form', content ).submit( function() {
                var $form = $( this );
                $( '.form-errors', content ).remove();
                
                $.post( $form.attr( 'action' ), $form.serialize(), function( json ) {
                    if ( json.success ) {
                        $form.html( '<div class="success">' + json.message + '</div>' )
                    } else {
                        for ( var key in json.errors ) {
                            var $errorlist = $( '<ul class="form-errors errorlist"><ul>' )
                            for ( var i = 0; i < json.errors[key].length; i++ ) {
                                $errorlist.append( '<li>' + json.errors[key][i] + '</li>' )
                            }

                            if ( key == '__all__' ) {
                                $errorlist.prependTo( $form )
                            } else {
                                $errorlist.prependTo( $( '#id_' + key ).prev() )
                            }
                        }
                    }
                }, "json" );

                return false;
            });
        };
        return $( this ).ajaxWindow( $.extend( options || {}, { loadCallback: loadCallback } ) );
    };

    
    /**
     * Binds edit features form
     */
    function bindEditFeaturesForm( content ) {
        var ffCallback = function() {
            return bindEditFeaturesForm( content );
        };
    
        var $content = $( content ),
            $form = $( 'form', $content ),
            $edit_button = $( 'a#edit' ),
            $save_button = $( 'input#save' ),
            $loader = $( '.ajax-loader', $content ),
            url = $form.attr( 'action' );
       
        $edit_button.click( function() {
            $content.load( $( this ).attr( 'href' ), ffCallback );
            return false;
        });
        
        $save_button.click( function() {
            $form.submit();
        });
        
        $form.submit( function() {
            $( '.form-errors', $content ).remove();
            
            $save_button.setButtonDisabled( true );
            $loader.show();
 
            $.post( url, $form.serialize(), function( json ) {
                if ( json.success ) {
                    $content.load( url + "?preview", ffCallback );
                } else {
                    for ( var key in json.errors ) {
                        var $errorlist = $( '<ul class="form-errors errorlist"><ul>' )
                        for ( var i = 0; i < json.errors[key].length; i++ ) {
                            $errorlist.append( '<li>' + json.errors[key][i] + '</li>' )
                        }

                        if ( key == '__all__' ) {
                            $errorlist.prependTo( $form )
                        } else {
                            $errorlist.prependTo( $( '#id_' + key ).prev() )
                        }
                    }
                    $save_button.setButtonDisabled( false );
                }
                $loader.hide();
            }, "json" );

            return false;
        });
    };

    /*
     * film features ajax window
     */
    $.fn.filmFeatures = function( options ) {
        return $( this ).ajaxWindow( $.extend( options || { 'width': 700 }, { loadCallback: bindEditFeaturesForm } ) );
    };

    /*
     * moderation edit film features
     */
    $.fn.filmFeaturesForm = function( options ) {
        return this.each( function() {
            bindEditFeaturesForm( $( this ) );
        });
    };

    /**
     * compare films widget
     */
    $.fn.filmComparisionWidget = function( options ) {
        return this.each( function() {
            var $this    = $( this ),
                feature  = $( '.header strong', $this ).text(),
                $actions = $( "a.action", this ),
                url      = $this.attr( 'data-url' ),
                $parent  = $this.wrap( "<div/>" ).parent(),
                $slider  = $( '#slider', $this ),
                $posters = $( '.body a', $this ),
                a_title  = $( '.caption span', $posters[0] ).text(),
                b_title  = $( '.caption span', $posters[1] ).text(),
                $description  = $( '#slider-description', $this )
            ;

            var $ui_slider = $slider.slider({ 
                min: 0, 
                max: 2,
                value: 1, 
                slide: function( e, ui ) {
                    var v = ui.value;
                    if ( v == 0 ) {
                        $( $posters[0] ).addClass( 'selected' );
                        $( $posters[1] ).removeClass( 'selected' );
                        $description.html( '<strong>' + a_title + '</strong> ' + gettext( 'is more' ) + ' ' + feature );
                    } else if ( v == 2 ) {
                        $( $posters[1] ).addClass( 'selected' );
                        $( $posters[0] ).removeClass( 'selected' );
                        $description.html( '<strong>' + b_title + '</strong> ' + gettext( 'is more' ) + ' ' + feature );
                    } else {
                        $( $posters[0] ).addClass( 'selected' );
                        $( $posters[1] ).addClass( 'selected' );
                        $description.html( gettext( 'equally' ) + ' ' + feature );

                    }
                }
            });

            $actions.click( function() {
                var action = $( this ).attr( "id" )
                $this.animate( { opacity: .1 }, 1000, function() {
                    if ( action == 'vote' ) {
                        var val = $ui_slider.slider( 'value' )
                        action = val == '1' ? 'eq' : val == '0' ? 'a' : 'b'
                    }
                    $.ajax({
                        url : url,
                        type: 'POST',
                        data: { action: action },
                        success: function( data ) {
                            $parent.html( data );
                        },
                        error  : function() {

                        }
                    });
                });
                return false;
            });
        });
    };

    // Custom jquery ui autocomplete
    $.widget( "custom.fmcomplete", $.ui.autocomplete, {
        options: {
            minLength: 3,
            source: function(request, response) {
                $.ajax({
                    url: settings.FULL_DOMAIN + "/search/autocomplete/",
                    dataType: "jsonp",
                    data: {
                        term: request.term
                    },
                    success: function( data ) {
                        response( data );
                    }
                });
            },
            select: function( event, ui ) {
                window.location =  ui.item.url
            }
        },
        _renderItem: function( ul, item ) {
            return $( '<li class="ac-row ' + item.category + '"></li>' )
                .data( "item.autocomplete", item )
                .append( $( '<a></a>' )
                    .append( '<img src="' + item.image + '"/>' )
                    .append( '<b>' + item.value + '</b>' )
                    .append( '<div class="item-category">' + item.category + '</span>' )
                    .append( '<div class="item-description">' + item.description + '</span>' )
                    .append( '<div class="item-rule"></div>' )
                )
                .appendTo( ul );
        }
    });

    // initialize search autocomplete
    $( ".ac_search_phrase" ).fmcomplete();

    // initialize remove confirmations
    $( ".remove-blog-post" ).removeBlogPost();
    $( ".remove-demot" ).removeDemot();

    // initialize request duplicate
    $( ".request-dp" ).flmAjaxForm();
    $( ".request-dm" ).flmAjaxForm();

}) ( jQuery )
