function open_channel(cb) {
    var ch=new goog.appengine.Channel(token);
    ch.open({
          'onmessage':function(m) {
               try {
                   var data = JSON.parse(m.data);
                   console.log('channel received:', data);
                   $('body').trigger('channel_message', [data]);
               } catch(err) {
                   console.error(err);
               }
               /*
               if(window.webkitNotifications) {
                   var notice = webkitNotifications.createNotification(settings.FULL_DOMAIN + '/static/favicon.ico', 'title', m.data);
                   notice.show();
                   setTimeout(function() {
                       notice.cancel();
                   }, 5000);
               }*/
          }, 
          'onopen':function(){
            console.log('opened');
            cb();
          }
    });
}
function init_channel(username, cb) {
    $.getScript('http://filmaster-tools.appspot.com/_ah/channel/jsapi', function() {
        $.getScript('http://filmaster-tools.appspot.com/request-token/?client_id=' + username, function() {
          console.log('channel scripts loaded');
          $(document).ready(function() {open_channel(cb);});
        });
    });
}
