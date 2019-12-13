# MongoDB BI Connector Demo with PowerBI

In this demo, we install everything locally. Please refer to [MongoDB official documentation](https://docs.mongodb.com/bi-connector/master/?_ga=2.112868032.593593240.1527042544-96261761.1510844831#local-database-and-bi-short) listing the installation and configuration steps to be taken.

In particular, see the [Quick start quide](https://docs.mongodb.com/bi-connector/master/local-quickstart/#quick-start-guide-for-windows)

## Installation

### About 

- We're installing everything in x64.
- 
<!-- - I'm using Windows 10 Pro running via Parallels Desktop on a Mac -->
- The dependencies installed here may not fully align with those specified in the documentation.

### Software Installed

<!-- MySQL Connector/ODBC 8.0.11 -->

- [MongoDB ODBC Driver](https://github.com/mongodb/mongo-odbc-driver/releases/tag/v1.0.0)
- MongoDB Enterprise 4.0
- MongoDB BI Connector 2.6
<!-- - MongoDB Enterprise 3.6.5 -->
- Visual C++ Redistributable for Visual Studio 2013
- Microsoft Excel
<!-- - Microsoft Power BI Desktop 2.58.5106.0_x64 -->

Once the above have been installed, add the `bin` paths for the MongoDB Enterprise and BI Connector to your `Path` System Environement variables. The default locations are:

```bash
C:\Program Files\MongoDB\Server\3.6\bin
C:\Program Files\MongoDB\Connector for BI\2.5\bin
```

## Configuration

- Create the directory path `C:\data\db`
- Open a command prompt and run `mongod` with all defaults. To verify, the last line should read similar to `2018-05-25T09:52:29.065-0500 I NETWORK  [initandlisten] waiting for connections on port 27017`
- Insert sample data via `mongoimport`. If you don't have any sample data, consider using the [Zip sample data](http://media.mongodb.org/zips.json). 
- Open a command prompt to the sample data directory and run `mongoimport --db test --collection zips --file zips.json`
- Open a command prompt and run `mongosqld install` with all defaults.
- Now run `mongosqld`. To verify, the last few lines should read similar to:
```bash
2018-05-23T19:57:09.698-0700 I NETWORK    [initandlisten] waiting for connections at 127.0.0.1:3307
2018-05-23T19:57:09.698-0700 I SAMPLER    [schemaDiscovery] initializing schema
2018-05-23T19:57:12.715-0700 I SAMPLER    [schemaDiscovery] sampling MongoDB for schema...
2018-05-23T19:57:12.897-0700 I SAMPLER    [schemaDiscovery] mapped schema for 1 namespaces: "test" (1): ["zips"]
```
- Create a DSN, windows search for and open `ODBC Data Sources (64-bit)` utility
  - Go to the `System DSN` tab and click `Add...`
  - Select `MySQL ODBC 8.0 Unicode Driver`
  - Add a name for your DNS, example `localMongo`
  - TCP/IP:  `127.0.0.1`, Port: `3307`
  - Database: `test`
  - Click `Test`. Verify it returns a `Connection Successful` message. Click `Ok`s to close the DSN application
- Open PowerBI:
  - Click `Get Data`
  - Search for and click `ODBC`
  - Select our just created DSN, in my case `localMongo`
  - Click `Ok`

At this point, Power BI is configured and reading data from the BI Connector which in turns communicates with our local MongoDB deployment.


Happy BI'ing!

