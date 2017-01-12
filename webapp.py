#!/usr/bin/env python

from __future__ import print_function

import multiprocessing

import gunicorn.app.base
from gunicorn.six import iteritems

from flask import Flask, render_template, request, Response
from flask_bootstrap import Bootstrap

import os, sys
import shutil
import tempfile
import pyferret
import itertools

from PIL import Image

#==============================================================
app = Flask(__name__)
bootstrap = Bootstrap(app)

#--------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#--------------------------------------------------------------
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#--------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

#--------------------------------------------------------------
@app.route('/data')
def data():

    nbMaps = 4
    cmdArray = [1,2,3,4]
    listSynchroMapsToSet = list(itertools.permutations(range(1,nbMaps+1), 2))

    return render_template('data.html', nbMaps=nbMaps, cmdArray=cmdArray, listSynchroMapsToSet=listSynchroMapsToSet) 

#--------------------------------------------------------------
@app.route('/dataTest')
def dataTest():
    return render_template('dataTest.html')

#--------------------------------------------------------------
@app.route('/wmspyferret')
def wmspyferret():

    fields = request.args

    try:
            if fields['SERVICE'] != 'WMS':
                    raise

            COMMAND = fields['COMMAND']
            VARIABLE = fields['VARIABLE'].replace('%2B','+')

            pyferret.run('go envScript.jnl')

            try:
                    MASK = fields['MASK']
            except:
                    MASK = None

            tmpname = tempfile.NamedTemporaryFile(suffix='.png').name
            tmpname = os.path.basename(tmpname)

            #---------------------------------------------------------
            if fields['REQUEST'] == 'GetColorBar':
                    pyferret.run('set window/aspect=1/outline=0')
                    pyferret.run('go margins 2 4 3 3')
                    pyferret.run(str(COMMAND + '/set_up ' + VARIABLE))	# str used here to convert unicode
                    pyferret.run('ppl shakey 1, 0, 0.15, , 3, 9, 1, `($vp_width)-1`, 1, 1.25 ; ppl shade')
                    pyferret.run('frame/format=PNG/transparent/xpixels=400/file="' + tmpdir + '/key' + tmpname + '"')

                    im = Image.open(tmpdir + '/key' + tmpname)
                    box = (0, 325, 400, 375)
                    area = im.crop(box)
                    area.save(tmpdir + '/' + tmpname, "PNG")

            #---------------------------------------------------------
            elif fields['REQUEST'] == 'GetMap':
                    WIDTH = int(fields['WIDTH'])
                    HEIGHT = int(fields['HEIGHT'])

                    # BBOX=xmin,ymin,xmax,ymax
                    BBOX = fields['BBOX'].split(',')

                    HLIM = '/hlim=' + BBOX[0] + ':' + BBOX[2]
                    VLIM = '/vlim=' + BBOX[1] + ':' + BBOX[3]

                    pyferret.run('set window/aspect=1/outline=5')           # outline=5 is a strange setting but works otherwise get outline around polygons
                    pyferret.run('go margins 0 0 0 0')
                    pyferret.run(str(COMMAND +  '/noaxis/nolab/nokey' + HLIM + VLIM + ' ' + VARIABLE))  # str used here to convert unicode
                    pyferret.run('frame/format=PNG/transparent/xpixels=' + str(WIDTH) + '/file="' + tmpdir + '/' + tmpname + '"')

                    if os.path.isfile(tmpdir + '/' + tmpname):
                            if MASK:
                                    img = Image.open(tmpdir + '/' + tmpname)
                                    mask = Image.open(MASK)
                                    img = Image.composite(img, mask, mask)
                                    img.save(tmpdir + '/' + tmpname)

            #---------------------------------------------------------
            else:
                    raise

            if os.path.isfile(tmpdir + '/' + tmpname):
                    ftmp = open(tmpdir + '/' + tmpname, 'rb')
                    img = ftmp.read()
                    ftmp.close()
                    os.remove(tmpdir + '/' + tmpname)

	    resp = Response(iter(img), status=200, mimetype='image/png')
	    return resp

    except Exception, e:
	    return(str(e)) 

#--------------------------------------------------------------
@app.route('/timeSeries')
def timeSeries():
    return 1

#--------------------------------------------------------------
@app.route('/help')
def help():
    return render_template('help.html')

#--------------------------------------------------------------
@app.route('/contact')
def contact():
    return render_template('contact.html')

#==============================================================
def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1

#==============================================================
class myArbiter(gunicorn.arbiter.Arbiter):

    def halt(self):
        # Close pyferret
        pyferret.stop()

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

# Global variables
nbMaps = 0
cmdArray = []
tmpdir = tempfile.mkdtemp()

print('Temporary directory to remove: ', tmpdir)

options = {
    'bind': '%s:%s' % ('127.0.0.1', 5000),
    'workers': number_of_workers(),
    'worker_class': 'sync',
    'threads': 1
}
StandaloneApplication(app, options).run()

sys.exit(1)
