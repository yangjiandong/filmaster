$( "#edit_biography" ).editBox( 'edit/biography/', { 
    'input': '<textarea>',
    'container': 'article.person .biography',
    'onSuccess': function( data, $a ) {
    $( 'article.person .biography' )
        .append( data.value )
        .append( $a );
    }
});

var bindEditTitle = function( $el ) {
    $( "#edit_title" ).editBox( 'edit/name/', { 
        'multiBox' : true,
        'onSuccess': function( data, $a ) {
            $( '#person_name' )
                .html( data.value[0].value + ' ' + data.value[1].value + ' ' )
                .append( $a );
            
            bindEditTitle();
         }
    });
};

bindEditTitle();
