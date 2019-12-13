#!/bin/bash

HAS=$1
for f in `find . -name *${HAS}*`
do

   filename=`echo $f|awk -F'/' '{SL = NF-1; TL = NF-2; print $TL "_" $SL  "_" $NF}'`
   echo "Moving "   $f  " to " $filename
   mv $f $filename

done
