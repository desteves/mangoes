import sys
from datetime import datetime

# Example usage
# cat syslog | python convert_log_date.py > date_syslog

## FROM Apr 12 19:40:10
## TO 2017-04-12T19:40:10.000+0000
for line in sys.stdin:
    try:
        dts = line[:15]
        d = datetime.strptime(dts, '%b %d %H:%M:%S')
        print d.strftime("2017-%m-%dT%H:%M:%S.000+0000"), line[16:],
    except Exception as e:
        pass
