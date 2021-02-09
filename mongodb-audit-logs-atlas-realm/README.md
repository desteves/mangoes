# Realm App

This Realm App allows for downloading of audit logs at specified intervals

## TODO

- Add scheduled trigger

## To Import

```
# 1. Update AWS Service Access Key
sed -i 's/CHANGEME/ADD-YOUR-ACCESS-KEY-HERE/' audit/services/aws-professional-services/config.json

# 2. Import as a *new* Realm App
realm-cli import --path=audit --strategy=replace-by-name 

# 3. Note down the app-id
APPID=audit-abcde

# 4. Update a Secrets & Variables
## AWS S3 Bucket
realm-cli secrets update --name=s3bucket --value=NewSecretValue --app-id="${APPID}"

## Atlas API key
realm-cli secrets update --name=privateKey --value=NewSecretValue --app-id="${APPID}"
realm-cli secrets update --name=publicKey --value=NewSecretValue --app-id="${APPID}"

## Atlas Project ID
realm-cli secrets update --name=projectId --value=NewSecretValue --app-id="${APPID}"




```
