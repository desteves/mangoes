var express = require('express');
var app = express();
var router = express.Router();
var svcs = process.env.VCAP_SERVICES;
var mongouri;

app.listen(process.env.PORT || 3000);

if (svcs) {
  //app is running in the cloud
  svcs = JSON.parse(svcs);
  if (svcs['mongodb-odb'])
    mongouri = svcs['mongodb-odb'][0].credentials.uri;
} else {
  //running locally or not on cloud foundry
  mongouri = 'mongodb://localhost:27017';
}

app.get('/', function (req, res) {
  res.send(mongouri)
});