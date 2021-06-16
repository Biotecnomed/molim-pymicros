from flask import Flask, jsonify, request, abort
from werkzeug.exceptions import HTTPException
from datetime import datetime
import pickle

import os
import shutil
import uuid
import json

app = Flask(__name__)

map = {}
WD = './wd'
model = pickle.load(open('iris_decision_tree', 'rb'))
label = ['Iris Setosa','Iris Versicolour','Iris Verginica']

# Return a welcome message
@app.route('/')
def welcome():
    return 'Welcome. A simple Decision Tree model on Iris Dateset'

# Choose a custom model/algorithm name
@app.route('/name')
def getName():
    return 'GINI Decision Tree on Iris Dataset'

# Choose a brief description. Html tag are admitted too
@app.route('/desc')
def description():
    return '<p> This model classify an Iris flower based on four measures: sepal length (cm), sepal width (cm), petal length (cm) and petal width (cm). ' \
           '\n The model is based on Decision Trees (DTs) (non-parametric supervised learning)' \
           '\n Input must be passed in the form of a json object like this: {"sepal_length": 1.0, "sepal_width": 1.0,"petal_length": 1.0,"petal_width": 1.0} </p>'

# Init a new task instance
@app.route('/init')
def init():
    generated = uuid.uuid4().hex
    os.mkdir(os.path.join(WD, generated))
    created_at = get_timestamp()
    task = {"status": 'INIT', 'created_at': created_at, 'updated_at': created_at}
    map[generated] = task
    return jsonify({'uuid': generated})

# Load input data
@app.route('/load/<uuid>',methods=['POST'])
def load(uuid):
    task = retrive(uuid)
    content = request.get_json()
    task['input'] = content
    update(task)
    return jsonify(task)

# Check everything is fine to run
@app.route('/check/<uuid>')
def check(uuid):
    task = retrive(uuid)
    checkinput(task)
    return jsonify(task)


# Simulate a fake task just passing from READY to RUNNING and finally to DONE
@app.route('/run/<uuid>')
def run(uuid):
    task = retrive(uuid)
    if task['status'] == 'LOADED':
        input = task['input']
        X = [input['sepal_length'],input['sepal_width'],input['petal_length'],input['petal_width']]
        task['status']  = 'RUNNING'
        ris = model.predict([X])
        task['status']  = 'DONE'
        task['output'] = label[ris[0]]
        update(task)
    return jsonify(task)


# Abort a task
@app.route('/abort/<uuid>')
def abort(uuid):
    task = retrive(uuid)
    if task['status'] == 'RUNNING':
        #maybe get the pid first
        #terminate
        task['status'] = 'ABORTED'
        update(task)
    return jsonify(task)

# Clean task workspace
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

# Get the task state[INIT,READY,RUNNING,DONE,ABORTED]
@app.route('/status/<uuid>')
def status(uuid):
    task = retrive(uuid)
    return jsonify(task)

# Stop and remove task with all its resources
@app.route('/remove/<uuid>')
def remove(uuid):
    task = retrive(uuid)
    path = os.path.join(WD, uuid)
    shutil.rmtree(path)
    map.pop(uuid)
    return jsonify(task)

# Get the output of a task
@app.route('/output/<uuid>')
def output(uuid):
    task = retrive(uuid)
    if task['status'] == 'DONE':
        return jsonify(task)

# Retrive an output resource by name
@app.route('/retrive/<uuid>/<name>')
def retrieve(uuid,name):
    task = retrive(uuid)
    if task['status'] == 'DONE':
        # fetch the correct resource
        return ('',200)

# Intended for testing purposes only
@app.route('/tasklist')
def tasklist():
    return jsonify(map)

# Intended for testing purposes only
@app.route('/taskerase')
def erase():
    for task in map:
        print('termino il processo con pid %s' % task)
    map.clear()
    # command = '''rm -rf %s/* ''' % WD
    # print(command)
    # process = subprocess.Popen(command,shell=True)
    shutil.rmtree(WD)
    os.mkdir(WD)
    return ('', 200)

# Handle Http Exception and wrap it as json
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

# Help method you can customize to fit your task repository access method
def retrive(uuid):
    if uuid not in map:
        abort(404, 'Invalid UUID')
    return map.get(uuid)

# Add here your custom check logic
def checkinput(task):
    input =  task['input']
    if 'sepal_length' in input and \
            'sepal_width' in input and \
            'petal_length' in input and \
            'petal_width' in input:
        task['status'] = 'LOADED'

# Just format a timestamp
def get_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))

# Update the last access time of a task
def update(task):
    task['updated_at'] = get_timestamp()


# If we're running in stand alone mode, run the application
# Don't forget to remove the debug flag in production
if __name__ == '__main__':
    if not os.path.exists(WD):
        os.mkdir(WD)

    app.run(debug=True)
