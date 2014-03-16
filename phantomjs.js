var detect = require('./detect');
var page = require('webpage').create();
page.open('http://www.captainhcg.com/', function() {
  page.render('captainhcg.png');
  phantom.exit();
});
