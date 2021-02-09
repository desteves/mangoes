exports = async function (PATH, U, P) {
  const arg = {
    scheme: 'https',
    host: 'cloud.mongodb.com',
    path: PATH,
    username: U,
    password: P,
    headers: {'Content-Type': ['application/json']},
    digestAuth: true
  }
  response = await context.http.get(arg);
  return EJSON.parse(response.body.text());
}