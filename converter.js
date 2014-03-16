var detect = require('./detect'),
    mongodb = require('mongodb'),
    setting = require('./settings'),
    jsdom = require('jsdom');

var mongoclient = new mongodb.MongoClient(new mongodb.Server(setting.db_config.host, setting.db_config.port), {native_parser: true});

var global = this;

mongoclient.open(function(err, mongoclient) {
    var db = mongoclient.db(setting.db_config.name);
    db.collection('Page').find().sort( { url: 1 } ).toArray(function(err, pages){
        pages.forEach(function(p, idx){
            console.log(idx+": "+p.url)
            if(idx<1970)
                return
            var html = p.html;
            html = html.replace(/<\/font>/g,"").replace(/<font.*?>/g,"");
            if(html.indexOf('<html') < 0){
                html = '<!doctype html><html><body>'+ html + '</body></html>';

            }
            try{
                var document = jsdom.jsdom(html);
                var window = document.parentWindow;
                var jquery = require('jquery')(window);
            }
            catch(err){
                console.log(err)
                return;
            }
            var _detect = {
                'callbacks': {
                    'finished': function(_result){
                        console.log("done: "+p.url);
                        db.collection('Page').update({_id: p._id},{$set: {'clean': _result._html}}, function(err,data){
                            if (err){
                                console.log(err);
                            }else{
                                console.log("score succeded");
                            }
                        })
                    }
                },
                'window': window,
                'jQuery': jquery,
                'debug': false
            };
            _detect = detect.init(_detect);
            if(_detect)
                _detect.start();
        });
    });
});

