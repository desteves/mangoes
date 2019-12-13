# MongoDB .Net C# Application Demo


This demo takes snippets of code from the [official driver documentation](http://mongodb.github.io/mongo-csharp-driver/) and puts them together in a running solution.

- Note: This demo assumes you have a local `mongod` process already configured and running on port `27017`


## Configuration


- Start a new Visual Studio solution
- Select a console app
- Search for NuGet dependency `MongoDB.Driver` and install.
- Edit the `Program` class as follows


```csharp

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using MongoDB.Bson;
using MongoDB.Driver;

namespace ConsoleApp1
{
	class Program
	{
		static void Main(string[] args)
		{
			// Using a connection-string
			var client = new MongoClient("mongodb://localhost:27017");
			var database = client.GetDatabase("mysampledatabase");
			// We’ve used a BsonDocument to indicate that we have no pre-defined schema. 
			// It is possible to use your plain-old-C#-objects (POCOs) as well. 
			var collection = database.GetCollection<BsonDocument>("dotnet");
			var document = new BsonDocument
{
	{ "name", "MongoDB" },
	{ "type", "Database" },
	{ "count", 1 },
	{ "info", new BsonDocument
			  {
				  { "x", 203 },
				  { "y", 102 }
			  }
	}
};


			// Insert a Document
			 collection.InsertOne(document);


			//Insert Multiple Documents
			var documents = Enumerable.Range(0, 100).Select(i => new BsonDocument("i", i));
			 collection.InsertMany(documents);


			//Counting Documents
			var count = collection.Count(new BsonDocument());
			Console.WriteLine(count);


			// Query the Collection
			document =  collection.Find(new BsonDocument()).FirstOrDefault();
			Console.WriteLine(document.ToString());

			// Get a Single Document with a Filter
			var filter = Builders<BsonDocument>.Filter.Eq("i", 71);

			document =  collection.Find(filter).First();
			Console.WriteLine(document);

			// Get a Set of Documents with a Filter
			filter = Builders<BsonDocument>.Filter.Gt("i", 50);
			var result = collection.Find(filter).ToList();
			foreach (var d in result)
			{
				Console.WriteLine(d["i"]);
			}
		}
	}
}




```
