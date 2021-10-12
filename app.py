from flask import Flask, jsonify, request, abort
from werkzeug.exceptions import HTTPException
from datetime import datetime
import uuid
import json
from joblib import load

map = {}
labels = ['CTRL','AD'] # set correct labels here
path_model = 'models/model.md' # path to the model
path_scaler_in = 'models/scaler.scl' # path to the scaler
clf = None  # the model
scaler = None  # the scaler
fetures = ['f1', 'f2', 'fn']  # a features list


def initAndCreateApp():
    global scaler, clf
    # read the config and check data correctness
    print("Loading model and scaler...")
    scaler = load(path_scaler_in)
    clf = load(path_model)
    return Flask(__name__)

### GET the APP
app = initAndCreateApp()

# Return a welcome message
@app.route('/')
def welcome():
    return 'Your custom welcome message'


# Choose a custom model/algorithm name
@app.route('/name')
def getName():
    return 'MOLIM Model/Algorithm Name'


# Choose a brief description. Html tag are admitted too
@app.route('/desc')
def description():
    return '<p> This model etc...</p>'


# Init a new task instance
@app.route('/init')
def init():
    generated = uuid.uuid4().hex
    created_at = get_timestamp()
    task = {"status": 'INIT', 'created_at': created_at, 'updated_at': created_at}
    map[generated] = task
    return jsonify({'uuid': generated})


# Load input data
@app.route('/load/<uuid>', methods=['POST'])
def load(uuid):
    task = retrive(uuid)
    content = request.get_json()
    filtered_content = {k: content[k] for k in fetures}
    task['input'] = filtered_content
    update(task)
    return jsonify(task)


# Check everything is fine to run
@app.route('/check/<uuid>')
def check(uuid):
    task = retrive(uuid)
    if checkinput(task):
        task['status'] = 'LOADED'
        update(task)
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
        lbl = clf.predict(X_pred)  # ris = model.predict([X])
        task['status'] = 'DONE'
        task['output'] = labels[lbl[0]]
        update(task)
    else:
        abort(404,"Task is not loaded");
    return jsonify(task)


# Abort a task
@app.route('/abort/<uuid>')
def abort(uuid):
    task = retrive(uuid)
    if task['status'] == 'RUNNING':
        task['status'] = 'ABORTED'
        update(task)
    return jsonify(task)


# Clean task workspace
@app.route('/reset/<uuid>')  # clean the workspace
def reset(uuid):
    task = retrive(uuid)
    if task['status'] == 'ABORTED':
        task['status'] = 'ABORTED'
        update(task)
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
#    path = os.path.join(WD, uuid)
#    shutil.rmtree(path)
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
    for task in map:
        print('termino il processo con pid %s' % task)
    map.clear()
    return ('', 200)

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
def checkinput(task):
    if "input" in task:
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
