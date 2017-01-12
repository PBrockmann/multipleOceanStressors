from flask import Flask, render_template
from flask_script import Manager
from flask_bootstrap import Bootstrap

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
@app.route('/data')
def data():
    return render_template('data.html')

#============================================
@app.route('/help')
def help():
    return render_template('help.html')

#============================================
@app.route('/contact')
def contact():
    return render_template('contact.html')

#============================================
if __name__ == '__main__':
    manager.run()
