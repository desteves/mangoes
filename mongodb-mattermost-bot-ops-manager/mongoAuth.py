from pymongo import MongoClient
import ssl

def authenticate(host, ping):
    # ---- Move these to settings? ----
    userId = 'mike'
    password = 'password'
    CertFile = '/some/file.pem'
    CAFile = '/som/ca/pem'
    # This is how long we wait to contact server.
    serverSelectionTimeoutMS = 2000

    # ---- End variables that may move to settings ----


    authed = False
    uri = 'mongodb://mike:password@' + host

    # Note - we will use the ping info to set these variables
    isSSL = False
    isUserPwd = True
    isX509 = False
    if isUserPwd and not isSSL:
        # Try user/password, no TLS
        try:
            con = MongoClient(uri, serverSelectionTimeoutMS=serverSelectionTimeoutMS, socketTimeoutMS=500, connectTimeoutMS=500)
            authed = True
        except:
            print('Failed authentication to host ' + host + ' TLS = No, Mechanism = UserId/Password')
            pass

    if isUserPwd and isSSL:
        # Try TLS here
        try:
            con = MongoClient(uri, serverSelectionTimeoutMS=serverSelectionTimeoutMS,
                              ssl=True,
                              ssl_certfile=CertFile,
                              ssl_cert_reqs=ssl.CERT_REQUIRED,
                              ssl_ca_certs=CAFile)
            con['admin'].authenticate(userId, password)
            authed = True
        except:
            print('Failed authentication to host ' + host + ' TLS = Yes, Mechanism = UserId/Password')
            pass

    if isX509:
        # Try X509 here
        try:
            con = MongoClient(uri, serverSelectionTimeoutMS=serverSelectionTimeoutMS,
                              ssl=True,
                              authMechanism='MONGODB-X509',
                              ssl_certfile=CertFile,
                              ssl_cert_reqs=ssl.CERT_REQUIRED,
                              ssl_ca_certs=CAFile)
            con['admin'].authenticate(userId, password)
            authed = True
        except:
            print('Failed authentication to host ' + host + ' TLS = Yes, Mechanism = UserId/Password')
            pass

    if authed:
        return (con)
    else:
        return  None