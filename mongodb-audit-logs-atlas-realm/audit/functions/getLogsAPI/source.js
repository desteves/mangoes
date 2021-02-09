exports = async function (PATH, QUERY, U, P) {
  const arg = {
    scheme: 'https',
    host: 'cloud.mongodb.com',
    path: PATH,
    query: QUERY, // date range
    username: U,
    password: P,
    headers: {'Content-Type': ['application/gzip'], 'Accept-Encoding': ['gzip, deflate']},
    digestAuth: true
  }
  response = await context.http.get(arg);

  
  try {
    const bodyText =  response.body.text();
    return bodyText
  } catch (error) {
    console.log("no body in request")
  }
  return null;
  
}