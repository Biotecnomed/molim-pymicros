import sys

from flask import Flask, jsonify, request, abort
from werkzeug.exceptions import HTTPException
from datetime import datetime
import uuid
import logging.config
import json
from os import environ
from joblib import load

# configure logging
port = environ.get("PORT","8080")
logfilename = '/tmp/molim_'+port+'.log'
logging.config.fileConfig('logging.conf',defaults={'logfilename': logfilename})

# create logger
logger = logging.getLogger('molim')
the_model = None
map = {}
labels = [] # labels
dlabels = [] # labels
clf = None  # the model
scaler = None  # the scaler
features = []
config = None

def initAndCreateApp():
    global config, the_model, scaler, clf, labels, dlabels

    logger.debug('Loading model configuration file...')
    with open('model.json','r') as confile:
        config = json.load(confile)

    code = environ.get("MODEL_CODE_NAME")
    if not code:
        logger.critical('MODEL_CODE_NAME env variable not set')
        sys.exit(1)
    logger.info('MODEL CODE NAME is %s', code)
    if not code in config['models']:
        logger.critical('No such model: %s', code)
        sys.exit(1)

    the_model = config['models'][code]

    logger.debug("Loading pre-trained model from %s...", the_model['trained'])
    clf = load(the_model['trained'])

    logger.debug("Loading scaler from %s...", the_model['scaler'])
    scaler = load(the_model['scaler'])

    logger.debug("Loading labels...")
    labels = the_model['labels']
    dlabels = the_model['label_descriptions']

    logger.debug("Loading feature list from %s ...", the_model['feature_list'])
    with open(the_model['feature_list'],'r') as file:
        for line in file:
            features.append(line.strip())

    return Flask(__name__)

app = initAndCreateApp()

# Return a welcome message
@app.route('/')
def welcome():
    return 'Your custom welcome message'


# Choose a custom model/algorithm name
@app.route('/name')
def getName():
    return jsonify(the_model['name'])


# Choose a brief description. Html tag are admitted too
@app.route('/desc')
def description():
    return jsonify(the_model['description'])


# Init a new task instance
@app.route('/init')
def init():
    generated = uuid.uuid4().hex
    created_at = get_timestamp()
    task = {"status": 'INIT', 'created_at': created_at, 'updated_at': created_at}
    map[generated] = task
    logger.info('Init new task with uuid %s',generated)
    return jsonify({'uuid': generated})


# Load input data
@app.route('/load/<uuid>', methods=['POST'])
def load(uuid):
    task = retrive(uuid)
    content = request.get_json()
    filtered_content = {k: content[k] if k in content else None for k in features}
    task['input'] = filtered_content
    update(task)
    logger.info('Loaded input on task %s',uuid)
    return jsonify(task)


# Check everything is fine to run
@app.route('/check/<uuid>')
def check(uuid):
    task = retrive(uuid)
    if checkinput(uuid,task):
        task['status'] = 'LOADED'
        update(task)
        logger.info('Task %s move to LOADED',uuid)
    else:
        logger.warning('Task %s cannot move to LOADED',uuid)
        abort(404,'Missing input in task {}'.format(uuid))
    return jsonify(task)


# Simulate a fake task just passing from READY to RUNNING and finally to DONE
@app.route('/run/<uuid>')
def run(uuid):
    task = retrive(uuid)
    if task['status'] == 'LOADED':
        input = task['input']
        X_pred = list(input.values())
        X_pred = [[float(x) for x in X_pred]]
        X_pred = scaler.transform(X_pred)
        task['status'] = 'RUNNING'
        logger.info('Task %s is running',uuid)
        lbl = clf.predict(X_pred)  # ris = model.predict([X])
        task['status'] = 'DONE'
        logger.info('Task %s is completed',uuid)
        task['output'] = labels[lbl[0]]
        task['output_description'] = dlabels[lbl[0]]
        update(task)
    else:
        logger.warning('Task %s is not ready to run',uuid)
        abort(404,"Task is not loaded")
    return jsonify(task)


# Abort a task
@app.route('/abort/<uuid>')
def abortTask(uuid):
    task = retrive(uuid)
    if task['status'] == 'RUNNING':
        task['status'] = 'ABORTED'
        update(task)
        logger.info('Task %s move to ABORTED',uuid)
    else:
        logger.warning('Task %s cannot move to ABORTED',uuid)
        abort(404,"Cannot abort task")
    return jsonify(task)


# Clean task workspace
@app.route('/reset/<uuid>')  # clean the workspace
def reset(uuid):
    task = retrive(uuid)
    if task['status'] == 'ABORTED':
        task['status'] = 'INIT'
        update(task)
        logger.info('Task %s move to INIT',uuid)
    else:
        logger.warning('Task %s cannot move to INIT',uuid)
        abort(404,"Cannot reset task")
    return jsonify(task)


# Get the task state[INIT,LOADED,RUNNING,DONE,ABORTED]
@app.route('/status/<uuid>')
def status(uuid):
    task = retrive(uuid)
    return jsonify(task)


# Stop and remove task with all its resources
@app.route('/remove/<uuid>')
def remove(uuid):
    task = retrive(uuid)
    map.pop(uuid)
    logger.info('Task %s was removed',uuid)
    return jsonify(task)


# Get the output of a task
@app.route('/output/<uuid>')
def output(uuid):
    task = retrive(uuid)
    if task['status'] == 'DONE':
        return jsonify(task)
    else:
        abort(404,'Task {} not completed: no output available'.format(uuid))


# Retrive an output resource by name
@app.route('/retrive/<uuid>/<name>')
def retrieve(uuid, name):
    task = retrive(uuid)
    if task['status'] == 'DONE':
        # fetch the correct resource
        return ('', 200)


# Intended for testing purposes only
@app.route('/tasklist')
def tasklist():
    return jsonify(map)


# Intended for testing purposes only
@app.route('/taskerase')
def erase():
    map.clear()
    logger.info('All tasks have been removed')
    return ('Done', 200)

@app.route('/stats')
def statistics():
    counter = {'TOTAL': len(map),'INIT': 0,'LOADED': 0,'RUNNING': 0, 'DONE': 0, 'ABORTED': 0}
    for k in map.keys():
        counter[map.get(k)['status']] += 1
    return jsonify(counter)


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
def checkinput(uuid,task):
    if "input" in task:
        input = task["input"]
        for k in input:
            if not input[k]:
                logger.warning('Missing input %s in task %s',k,uuid)
                return False
        return True
    else:
        return False


# Just format a timestamp
def get_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


# Update the last access time of a task
def update(task):
    task['updated_at'] = get_timestamp()

# If we're running in stand alone mode, run the application
# Don't forget to remove the debug flag in production
if __name__ == '__main__':
    app.run(debug=True)
