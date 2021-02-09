exports = async function (args) {
  
  // Get start/stop time
  const HOURS = 1;
  const secondsSinceEpoch = Math.round(Date.now() / 1000)
  var endDate = secondsSinceEpoch;
  var startDate = endDate - HOURS * 60 * 60; 
  
  //Get service
  const s3service = context.services.get("aws-professional-services").s3("us-east-1");
  
  // Get Secrets
  const username = context.values.get("publicKey");
  const pass = context.values.get("privateKey");
  const projectID = context.values.get("projectId");
  const getProcessesEndpoint = "api/atlas/v1.0/groups/" + projectID + "/processes";
  const bucket = context.values.get("s3bucket");
  
  // Get Process List
  response = await  context.functions.execute("getProcessesAPI", getProcessesEndpoint, username, pass);
    processList = response.results;
    processList.forEach( async function (process) {
      let processId = process.userAlias;  
      
      if (processId != undefined) {
        // process is NOT paused
     
        console.log("processId "+processId)
        
        // Get Audits for a given ProcessID
        let getAuditLogsEndpoint = "api/atlas/v1.0/groups/" + projectID + "/clusters/" + processId + "/logs/mongodb-audit-log.gz" ;
        let query = {
          "startDate" : [startDate.toString()],
          "endDate": [endDate.toString()] 
        };
        let auditLog = await context.functions.execute("getLogsAPI", getAuditLogsEndpoint, query, username, pass);
        
        // Push to S3
        const fileName =  processId + "_" + startDate + "_" + endDate + "_mongodb-audit-log.gz";
        console.log("fileName  " + fileName)
        await s3service.PutObject({
            'Bucket':bucket,
            'Key' : fileName,
            'ContentType': "text/plain",
            'ContentEncoding': "gzip",
            'Body': auditLog
        }).then(output =>console.log(JSON.stringify(output))).catch( err => console.log(err));
      } else {
        console.log("SKIPPING  "  + process.hostname + " as it appears to be paused.");
      }
    }) // end forEach
  return { 'ok': 1 };
}; 