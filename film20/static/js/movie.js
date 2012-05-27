$( "#add_photo" ).addPhoto();
$( "#add_video" ).addVideo();


var bindEditTitle = function( $el ) {
    $( "#edit_title" ).editBox( 'edit/title/', {
        'onSuccess': function( data, $a ) {
            if ( data.need_moderate ) {
                return false;
            }
            var $h1 = $( 'article.movie header h1' );
            var span = $( 'span', $h1 ).html();
            var $ot = $( 'article.movie header p.original-title' );
            
            if ( $ot.length == 0 ) {
                var text_nodes = $h1.contents().filter( function() { return this.nodeType == 3; } );
                var original_title = text_nodes ? text_nodes[0].nodeValue : '';
                $( '<p class="original-title">' + 
                        gettext( 'Original title' ) + ': ' + 
                        '<strong>' + original_title + '</strong>' + 
                   '</p>' 
                 ).insertAfter( $h1 );
            }

            $h1.html( '' )
                .append( data.value + ' ' )
                .append( $( '<span>' + span + ' </span>' ) )
                .append( $a );

            bindEditTitle();
        }
    });
};
bindEditTitle();

$( "#edit_tags" ).editBox( 'edit/tags/', {
    'container': 'article.movie .categories-wrapper',
    'onLoad'   : function( $input ) {
        $input.autocomplete( "/ajax/search_tag_autocomplete/", { multiple:true, multipleSeparator:"," });
    },
    'onSuccess': function( data, $a ) {
        var $container =  $( 'article.movie .categories-wrapper' ).html( '' );
        var $ul = $( '<ul class="categories"></ul>' ).appendTo( $container );
        for ( var i = 0; i < data.value.length; i++ ) {
            var tag = data.value[i];
            $( '<li>' )
                .append( '<a href="/tag/' + tag + '/">' + tag + ' </a>' )
                .appendTo( $ul );
        }

        $container.append( $a.css( 'display', 'inline' ) );
    }
});

$( "#edit_description" ).editBox( 'edit/description/', { 
    'input': '<textarea>',
    'container': 'article.movie .description',
    'onSuccess': function( data, $a ) {
        $( 'article.movie .description' )
            .append( data.value )
            .append( $a );
    }
});
