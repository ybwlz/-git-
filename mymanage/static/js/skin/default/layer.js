/*! layer-v3.5.1 */
;!function(window, undefined){
"use strict";

var isLayui = window.layui && layui.define, ready = {
    getPath: function(){
        var jsPath = document.currentScript ? document.currentScript.src : function(){
            var js = document.scripts,
            last = js.length - 1,
            src;
            for(var i = last; i > 0; i--){
                if(js[i].readyState === 'interactive'){
                    src = js[i].src;
                    break;
                }
            }
            return src || js[last].src;
        }();
        return jsPath.substring(0, jsPath.lastIndexOf('/') + 1);
    }(),
    
    config: {}, end: {}, minIndex: 0, minLeft: [],
    btn: ['&#x786E;&#x5B9A;', '&#x53D6;&#x6D88;'],
    
    type: ['dialog', 'page', 'iframe', 'loading', 'tips'],
    getStyle: function(node, name){
        var style = node.currentStyle ? node.currentStyle : window.getComputedStyle(node, null);
        return style[style.getPropertyValue ? 'getPropertyValue' : 'getAttribute'](name);
    },
    link: function(href, fn, cssname){
        if(!layer.path) return;
        var head = document.getElementsByTagName("head")[0], link = document.createElement('link');
        if(typeof fn === 'string') cssname = fn;
        var app = (cssname || href).replace(/\.|\//g, '');
        var id = 'layuicss-'+ app, timeout = 0;
        
        link.rel = 'stylesheet';
        link.href = layer.path + href;
        link.id = id;
        
        if(!document.getElementById(id)){
            head.appendChild(link);
        }
    }
};

var layer = {
    v: '3.5.1',
    ie: function(){
        var agent = navigator.userAgent.toLowerCase();
        return (!!window.ActiveXObject || "ActiveXObject" in window) ? (
            (agent.match(/msie\s(\d+)/) || [])[1] || '11'
        ) : false;
    }(),
    index: (window.layer && window.layer.v) ? 100000 : 0,
    path: ready.getPath,
    config: function(options, fn){
        options = options || {};
        layer.cache = ready.config = Object.assign({}, ready.config, options);
        layer.path = ready.config.path || layer.path;
        typeof options.extend === 'string' && (options.extend = [options.extend]);
        return this;
    },
    
    open: function(content, options){
        console.log('模拟打开层');
        return this;
    },
    
    alert: function(content, options, yes){
        alert(content);
        return this;
    },
    
    confirm: function(content, options, yes, cancel){
        return confirm(content) ? (typeof yes === 'function' && yes()) : (typeof cancel === 'function' && cancel());
    },
    
    msg: function(content, options, end){
        console.log(content);
        return this;
    },
    
    load: function(icon, options){
        console.log('加载中...');
        return this;
    },
    
    close: function(index){
        console.log('关闭层');
        return this;
    }
};

window.layer = layer;
}(window);
