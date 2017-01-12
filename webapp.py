#!/usr/bin/env python

from __future__ import print_function

import multiprocessing

import gunicorn.app.base
from gunicorn.six import iteritems

import os, sys
from os.path import basename
import re
import shutil
import tempfile
import pyferret
from paste.request import parse_formvars
import subprocess

from jinja2 import Template
import itertools
from PIL import Image

from flask import Flask, render_template, make_response, request, Response, session, url_for
from flask_script import Manager
from flask_bootstrap import Bootstrap

from flask import g

# For bokeh plots
import pandas as pd
import bokeh #0.12.3
from bokeh.plotting import figure, ColumnDataSource
from bokeh.resources import CDN
from bokeh.embed import file_html, components
from datetime import datetime as dt
from bokeh.models import DatetimeTickFormatter
from bokeh.models import HoverTool, BoxAnnotation
from math import pi

#==============================================================
app = Flask(__name__)

manager = Manager(app)
bootstrap = Bootstrap(app)


#============================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


#============================================
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#============================================
@app.route('/')
def index():
    return render_template('index.html')

#============================================
@app.route('/help')
def help():
    return render_template('help.html')

#============================================
@app.route('/contributors')
def contributors():
    return render_template('contributors.html')

#============================================
@app.route('/data')
def data():

    nbMaps = 4   #len(cmdArray)
    listSynchroMapsToSet = list(itertools.permutations(range(1,nbMaps+1), 2)) 
       
    session['cart'] = [1,2,3,4]

    print("request.method in /maps !!!!!!!!!!!: ", request.method)
    print("request.args: ", request.args)
    

    if request.args.get('REQUEST') == 'calcTimeseries':
        print("request.args in ts: ", request.args)
        ts_flag = 'true'        
        XTRANS = str(request.args.get('XTRANS')) # [xlim1:xlim2]
        YTRANS = str(request.args.get('YTRANS')) # [ylim1:ylim2]

        XTRANS = XTRANS + "@ave"
        YTRANS = YTRANS + "@ave"
        print("XTRANS: ", XTRANS) #XTRANS = '51.33:-131.48'
        print("YTRANS: ", YTRANS) #YTRANS = '-45.7:45.7'
        # VAR = request.args.get('VAR')

        # for testing only
        VAR = 'THETAO'   #'temp'
        # dset = 'levitus_climatology'
        # pyferret.run('use ' + dset)

        #Bokeh plot code
        #=======================================================
        # pyferret.start(journal=False, unmapped=True, quiet=True, verify=False)

        dset = 'thetao_Oyr_ALL_historical_r1i1p1_1870-2005.nc'

        # # pyferret.run("use /prodigfs/project/CARBON/CRESCENDO/thetao_Oyr_ALL_historical_r1i1p1_1870-2005.nc")
        # pyferret.run("use thetao_Oclim_ALL_piControl_r1i1p1_1990-1999.nc")
        # pyferret.run("let var=" + VAR + "[k=1,m=1,x=" + XTRANS + ",y=" + YTRANS + "]")

        # tmpfile = tempfile.NamedTemporaryFile(suffix='.csv').name

        # pyferret.run("spawn echo 'date,'" + VAR + " > " + tmpfile)
        # pyferret.run("list/quiet/nohead/norowlab/precision=7/format=\"comma\"/file=\"" + tmpfile + "\"/append TAX_DATESTRING(t[g=var],var,\"mon\"), var")

        # pyferret.stop()

        # #=======================================================
        # os.environ[ 'MPLCONFIGDIR' ] = '/tmp/'

        # df = pd.read_csv(tmpfile)
        #TEMPORARY, FOR ME
        tmpname = 'teststressors.csv'
        df = pd.read_csv('/home/users/cnangini/teststressors.csv')

        df['date'] = pd.to_datetime(df['date'], format='%b-%Y')  # convert ferret dates as datetimes
        # COMMENT OUT FOR ME df = df.set_index('date')

        # ### Plot with bokeh
        colors = ["#8c564b","#1f77b4","#2ca02c","#d62728","#9467bd","#e377c2","#7f7f7f","#bcbd22","#17bec"]

        dfer = pd.DataFrame()
        dfer['xval'] = df.ix[:, 0]
        dfer['yval'] = df.ix[:, 1]

        # Bokeh plot
        title='Average timeseries for ' + dset + ' (x: ' + XTRANS + ', y: ' + YTRANS + ')'
        p = figure(title=title,
                    plot_width=700,plot_height=400)
        p.line(dfer['xval'], dfer['yval'])

        # format axes        
        p.xaxis.formatter=DatetimeTickFormatter(formats=dict(
            hours=["%d %B %Y"],
            days=["%d %B %Y"],
            months=["%d %B %Y"],
            years=["%d %B %Y"],
        ))
        p.xaxis.major_label_orientation = pi/4
        p.yaxis.axis_label = "avg " + VAR

        # create the HTML elements to pass to template
        figJS,figDiv = components(p,CDN)
   

        # Render to new page
        return (render_template('tmp_ts.html',
            nbMaps=nbMaps, cmdArray=session['cart'],
            listSynchroMapsToSet=listSynchroMapsToSet,
            ts_flag=ts_flag,
            y=dfer['yval'],
            figJS=figJS,figDiv=figDiv,
            tmpname=tmpname
        ))
            
    
    return render_template('data.html', nbMaps=nbMaps, cmdArray=session['cart'], 
                            listSynchroMapsToSet=listSynchroMapsToSet)

@app.route('/ts_dialog', methods = ['GET'])
def api_tsdialog():

    print("request.method in /dialog !!!!!!!!!!!: ", request.method)
    print("request.args: ", request.args)

    if request.args.get('REQUEST') == 'calcTimeseries':
        print("request.args in dialog: ", request.args)
              
        XTRANS = str(request.args.get('XTRANS')) # [xlim1:xlim2]
        YTRANS = str(request.args.get('YTRANS')) # [ylim1:ylim2]

        XTRANS = XTRANS + "@ave"
        YTRANS = YTRANS + "@ave"
        print("XTRANS: ", XTRANS) #XTRANS = '51.33:-131.48'
        print("YTRANS: ", YTRANS) #YTRANS = '-45.7:45.7'
        VAR = request.args.get('VAR')
        print("VAR: ", VAR)

        # for testing only
        VAR = 'THETAO'   #'temp'
       
        #Bokeh plot code
        #=======================================================
        # pyferret.start(journal=False, unmapped=True, quiet=True, verify=False)

        dset = 'thetao_Oyr_ALL_historical_r1i1p1_1870-2005.nc'

        # # pyferret.run("use /prodigfs/project/CARBON/CRESCENDO/thetao_Oyr_ALL_historical_r1i1p1_1870-2005.nc")
        # pyferret.run("use thetao_Oclim_ALL_piControl_r1i1p1_1990-1999.nc")
        # pyferret.run("let var=" + VAR + "[k=1,m=1,x=" + XTRANS + ",y=" + YTRANS + "]")

        # tmpfile = tempfile.NamedTemporaryFile(suffix='.csv').name

        # pyferret.run("spawn echo 'date,'" + VAR + " > " + tmpfile)
        # pyferret.run("list/quiet/nohead/norowlab/precision=7/format=\"comma\"/file=\"" + tmpfile + "\"/append TAX_DATESTRING(t[g=var],var,\"mon\"), var")

        # pyferret.stop()

        # #=======================================================
        # os.environ[ 'MPLCONFIGDIR' ] = '/tmp/'

        # df = pd.read_csv(tmpfile)
        #TEMPORARY, FOR ME
        tmpname = 'teststressors.csv'
        df = pd.read_csv('/home/users/cnangini/teststressors.csv')

        df['date'] = pd.to_datetime(df['date'], format='%b-%Y')  # convert ferret dates as datetimes
        # COMMENT OUT FOR ME df = df.set_index('date')

        # ### Plot with bokeh
        colors = ["#8c564b","#1f77b4","#2ca02c","#d62728","#9467bd","#e377c2","#7f7f7f","#bcbd22","#17bec"]

        dfer = pd.DataFrame()
        dfer['xval'] = df.ix[:, 0]
        dfer['yval'] = df.ix[:, 1]

        # Save to csv in tmpdir
        fname = tempfile.NamedTemporaryFile(suffix='.csv').name
        dfer.to_csv(fname, sep='\t')
        os.rename(fname, tmpdir + "/" + basename(fname))
        print("saved to ", tmpdir + "/" + basename(fname))

        # Bokeh plot        
        title='Model-mean timeseries for ' + VAR + ' over [X: ' + XTRANS.split('@ave')[0] + ', Y: ' + YTRANS.split('@ave')[0] + '] relative to 1990-1999'
        p = figure(title=title,
                    plot_width=700,
                    plot_height=400)
        p.line(dfer['xval'], dfer['yval'])

        # format axes        
        p.xaxis.formatter=DatetimeTickFormatter(formats=dict(
            hours=["%d %B %Y"],
            days=["%d %B %Y"],
            months=["%d %B %Y"],
            years=["%d %B %Y"],
        ))
        p.xaxis.major_label_orientation = pi/4
        p.yaxis.axis_label = "avg " + VAR

        # create the HTML elements to pass to dialog
        figJS,figDiv = components(p,CDN)

        # buttonString = "<button class='btn btn-default' id=\"Download\">Download</button>"
        buttonString = '<a href="/download?&REQUEST=SaveTimeseries&FILENAME=' + basename(fname) + '"><button class="btn btn-default">Download</button></a>'
        print("buttonString: ", buttonString)

        return figJS + figDiv + buttonString


def after_this_request(f):
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f



@app.route('/download')
def download_ts():
    print("request.args in download_ts: ", request.args)

    if request.args.get('REQUEST') == 'SaveTimeseries':
        
        fname = request.args.get('FILENAME')

        ftmp = open(tmpdir + '/' + fname, 'rb')
        ts_csv = ftmp.read()
        ftmp.close()

        # WIP
        # @after_this_request
        # def remove_file(response):
        #     try:
        #         os.remove(tmpdir + "/" + fname)
        #     except Exception as error:
        #         app.logger.error("Error removing or closing downloaded file handle", error)
        #     return response

                
        return Response(
            ts_csv,
            mimetype="text/csv",
            headers={"Content-disposition":
                     "attachment; filename=timeseries.csv"}
            )

#==============================================================
def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1

#==============================================================
class myArbiter(gunicorn.arbiter.Arbiter):

    def halt(self):
	# Close pyferret
        pyferret.stop()

        print("current wdir before exit: ", os.getcwd())

    	print('Removing temporary directory: ', tmpdir)
    	shutil.rmtree(tmpdir)

        super(myArbiter, self).halt()


#==============================================================
class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):

	    # Start pyferret	
        pyferret.start(journal=False, unmapped=True, quiet=True, verify=False)

    	master_pid = os.getpid()
    	print('---------> gunicorn master pid: ', master_pid)    

        self.options = options or {}
        self.application = app

        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

# if control before exiting is needed
    def run(self):
        try:
            myArbiter(self).run()
        except RuntimeError as e:
            print('\nError: %s\n' % e, file=sys.stderr)
            sys.stderr.flush()
	    sys.exit(1)


#==============================================================
from optparse import OptionParser

#------------------------------------------------------
usage = "%prog [--env=script.jnl] [--width=400] [--height=400] [--size=value] [--center=[0,0]] [--zoom=1] [--server]" + \
	"\n                              'cmd/qualifiers variable; cmd/qualifiers variable'" + \
	"\n\n'cmd/qualifiers variable' is a classic ferret call (no space allowed except to" + \
	"\nseparate the variable from the command and its qualifiers). The semi-colon character ';'" +\
	"\nis the separator between commands and will determine the number of maps to be drawn." + \
	"\nThe qualifiers can include the title qualifier considering that the space character" + \
	"\nis not allowed since used to distinguish the cmd/qualifiers and the variable(s)." + \
	"\nFor this, you can use the HTML code '&nbsp' for the non-breaking space (without the ending semi-colon)." + \
	"\nFor example: 'shade/lev=20/title=Simulation&nbspA varA; shade/lev=20/title=Simulation&nbspB varB'"

version = "%prog 0.9.5"

#------------------------------------------------------
parser = OptionParser(usage=usage, version=version)

parser.add_option("--width", type="int", dest="width", default=400,
		help="200 < map width <= 600")
parser.add_option("--height", type="int", dest="height", default=400,
		help="200 < map height <= 600")
parser.add_option("--size", type="int", dest="size",
		help="200 < map height and width <= 600")
parser.add_option("--env", dest="envScript", default="pyferretWMS1.jnl",
		help="ferret script to set the environment (default=pyferretWMS1.jnl). It contains datasets to open, variables definition.")
parser.add_option("--center", type="string", dest="center", default='[0,-40]',
		help="Initial center of maps as [lat, lon] (default=[0,-40])")
parser.add_option("--zoom", type="int", dest="zoom", default=1,
		help="Initial zoom of maps (default=1)")
parser.add_option("--server", dest="serverOnly", action="store_true", default=False,
		help="Server only (default=False)")

(options, args) = parser.parse_args()
print("options, args: ", parser.parse_args() )

if options.size:
	mapHeight = options.size
	mapWidth = options.size
else:
	mapHeight = options.height
	mapWidth = options.width

mapCenter = options.center
mapZoom = options.zoom
envScript = options.envScript
serverOnly = options.serverOnly

#------------------------------------------------------
# Global variables
nbMaps = 0
cmdArray = []
tmpdir = []
tmpdir = tempfile.mkdtemp()
print('Temporary directory to remove: ', tmpdir)

#------------------------------------------------------
if serverOnly:
	if len(args) != 0:
        	parser.error("No argument needed in mode server")
		parser.print_help()

#------------------------------------------------------
options = {
    'bind': '%s:%s' % ('127.0.0.1', '8000'),
    'workers': number_of_workers(),
    'worker_class': 'sync',
    'threads': 1 
}

StandaloneApplication(app, options).run()

sys.exit(1)