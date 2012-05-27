{% load json %}
if(!window.console) {
    console = new function() {
        this.log = this.debug = this.info = function() {}
    }
}

window.settings = {{global.js_data|json|default:"{}"}};
window.FM = window.FM || {};
window.FM._post_init_callbacks  = [];
window.FM.addPostInitCallback = function(cb) {
    window.FM._post_init_callbacks.push(cb);
}
window.FM.postInit = function() {
    var cb;
    while(cb=FM._post_init_callbacks.shift()) 
        cb();
}

