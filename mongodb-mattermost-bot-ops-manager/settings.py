#### Global settings for all modules ####
# Import this file into every module and specify settings here.

# mongoDaemon settings
daemonSleepTimeSeconds = 300

# Lock and wait settings
waitForGroupLockSeconds = 5
waitForUpgradeSeconds = 120
checkUpgradeStatusSeconds = 5
waitForRestartSeconds = 15

# Chat server settings
chatServerUrl = 'http://localhost:8065/hooks/abc123abc123'
chatServerVendor = 'Mattermost'
chatServerUser = 'om-alerts'
chatServerToken = 'abc123abc123'
chatServerTeam = 'abc123abc123'
chatServerAPIUrl = 'http://localhost:8065/api/v4'
chatBotPrefix = ''
chatIgnoreUsers = ['mongobot', 'airflow'] # These are the users we post as, so ignore any post from them
chatCallBackUrl = 'http://docker.for.mac.localhost/chatbot' # The URL of our chatbot to be called by the chat server

# Ticket server settings
ticketServerUrl = 'http://mycompany.jira.com'

# Ops Manager settings
opsmgrServerUrl = 'http://opsmgr.vagrant.local:8080' # Be sure there is no trailing slash here
opsmgrUser = 'admin@localhost.com'
opsmgrApiKey = 'abc123abc123'
opsmgrMetricPeriod = 'PT1H' # ISO-8601 formatted period to chart (PT1H = most recent 1 hour)
opsmgrMetricGranularity = 'PT10S' # ISO-8601 formatted period to chart (PT10S = every 10 seconds)
opsmgrWebHookReturnValue = '{"ok": true}' # Value OpsMgr want to see returned from the webhook if all went well
opsmgrDefaultGroup = 'test' # If O/M group is not provided in chat, we will use this one

# O/M Charting Settings
chartingRemoveBelowThreshold = 1.0 # Remove all points below this threshold to improve chart appearance
chartingYLimitScaling = 1.5 # Set Y axis scale to the max Y value times this number to improve chart appearance
chartingSeriesColors = ['b', 'g', 'k', 'y'] # Standard plot line colors
chartingSeriesHighlightColors = ['r', 'c', 'm'] # Hi-lighted plot line colors
chartingGridColor = '#116149'
chartingSizeWidthPx = 400.0
chartingSizeHieghtPx = 200.0
chartingDPI = 100.0
chartingDateFmt = '%H:%M' # For X axis date display
chartingTitleFontSize = 8
chartingLegendLocation = 2 # See https://matplotlib.org/api/legend_api.html for definitions
chartingLegendFontSize = 8
chartingGlobalFontSize = 8
chartingXAxisSeries = 'timestamp'

groupids = ['abc123abc123']

# Image web server settings
imgserverFolder = 'images'
imgserverUrl = 'http://localhost'

# Other Settings
defaultSources = ['opsmgr']
snarkyReplies = ["Sorry, I can't do that, Hal!", \
                  "I do not understand that request.", \
                  "Watchu talkin' about Willis?", \
                  "Can you re-phrase that in the form of a question?", \
                  "I'm confused - please try again and type slowly so I can understand!", \
                  "I just don't understand what you're asking of me.  Maybe you should ask in a different way.", \
                  "Uhhhhh - no, I don't think so.", \
                  "Does not compute - initiating self-destruct sequence in 3 - 2 - 1...."]


# Alert Blackout settings
# Do not change these next two items unless new ones are added on future Ops Manager versions.
alertsToBlackOutHostAlerts = ['HOST_DOWN', 'HOST_RECOVERING', 'VERSION_BEHIND', 'HOST_EXPOSED', 'OUTSIDE_METRIC_THRESHOLD']
alertsToBlackOutRplSetAlerts = ['CONFIGURATION_CHANGED', 'PRIMARY_ELECTED', 'TOO_FEW_HEALTHY_MEMBERS', 'TOO_MANY_UNHEALTHY_MEMBERS', 'NO_PRIMARY']
# Change the ones below for your deployment and preferences
alertsToBlackOut = ['HOST_DOWN', 'PRIMARY_ELECTED', 'NO_PRIMARY']
alertGroupsToBlackOut = ['Test', 'Manual', 'SenSei2']
alertAutoUnBlackoutTimeMins = 100 #1440
alertAutoUnBlackoutWarnTimeMins = 10
alertBlackoutHealthCheckTimeMins = 1440
alertBlackoutHealthCheckMinOplogWindowHours = 12
alertBlackoutMongoURI = 'mongodb://mike:password@node1.vagrant.local:27017,node2.vagrant.local:27017,node3.vagrant.local:27017/admin'
alertBlackoutMongoDB = 'MongoBotAlerts'
alertBlackoutMongoCollection = 'AlertBlackouts'
alertDeamonIntervalMinutes = 5

# Set up each OpsMgr instance here with a url, user, and apiKey
alertBlackoutOMList = [{'url' : 'http://opsmgr.vagrant.local:8080', 'user' : 'admin@localhost.com', 'apiKey' : 'abc123abc123' }]


## Ping / currentOp settings


mmsadminOMList = [{'mmsuser': '','mmscred':'', 'mmshost':'opsmgr.vagrant.local:37017'}]