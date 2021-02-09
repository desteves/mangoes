# Mongos Dockerfile for CF

## About

Assumes CF has Docker support enabled. See [link](https://docs.cloudfoundry.org/adminguide/docker.html)



## Building

```
docker build -t nullstring/mongos-for-cf .
docker push nullstring/mongos-for-cf
```

## To Run

### Locally

```
docker run -it -p 27017:27017 mongos-docker-test
```

### In Cloud Foundry

```
cf enable-feature-flag diego_docker

cf push cf push --var MMS_URI=https://opsman.company.com \
    --var MMS_GROUP_ID=123abc \
    --var MMS_AGENT_KEY=xyz
    


mongos-app --docker-image nullstring/mongos-for-cf



cf bind-service mongos-app my-spring-app
cf restage mongos-app

```