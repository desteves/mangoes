#!/bin/sh 

# #############################################################################
echo "mtools/grep commands for mongod log analyses"
# #############################################################################

echo "mongotop - Get the read and write in ms for a given collection and exclude those that take less than 10ms"
cat  mongotop.tee.out | grep  'collection' |  awk '{$1=$1}1' | grep -v "[0-9]ms [0-9]ms [0-9]ms" | cut -f3- -d' '

# #############################################################################

echo "mlogfilter - with date range, default use UTC dates"
export FILEIN=mongodb.log
export FILEOUT=m.log
cat $FILEIN | mlogfilter --from  "2018-02-28T15:32" --to "2018-02-28T15:38" >$FILEOUT

# #############################################################################
echo "identify top IPs that opened connections against the given mongod"

echo "count       ip"
cat mongodb.log | grep "connection accepted from" | cut -d\  -f9 | cut -d':' -f 1 | sort| uniq -c | sort -nr

echo "for specific date and restricting the ip"
grep '^2017-12' mongod.log |   grep -o 'connection accepted from [.0-9]*' | sort | uniq -c | sort -rn

echo "using mloginfo"
mloginfo --connstats mongod.log

# #############################################################################

echo "mplotqueries - visualize the connchurn rate"
mplotqueries mongodb.log --type connchurn

# #############################################################################

echo "identify slowest queries"
grep '[0-9]ms$' mongod.log |   sed 's/^.*\s\([0-9]*\)ms$/\1 \0/'| sort -rn |   sed 's/^[0-9]* //' | head -n 20

grep ' [0-9]\{3,\}ms$' mongod.log |awk '{t = $1; $1 = $NF;$2 = t;  print}' | sort -rn | head -10

# #############################################################################

echo "look for collection scans"
for f in $(ls mongod.log*); do echo $f; grep COLLSCAN $f | grep -v 'oplog.rs' | wc -l; done
grep COLLSCAN mongod.log* | egrep -v 'oplog.rs' | awk '{print $6}' | sort | uniq

# #############################################################################

mlogfilter <logfile.log> --from Jul DD H:MM | head -(how many to see)
mlogfilter <logfile.log> --from "start +1h" | head -(how many to see)
mlogfilter <logfile.log> --from Date --to "+1h" | head -(how many to see)

### grepping log files
grep  '(.... connections now open' mongod.log | less
grep -v oplog mongod.log  | grep -o "[0-9]\+ms" | sort -n | tail
	1006369ms
	1006369ms
	1006369ms
	1006369ms

grep 1006369ms mongod.log

egrep '[0-9]{3,}ms$' mongod.log | awk '{print $NF, $0}' | sort -n | tail -n 5
egrep '[0-9]{3,}ms$' mongod.log | grep -iv getlasterror | awk '{print $NF, $0}' | sort -n | tail -n 5
egrep '[0-9]{3,}ms$' mongod.log | grep orderby | awk '{print $NF, $0}' | sort -n | tail -n 5
egrep '[0-9]{3,}ms$' mongod.log | grep orderby | awk '{print $NF, $0}' | sort -n | head -n 5


# #############################################################################
