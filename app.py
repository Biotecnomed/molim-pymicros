from flask import Flask, jsonify, request, abort
from werkzeug.exceptions import HTTPException
from datetime import datetime
import subprocess

import os
import shutil
import uuid
import json
app = Flask(__name__)

map = {}
WD = './wd'

@app.route('/')
def welcome():
    return 'Welcome. This is (python-)microservice template to wrap model and algorithm task of MolimOncoBrain project'

@app.route('/name')
def getName():
    return 'Your model name'

@app.route('/desc')
def description():
    return 'A short description of your model...'

@app.route('/init')
def init():
    generated = uuid.uuid4().hex
    os.mkdir(os.path.join(WD,generated))
    created_at = get_timestamp()
    task = {"status": 'INIT', 'created_at': created_at, 'updated_at': created_at}
    map[generated] = task
    return jsonify({'uuid': generated})

@app.route('/load/<uuid>',methods=['POST'])
def load(uuid):
    task = retrive(uuid)
    content = request.get_json()
    file = os.path.join(WD,uuid,'input.json')
    with open(file,'w') as jsonfile:
        json.dump(content,jsonfile,indent=4)
    update(task)
    return jsonify(task)

@app.route('/upload/<uuid>', methods=['POST'])
def upload_file(uuid):
    task = retrive(uuid)
    f = request.files['file']
    name = request.form['name']
    savepath = os.path.join(WD,uuid,name)
    f.save(savepath)
    update(task)
    return jsonify(task)

@app.route('/check/<uuid>')
def check(uuid):
    task = retrive(uuid)
    checkinput(task)
    return jsonify(task)

@app.route('/run/<uuid>')
def run(uuid):
    task = retrive(uuid)
    if task['status'] == 'LOADED':
        #run
        task['status']  = 'RUNNING'
        update(task)
    return jsonify(task)

@app.route('/abort/<uuid>') #stop task if is running
def abort(uuid):
    task = retrive(uuid)
    if task['status'] == 'RUNNING':
        #maybe get the pid first
        #terminate
        task['status'] = 'ABORTED'
        update(task)
    return jsonify(task)

@app.route('/reset/<uuid>') #clean the workspace
def reset(uuid):
    task = retrive(uuid)
    if task['status'] == 'ABORTED':
        path = os.path.join(WD,uuid)
        shutil.rmtree(path)
        os.mkdir(path)
        task['status']  = 'ABORTED'
        update(task)
    return jsonify(task)

@app.route('/status/<uuid>') #get the task state[INIT,RUNNING,DONE,ABORTED]
def status(uuid):
    task = retrive(uuid)
    return jsonify(task)

@app.route('/remove/<uuid>') #stop and remove task with all its resources
def remove(uuid):
    task = retrive(uuid)
    path = os.path.join(WD,uuid)
    shutil.rmtree(path)
    map.pop(uuid)
    return jsonify(task)

@app.route('/output/<uuid>')
def output(uuid):
    task = retrive(uuid)
    if task['status'] == 'DONE':
        return jsonify(task)

@app.route('/tasklist')
def tasklist():
    return jsonify(map)

@app.route('/taskerase')
def erase():
    for task in map:
        print('termino il processo con pid %s' % task)
    map.clear()
    #command = '''rm -rf %s/* ''' % WD
    #print(command)
    #process = subprocess.Popen(command,shell=True)
    shutil.rmtree(WD)
    os.mkdir(WD)
    return ('',200)


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

def retrive(uuid):
    if uuid not in map:
        abort(404,'Invalid UUID')
    return map.get(uuid)

def checkinput(task):
    task['status'] = 'LOADED'

def get_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))

def update(task):
    task['updated_at'] = get_timestamp()

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    if not os.path.exists(WD):
        os.mkdir(WD)

    app.run(debug=True)


