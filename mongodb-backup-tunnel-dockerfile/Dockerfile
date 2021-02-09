FROM ubuntu:bionic

##########################################################################
# Tools
##########################################################################

## https://docs.mongodb.com/manual/tutorial/install-mongodb-enterprise-on-ubuntu/
RUN apt-get update && apt-get install -y wget gnupg
RUN wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | apt-key add -
RUN echo "deb [ arch=amd64 ] http://repo.mongodb.com/apt/ubuntu bionic/mongodb-enterprise/4.2 multiverse" |  tee /etc/apt/sources.list.d/mongodb-enterprise.list
## mongodb-enterprise-tools -- Contains the following MongoDB tools: mongoimport bsondump, mongodump, mongoexport, mongofiles, mongorestore, mongostat, and mongotop.
## mongodb-enterprise-shell -- Contains the mongo shell.
RUN apt-get update && apt-get install -y mongodb-enterprise-tools mongodb-enterprise-shell	

##########################################################################
# Tunnel
##########################################################################

EXPOSE   27017
WORKDIR /root
## using ADD for auto untar
ADD tunnel-*.tar.gz . 
RUN mv tunnel-*.txt atlas.txt && mv tunnel-* tunnel
ENTRYPOINT [ "./tunnel" ]

## then exec bash into container to run mongo shell, mongorestore or mongodump commands


kinto-un