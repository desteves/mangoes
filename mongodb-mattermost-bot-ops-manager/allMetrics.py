import settings
import utils
import json
import datetime

mreturn = 'OP_EXECUTION_TIME_TOTAL'

sumVals = {}
sumVals['OP_EXECUTION_TIME_TOTAL'] = ['AVG_WRITE_EXECUTION_TIME',
                       'AVG_COMMAND_EXECUTION_TIME',
                       'OP_EXECUTION_TIME_READS',
                       'OP_EXECUTION_TIME_WRITES',
                       'OP_EXECUTION_TIME_COMMANDS'
                       ]

resp = utils.getOpsMgrMetrics([],
                              '5a53ccb9a7ca7513f7ed9dfe',
                              '6501a70de7282a24e18219468f35d028',
                              granularity='PT1M',
                              period=None,
                              startTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=7),
                              endTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=2),
                            )

tm = utils.transformMetrics(resp)
sm = utils.scrubMetrics(tm, removeBlowThreshhold=-9999.0)

summed = None
if mreturn in sumVals:
    summed = summedMetrics = utils.sumMetrics(sm, sumVals)

# Return the metric we asked for only - search thru both
rm = {}
if mreturn in sm:
    rm[settings.chartingXAxisSeries] = sm[settings.chartingXAxisSeries]
    rm[mreturn] = sm[mreturn]
elif mreturn in sumVals and mreturn in summed:
    rm[settings.chartingXAxisSeries] = summed[settings.chartingXAxisSeries]
    rm[mreturn] = summed[mreturn]

print(rm)