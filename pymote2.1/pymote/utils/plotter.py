#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is supporting material for the book
# Building Machine Learning Systems with Python
# by Willi Richert and Luis Pedro Coelho
# published by PACKT Publishing
#
# It is made available under the MIT License

import os
import json
import scipy as sp
import matplotlib.pyplot as plt

from pymote.logger import logger
from pymote.utils.filing import get_path


# plot input data
def plots(x, y, fname, ymax=None, xmin=None, ymin=None,
          xlabel="X", ylabel="Y", title=None, labels="", more_plots=None, format='pdf',  **kwargs):

    title = title or fname
    colors = ['g', 'k', 'b', 'm', 'r', 'c']
    line_styles = ['o-', '-.', '--', 'o:', 'x-']
    styles = ['go-', 'k-.', 'm.-', 'bx:', 'g.:', 'ro--']
    plt.figure(num=None, figsize=(9, 6))
    plt.clf()

    if more_plots and isinstance(more_plots, list):
        more_plots.insert(0, y)
        for yy in more_plots:
            #plt.plot(x, yy, linestyle=line_styles.pop(), linewidth=1, c=colors.pop())
            try:
                sty = styles.pop()
            except:
                sty = styles[0]

            plt.plot(x, yy, sty)
            #plt.plot(x, yy)
            #plt.scatter(x, yy, s=10)
        plt.legend(["%s" % m for m in labels], loc="upper left")
    else:
        plt.plot(x, y)
        plt.scatter(x, y, s=10)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    plt.autoscale(tight=True)
    if ymin:
        plt.ylim(ymin=ymin)
    if ymax:
        plt.ylim(ymax=ymax)
    if xmin:
        plt.xlim(xmin=xmin)

    plt.grid(True, linestyle='-', color='0.75')
    #plt.show()
    if 'pdf' in format:
        from matplotlib.backends.backend_pdf import PdfPages
        with PdfPages(fname+".pdf") as pdf:
            pdf.savefig(transparent=True)
            d = pdf.infodict()
            d['Title'] = title or kwargs.pop('title', fname)
            d['Author'] = kwargs.pop('author', 'Farrukh Shahzad')
            d['Subject'] = kwargs.pop('subject','PhD Dissertation Dec 2015 - KFUPM')
    else:
        plt.savefig(fname+'.'+format, format=format, transparent=True)


# plot bars input data
def plot_bars(x, y, fname, ymax=None, xmin=None, ymin=None,
          xlabel="X", ylabel="Y", title=None, color='r', format='pdf',  **kwargs):

    title = title or fname
    plt.figure(num=None, figsize=(9, 6))
    plt.clf()
    #plt.scatter(x, y, s=10)
    width = 0.5
    plt.bar(x-width/2, y, width, color=color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    plt.autoscale(tight=True)
    if ymin:
        plt.ylim(ymin=ymin)
    if ymax:
        plt.ylim(ymax=ymax)
    if xmin:
        plt.xlim(xmin=xmin)

    plt.grid(True, linestyle='-', color='0.75')
    #plt.show()
    if 'pdf' in format:
        from matplotlib.backends.backend_pdf import PdfPages
        with PdfPages(fname+".pdf") as pdf:
            pdf.savefig()
            d = pdf.infodict()
            d['Title'] = title or kwargs.pop('title', fname)
            d['Author'] = kwargs.pop('author', 'Farrukh Shahzad')
            d['Subject'] = kwargs.pop('subject','PhD Dissertation Dec 2015 - KFUPM')
    else:
        plt.savefig(fname+'.'+format, format=format, transparent=True)


def gethtmlLine(x, y, fname, folder="", axis_range={}, labels=None,
          xlabel="X", ylabel="Y", title=None, color='r', comment=".", **kwargs):

    title =  title or fname
    plot_type = 'spline'
    if 'plot_type' in kwargs:
        plot_type = kwargs.pop('plot_type', 'line')

    plot_options = [""]
    if 'plot_options' in kwargs:
        plot_options = kwargs.pop('plot_options')

    show_range = kwargs.pop('show_range', None)
    circle = ""
    if show_range:
        circle = "allowPointSelect:true, marker: {states: {select: {lineColor: 'red', radius: " + str(show_range) + "}}},"
    series_data = ''
    k = 0
    for series in y:
        series_data += '''
        {
            name: "''' + (labels[k] if k < len(labels) else "") + '''",
            ''' + (plot_options[k] if k < len(plot_options) else "") + '''
            data: ''' + str(series) + ''',
            ''' + circle + '''
        },
'''
        k += 1

    contents = '''<!DOCTYPE html>
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">
  <title>'''+title+'''</title>
  <script type='text/javascript' src='http://code.jquery.com/jquery-1.9.1.js'></script>
  <style type='text/css'>
  </style>

<script type='text/javascript'>//<![CDATA[

var chart;
var w;
$(function () {
    w = $('#container').width()
    $('#container').highcharts({
        credits: {
            enabled: false
        },
        exporting: {
            filename: "''' + fname + '''"
        },
        legend: {
            margin: -10, padding: 0, y: -5, //layout: 'vertical', align: 'right', verticalAlign: 'middle', shadow: true, backgroundColor: '#FFFFFF',
            title: {
                //text: 'Farrukh Shahzad<br/>PhD, KFUPM<br/>Nov. 2015</span>',
                style: {fontStyle: 'italic', fontSize: '10px'}
            }
        },
        chart: {
            zoomType: 'xy', panning: true, panKey: 'shift',
            type: "''' + plot_type + '''"
        },
        title: {
            text: "''' + title + '''"
        },
        subtitle: {
            text: "''' + comment + '''",
            style: {color:'black', fontSize: '18px', fontFamily: 'Times'}
        },
        tooltip: {
            borderRadius: 10,
            crosshairs: [{width: 1, color: 'gray',  dashStyle: 'shortdot'}, {width: 1, color: 'gray',  dashStyle: 'shortdot'}],
            pointFormat: '<span style="font-weight: bold; color: {series.color}">{series.name}</span>: <b>{point.y:.1f}</b><br />',
            headerFormat: '<span style="font-size: 12px">''' + xlabel + ''' {point.key}</span><br />',
            shared: true
        },
        xAxis: { // Primary xAxis
            minRange : 5,
            min: '''+ json.dumps(axis_range.get('xmin')) + ''', max: '''+ json.dumps(axis_range.get('xmax')) + ''',
            title: {text: "'''+ xlabel + '''", y: -10, style: {color:'black'}}
        },
        yAxis: { // Primary yAxis
            lineWidth: 1,
            minPadding: 0.0,
            maxPadding: 0.0,
            min: '''+ json.dumps(axis_range.get('ymin')) + ''', max: '''+ json.dumps(axis_range.get('ymax')) + ''',
            title: {text: "'''+ ylabel + '''", x: 10, style: {color:'black'}}
        },
        series: [''' + series_data + ''']
    });
});
//]]>

</script>

</head>
<body>
<script src="http://code.highcharts.com/highcharts.js"></script>
<script src="http://code.highcharts.com/modules/data.js"></script>
<script src="http://code.highcharts.com/highcharts-more.js"></script>
<script src="http://code.highcharts.com/modules/exporting.js"></script>

<div id="container" style="height: 600px; margin: auto; min-width: 600px; max-width: 600px"></div>
</body>
</html>
'''

    path = get_path(folder,fname) + ".html"
    if 'open' in kwargs:
        browseLocal(contents, filename=path)
    else:
        strToFile(contents, filename=path)


def gethtmlScatter(x, y, fname, folder="", axis_range={}, labels=None,
          xlabel="X", ylabel="Y", title=None, comment=".", **kwargs):

    w = 100
    h = 100
    title = title or fname
    report = kwargs.pop('report', comment)
    plot_type = 'scatter'
    if 'plot_type' in kwargs:
        plot_type = kwargs.pop('plot_type')

    plot_options = [""]
    if 'plot_options' in kwargs:
        plot_options = kwargs.pop('plot_options')

    show_range = kwargs.pop('show_range', 0)
    circle = ""
    if show_range:
        circle = "allowPointSelect:true, marker: { states: { select: { lineColor: 'red', radius: " + str(show_range) + "}}},"

    series_data = ""
    series_line = ""
    k=0
    if len(y)>10:
       series_data += '''
            {
                name: "''' + (labels[k] if k < len(labels) else "") + '''",
                ''' + (plot_options[k] if k < len(plot_options) else "") + '''
                data: ''' + str(y) + ''',
                ''' + circle + '''
            },
    '''
    else:
        k=0
        for series in y:
            series_data += '''
            {
                name: "''' + (labels[k] if k < len(labels) else "") + '''",
                ''' + (plot_options[k] if k < len(plot_options) else "") + '''
                data: ''' + str(series) + ''',
                ''' + circle + '''
            },
    '''
            k += 1

        if k > 1:
            j = 0
            for yy in y[1]:
                try:
                    #print yy['name'], y[1][j]['name']
                    if yy['name'] == y[2][j]['name']:
                        yyx, yyy = yy['x'], yy['y']
                        yyx2, yyy2 = y[2][j]['x'], y[2][j]['y']
                        yyx2 = w + 3 if yyx2 > w + 3 else yyx2
                        yyx2 = -3 if yyx2 < -3 else yyx2
                        yyy2 = h + 3 if yyy2 > h+3 else yyy2
                        yyy2 = -3 if yyy2 < -3 else yyy2

                        series_line += "chart.renderer.path(['M', chart.xAxis[0].toPixels(" + str(yyx) + \
                                   "), chart.yAxis[0].toPixels(" + str(yyy) + \
                                   "), 'L', chart.xAxis[0].toPixels(" + str(yyx2) + \
                                   "), chart.yAxis[0].toPixels(" + str(yyy2) + \
                                   ")]).attr({'stroke-width': 1, stroke: 'gray'}).add(group);"
                        j += 1
                except (ValueError, Exception) as exc:
                    print exc
                    break



    contents = '''<!DOCTYPE html>
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">
  <title>'''+title+'''</title>
  <script type='text/javascript' src='http://code.jquery.com/jquery-1.9.1.js'></script>
  <style type='text/css'>
  </style>

<script type='text/javascript'>//<![CDATA[

var chart;
var w;
$(function () {
    var group;
    vis = true;
    w = $('#container').width()
    $('#container').highcharts({
        credits: {
            enabled: false
        },
        exporting: {
            filename: "''' + fname + '''"
        },
        legend: {
            margin: -5, padding: 0, y: -5, //layout: 'vertical', align: 'right', verticalAlign: 'middle', shadow: true, backgroundColor: '#FFFFFF',
            title: {
                //text: 'Farrukh Shahzad<br/>PhD, KFUPM<br/>Nov. 2015</span>',
                style: {fontStyle: 'italic', fontSize: '10px'}
            }
        },
        chart: {
            zoomType: 'xy', panning: true, panKey: 'shift',
            type: "''' + plot_type + '''"
        },
        title: {
            text: "''' + title + '''"
        },
        subtitle: {
            text: "''' + comment + '''",
            style: {color:'black', fontSize: '18px', fontFamily: 'Times'}
        },
        tooltip: {
            borderRadius: 10,
            crosshairs: [{width: 1, color: 'gray',  dashStyle: 'shortdot'}, {width: 1, color: 'gray',  dashStyle: 'shortdot'}],
            pointFormat: 'X: {point.x:.1f}, Y: {point.y:.1f}',
            headerFormat: '<b>Node: {point.key}</b>, {series.name}<br />',
            shared: true
        },
        xAxis: [{ // Primary xAxis
            //minRange : 5,
            gridLineWidth: 1,
            min: '''+ json.dumps(axis_range.get('xmin')) + ''', max: '''+ json.dumps(axis_range.get('xmax')) + ''',
            title: { text: "'''+ xlabel + '''", y: -5, style: {color:'black'}}
        }],
        yAxis: [{ // Primary yAxis
            lineWidth: 1,
            minPadding: 0.0,
            maxPadding: 0.0,
            min: '''+ json.dumps(axis_range.get('ymin')) + ''', max: '''+ json.dumps(axis_range.get('ymax')) + ''',
            title: {text: "'''+ ylabel + '''", x: 5, style: {color:'black'}}
        }],
        series: [''' + series_data + ''' ]
    },
    function (chart) { // on complete
        group = chart.renderer.g().add();
    '''+ series_line + '''
    });''' + \
    ("$('#button').click(function () {if (vis) group.hide(); else group.show(); vis = !vis; });" if len(series_line)>1 else "") + \
'''
});
//]]>

</script>

</head>
<body>
<script src="http://code.highcharts.com/highcharts.js"></script>
<script src="http://code.highcharts.com/modules/data.js"></script>
<script src="http://code.highcharts.com/highcharts-more.js"></script>
<script src="http://code.highcharts.com/modules/exporting.js"></script>

<table border="0" align="center"><tr><td align="center">
<span id="container" style="height: 600px; margin: auto; min-width: 600px; max-width: 600px"></span>
''' + ("<button id='button'>Toggle Error Lines</button>" if len(series_line)>1 else "") + \
'''</td><td style="font-family: 'Lucida Console'; font-size: 12px; height: 600px; padding: 25px; max-width: 500px">
<span id="report" ><h3>''' + title + '''</h3>''' + \
               report + '''<br><br>Click on the legend on the bottom to hide/show series</span>
</td></tr></table>
</body>
</html>
'''
    path = get_path(folder,fname) + ".html"
    if 'open' in kwargs:
        browseLocal(contents, filename=path)
    else:
        strToFile(contents, filename=path)


def gethtmlmultiplots(x, y, fname, folder="", axis_range={}, labels=None,
          xlabel="X", ylabel="Y", title=None, comment=".", **kwargs):

    w = 100
    h = 100
    title = title or fname
    report = kwargs.pop('report', comment)
    plot_type = 'scatter'
    if 'plot_type' in kwargs:
        plot_type = kwargs.pop('plot_type')

    plot_options = [""]
    if 'plot_options' in kwargs:
        plot_options = kwargs.pop('plot_options')

    series_data = ""
    k=0
    if len(y)>10:
       series_data += '''
            {
                name: "''' + (labels[k] if k < len(labels) else "") + '''",
                ''' + (plot_options[k] if k < len(plot_options) else "") + '''
                data: ''' + str(y) + ''',
            },
    '''
    else:
        for series in y:
            series_data += '''
            {
                name: "''' + (labels[k] if k < len(labels) else "") + '''",
                ''' + (plot_options[k] if k < len(plot_options) else "") + '''
                data: ''' + str(series) + ''',
            },
    '''
            k += 1

    contents = '''<!DOCTYPE html>
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">
  <title>'''+title+'''</title>
  <script type='text/javascript' src='http://code.jquery.com/jquery-1.9.1.js'></script>
  <style type='text/css'>
  </style>

<script type='text/javascript'>//<![CDATA[

var chart;
var w;
$(function () {
    var group;
    vis = true;
    w = $('#container').width()
    $('#container').highcharts({
        credits: {
            enabled: false
        },
        exporting: {
            filename: "''' + fname + '''"
        },
        legend: {
            margin: -5, padding: 0, y: -5, //layout: 'vertical', align: 'right', verticalAlign: 'middle', shadow: true, backgroundColor: '#FFFFFF',
            title: {
                //text: 'Farrukh Shahzad<br/>PhD, KFUPM<br/>Nov. 2015</span>',
                style: {fontStyle: 'italic', fontSize: '10px'}
            }
        },
        chart: {
            zoomType: 'xy', panning: true, panKey: 'shift',
            type: "''' + plot_type + '''"
        },
        title: {
            text: "''' + title + '''"
        },
        subtitle: {
            text: "''' + comment + '''",
            style: {color:'black', fontSize: '18px', fontFamily: 'Times'}
        },
        tooltip: {
            borderRadius: 10,
            crosshairs: [{width: 1, color: 'gray',  dashStyle: 'shortdot'}, {width: 1, color: 'gray',  dashStyle: 'shortdot'}],
            pointFormat: '{point.x:.1f}, {point.y:.1f}',
            headerFormat: '<b>{series.name}</b><br />',
            shared: true
        },
        xAxis: [{ // Primary xAxis
            gridLineWidth: 1,
            min: '''+ json.dumps(axis_range.get('xmin')) + ''', max: '''+ json.dumps(axis_range.get('xmax')) + ''',
            title: { text: "'''+ xlabel + '''", y: -5, style: {color:'black'}}
        }],
        yAxis: [{ // Primary yAxis
            lineWidth: 1,
            minPadding: 0.0,
            maxPadding: 0.0,
            min: '''+ json.dumps(axis_range.get('ymin')) + ''', max: '''+ json.dumps(axis_range.get('ymax')) + ''',
            title: {text: "'''+ ylabel + '''", x: 5, style: {color:'black'}}
        }],
        series: [''' + series_data + ''' ]
    })
});
//]]>

</script>

</head>
<body>
<script src="http://code.highcharts.com/highcharts.js"></script>
<script src="http://code.highcharts.com/modules/data.js"></script>
<script src="http://code.highcharts.com/highcharts-more.js"></script>
<script src="http://code.highcharts.com/modules/exporting.js"></script>

<table border="0" align="center"><tr><td align="center">
<span id="container" style="height: 600px; margin: auto; min-width: 600px; max-width: 600px"></span>
</td><td style="font-family: 'Lucida Console'; font-size: 12px; height: 600px; padding: 25px; max-width: 500px">
<span id="report" ><h3>''' + title + '''</h3>''' + \
               report + '''<br><br>Click on the legend on the bottom to hide/show series</span>
</td></tr></table>
</body>
</html>
'''
    path = get_path(folder,fname) + ".html"
    if 'open' in kwargs:
        browseLocal(contents, filename=path)
    else:
        strToFile(contents, filename=path)

def strToFile(text, filename):
    """Write a file with the given name and the given text."""
    output = open(filename,"w")
    output.write(text)
    output.close()


def browseLocal(webpageText='Test', filename='tempBrowseLocal.html'):
    '''Start your webbrowser on a local file containing the text
    with given filename.'''
    import webbrowser, os.path
    strToFile(webpageText, filename)
    webbrowser.open("file:///" + os.path.abspath(filename)) # elaborated for Mac


if __name__ == '__main__':
    plot_bars([1,2,3,4], [100,200,34,200], None, "test", title="Good Graph")