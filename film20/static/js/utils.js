var display_error = function(msg, elem) {
    var msg_div = $('<div class="error"><ul class="errorlist"><li>'+msg+'</li></ul></div>');
    msg_div.insertAfter(elem).fadeIn('slow').animate({opacity: 1.0}, 5000).fadeOut('slow',function() { msg_div.remove(); });
}; 
var display_info = function(msg, elem) {
    var msg_div = $('<div class="action-info">'+msg+'</div>');
    msg_div.insertAfter(elem).fadeIn('slow').animate({opacity: 1.0}, 5000).fadeOut('slow',function() { msg_div.remove(); });
};

function create_edit_box(container, textarea, text, ok_cb, cancel_cb) {
    var content = $(container).contents().detach()
    var input=$(textarea ? '<textarea>' : '<input type="text">').val(text);
    var edit_box = $('<div>')
    edit_box.append(input);
    $('<button>').text('ok').appendTo(edit_box).click(function() {
      $(container).append(content);
      ok_cb(input.val());
      edit_box.remove();
    });
    $('<button>').text('cancel').appendTo(edit_box).click(function() {
      cancel_cb && cancel_cb();
      edit_box.remove();
      $(container).append(content);
    })
    $(container).append(edit_box);
}

function edit_tags(editlink, permalink, type) {
    var cont = $(editlink).parent('.tags');
    var uri;
    if(type==1) 
        uri='/api/1.0/film/';
    else if(type==2) 
        uri='/api/1.0/person/';
    else
        return;
    
    $.get(uri + permalink + '/', null, function(data) {
        create_edit_box(cont, false, data.tags && data.tags.join(', ') || "", function(txt) {
            var ed = cont.find('.edit').detach()
            cont.empty();
            var tags = txt.split(',')
            for(var i=0; i<tags.length; i++) {
              $("<span class='tag'>").text(tags[i]).appendTo(cont);
              if(i<tags.length-1) cont.append(", ");
            }
            cont.append(ed);
        });
    });
}

function edit_film_tags(permalink) {
    $.get('/api/1.0/film/' + permalink + '/', null, function(data) {
        var cont = $('#movie_info .tags');
        create_edit_box(cont, false, data.tags.join(', '), function(txt) {
            var ed = cont.find('.edit').detach()
            cont.empty();
            var tags = txt.split(',')
            for(var i=0; i<tags.length; i++) {
              $("<span class='tag'>").text(tags[i]).appendTo(cont);
              if(i<tags.length-1) cont.append(", ");
            }
            cont.append(ed);
        });
    });
}

function toggle_more() {
    $(this).parents('.collapsed,.expanded').toggleClass('expanded').toggleClass('collapsed')
    return false;
}

$(document).ready(function() {
  $('.collapsed,.expanded').find('a.lessmore').click(toggle_more);
});
