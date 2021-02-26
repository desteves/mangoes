#### Class to generate OpsMgr charts ####

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import settings
import utils
import time

# Generate chart - most of the values are contained in the settings
def genChart(chartId, chartData, title, seriesLabels, hilightedSeriesLabels = {}, showLegend = False, useLogScale = False, showGrid = True, scaleYAxis = True):
    fname = None
    if chartData is not None and 'errorCode' not in chartData:
        xplot = chartData[settings.chartingXAxisSeries]
        fig, ax = plt.subplots()

        # set global font size
        matplotlib.rcParams.update({'font.size':settings.chartingGlobalFontSize})

        # plot the regular series and labels
        i = 0
        for k in seriesLabels.keys():
            ax.plot(xplot, chartData[k], settings.chartingSeriesColors[i], label=seriesLabels[k])
            i += 1

        # plot the hi-lightes series and labels
        i = 0
        for k in hilightedSeriesLabels.keys():
            ax.plot(xplot, chartData[k], settings.chartingSeriesHighlightColors[i], label=hilightedSeriesLabels[k])
            i += 1

        # set up legend
        if showLegend:
            ax.legend(loc=settings.chartingLegendLocation, fontsize=settings.chartingLegendFontSize)
        else: # if no legend, put the 1st series title on the y axis instead
            plt.ylabel(list(seriesLabels.values())[0])

        # set scale to log if desired
        if useLogScale:
            plt.yscale('log')

        # set chart size and date format
        fig.autofmt_xdate()
        fig.set_size_inches(settings.chartingSizeWidthPx / settings.chartingDPI, settings.chartingSizeHieghtPx / settings.chartingDPI)
        myFmt = DateFormatter(settings.chartingDateFmt)
        ax.xaxis.set_major_formatter(myFmt)

        # show grid if needed
        if showGrid:
            ax.grid(color=settings.chartingGridColor)
            plt.grid(True)

        # Set Y Axis limit if desired
        if scaleYAxis:
            plt.ylim(0, utils.getYAxisLimit(chartData))

        # Set title and font size
        fig.suptitle(title, fontsize=settings.chartingTitleFontSize)

        # save file
        fname = settings.imgserverFolder + '/' + chartId + '_' + str(time.time()) + '_OpsMgr.png'
        plt.savefig(fname, dpi = settings.chartingDPI)
        plt.close()
    else:
        fname = chartData

    return fname

# Generate a connections chart
def genConnectionsChart(id, grp, host, title):
    f = None
    j = utils.getOpsMgrMetrics(['CONNECTIONS'], grp, host)
    # Transform and Scrub the metrics
    d = utils.scrubMetrics(utils.transformMetrics(j))
    # Generate OpsMgr chart
    if d is not None:
        f = genChart(id, d, title, {"CONNECTIONS": 'Connections'})
    return f

# Generate an op counter chart
def genOpsCounterChart(id, grp, host, title):
    f = None
    # Generate OpsMgr Op Counter chart
    j = utils.getOpsMgrMetrics(['OPCOUNTER_CMD', 'OPCOUNTER_QUERY', 'OPCOUNTER_UPDATE', 'OPCOUNTER_DELETE',
                                'OPCOUNTER_GETMORE', 'OPCOUNTER_INSERT', 'OPCOUNTER_REPL_CMD', 'OPCOUNTER_REPL_UPDATE',
                                'OPCOUNTER_REPL_DELETE', 'OPCOUNTER_REPL_INSERT'],
                                grp, host)
    # Transform, Sum, and Scrub the metrics
    sumVals = {}
    # sum up all the OPCOUNTER_xxx metrics as 'OpCounters'
    sumVals['OpCounters'] = ['OPCOUNTER_CMD', 'OPCOUNTER_QUERY', 'OPCOUNTER_UPDATE', 'OPCOUNTER_DELETE',
                               'OPCOUNTER_GETMORE', 'OPCOUNTER_INSERT']
    # sum up all the OPCOUNTER_REPL_xxx metrics as 'RplCounters'
    sumVals['RplCounters'] = ['OPCOUNTER_REPL_CMD', 'OPCOUNTER_REPL_UPDATE', 'OPCOUNTER_REPL_DELETE',
                               'OPCOUNTER_REPL_INSERT']
    # Tranform, Sum, and then Scrub the metrics
    d = utils.scrubMetrics(utils.sumMetrics(utils.transformMetrics(j), sumVals))
    # Generate a chart
    f = genChart(id, d, title,
                          {"OpCounters":'Ops/s', 'RplCounters':'Replication Ops/s'}, showLegend = True )
    return f

def genQueueChart(id, grp, host, title):
    f = None
    # Generate OpsMgr Queue chart
    j = utils.getOpsMgrMetrics(['GLOBAL_LOCK_CURRENT_QUEUE_TOTAL', 'GLOBAL_LOCK_CURRENT_QUEUE_READERS',
                                'GLOBAL_LOCK_CURRENT_QUEUE_WRITERS'], grp, host)
    # Transform, Sum, and Scrub the metrics
    sumVals = {}
    # Tranform, Sum, and then Scrub the metrics
    d = utils.scrubMetrics(utils.sumMetrics(utils.transformMetrics(j), sumVals))
    # Generate a chart
    f = genChart(id, d, title,
                          {'GLOBAL_LOCK_CURRENT_QUEUE_READERS':'Readers', 'GLOBAL_LOCK_CURRENT_QUEUE_WRITERS':'Writers'},
                          hilightedSeriesLabels = {'GLOBAL_LOCK_CURRENT_QUEUE_TOTAL':'Total'}, showLegend = True )
    return f

def genRplLagChart(id, grp, host, title):
    f = None
    j = utils.getOpsMgrMetrics(['OPLOG_SLAVE_LAG_MASTER_TIME'], grp, host)

    # Transform and Scrub the metrics
    d = utils.scrubMetrics(utils.transformMetrics(j))

    f = genChart(id, d, title, {'OPLOG_SLAVE_LAG_MASTER_TIME': 'Replication Lag'})
    return f


