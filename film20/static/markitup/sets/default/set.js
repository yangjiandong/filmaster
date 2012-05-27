// ----------------------------------------------------------------------------
// markItUp!
// ----------------------------------------------------------------------------
// Copyright (C) 2011 Jay Salvat
// http://markitup.jaysalvat.com/
// ----------------------------------------------------------------------------
// Html tags
// http://en.wikipedia.org/wiki/html
// ----------------------------------------------------------------------------
// Basic set. Feel free to add more tags
// ----------------------------------------------------------------------------
var mySettings = {
	onShiftEnter:  	{keepDefault:false, replaceWith:'<br />\n'},
	onCtrlEnter:  	{keepDefault:false, openWith:'\n<p>', closeWith:'</p>'},
	onTab:    		{keepDefault:false, replaceWith:'    '},
	markupSet:  [ 	
		{name:'Bold', key:'B', openWith:'(!(<strong>|!|<b>)!)', closeWith:'(!(</strong>|!|</b>)!)' },
		{name:'Italic', key:'I', openWith:'(!(<em>|!|<i>)!)', closeWith:'(!(</em>|!|</i>)!)'  },
		{name:'Stroke through', key:'S', openWith:'<del>', closeWith:'</del>' },
		{separator:'---------------' },
		{name:'Bulleted List', openWith:'    <li>', closeWith:'</li>', multiline:true, openBlockWith:'<ul>\n', closeBlockWith:'\n</ul>'},
		{name:'Numeric List', openWith:'    <li>', closeWith:'</li>', multiline:true, openBlockWith:'<ol>\n', closeBlockWith:'\n</ol>'},
		{separator:'---------------' },
		{name:'Picture', key:'P', replaceWith: function( markItUp ) {
            closeTopLayer = function() {
                $( "#toplayer" ).remove();
                $( "#overlay" ).remove(); 
            }

            upload_photo_callback = function( data ) {
                $.markItUp( { openWith: '<img src="' + data['image'] + '" />' } );
                closeTopLayer();
            }

            var id = uniqueId()
            var settings = {
                'title' : 'Insert Photo',
                'url'   : '/upload/picture',
                'el'    : '<div id="' + id + '" class="content loading"></div>'
            };

            FM.toplayer({
                headline: settings.title,
                content: settings.el,
                width: '560',
            });
            
            var $content = $( "#" + id );
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
                    closeTopLayer();
                    return false;
                });
            });
        }},
		{name:'Spoiler', openWith:'<spoiler>', closeWith:'</spoiler>' },
	]
}
