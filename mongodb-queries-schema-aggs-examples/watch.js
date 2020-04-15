while( true) 
{
  var cur =  db.getSiblingDB("cstest").collection.watch();
  while (!cur.isExhausted())
  {
    if (cur.hasNext())
    {
      print (JSON.stringify(cur.next(), null, 2));
    }
  }

  print ("exhausted cursor");

}
