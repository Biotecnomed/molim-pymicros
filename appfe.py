import sys
import os
from flask import Flask, jsonify, request, abort
from werkzeug.exceptions import HTTPException
from datetime import datetime
import uuid
import logging.config
import json
from os import environ
from radiomics import featureextractor

# configure logging
port = environ.get("PORT","8080")
logfilename = '/tmp/molim_fe_'+port+'.log'
logging.config.fileConfig('logging.conf',defaults={'logfilename': logfilename})

# working dir
WD = '/tmp/wd'

# the allowed img types:
img_prefix_dict={}
img_prefix_dict['ADC']='ADC_'
img_prefix_dict['PC'] = 'PC_'
img_prefix_dict['SUB'] = 'SUB_'
img_prefix_dict['T2'] = 'T2_'

# create logger
logger = logging.getLogger('molim')
the_model = None
map = {}
extractor = None
config = None

def initAndCreateApp():
    global config, the_model, extractor

    logger.debug('Loading service configuration file...')
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

    # Initialize feature extractor
    logger.debug("Loading pyradiomics configuration from %s...", the_model['pyradiomics_conf'])
    extractor = featureextractor.RadiomicsFeatureExtractor(the_model['pyradiomics_conf'])

    logger.debug("Create a working directory...")
    if not os.path.exists(WD):
        os.mkdir(WD)

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
    os.mkdir(os.path.join(WD,generated))
    task = {"status": 'INIT', 'created_at': created_at, 'updated_at': created_at}
    map[generated] = task
    logger.info('Init new task with uuid %s',generated)
    return jsonify({'uuid': generated})


@app.route('/upload/<uuid>', methods=['POST'])
def upload_file(uuid):
    task = retrive(uuid)
    f = request.files['file']
    name = request.form['name']
    if name not in ['origin','roi']:
        abort(404,'Invalid resource name')
    if name == 'origin':
        type = request.form['type']
        if type not in img_prefix_dict.keys():
            abort(404,'Invalid resource for volume type')
        task['vtype'] = type
    savepath = os.path.join(WD,uuid,name+'.nii.gz')
    f.save(savepath)
    update(task)
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
    prefix = img_prefix_dict[task['vtype']]
    output = os.path.join(WD,uuid,'output.json')

    if task['status'] == 'LOADED':
        try:
            task['status'] = 'RUNNING'
            logger.debug('Extracting features fot task %s',task)
            path_image_in = os.path.join(WD,uuid,'origin.nii.gz')
            path_roi_in = os.path.join(WD,uuid,'roi.nii.gz')
            featureVector = extractor.execute(path_image_in, path_roi_in)
            logger.debug('Changing keys prefix...')
            res={}
            for df_k in featureVector.keys():
                res[(prefix+df_k)]=str(featureVector[df_k])
            logger.debug('Saving output to task %s working dir...',task)
            with open(output,'w') as jsonoutput:
                json.dump(res,jsonoutput)
            task['status'] = 'DONE'
            logger.info('Task %s completed',uuid)
            update(task)
        except Exception as err:
            logger.error('Unexpected error while running features extraction: %s',err)
            task['status'] = 'ABORTED'
            update(task)
            abort(500,'Internal server error')
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
        #return send_from_directory(os.path.join(WD,task),'output.json')
        output = os.path.join(WD,uuid,'output.json')
        with open(output,'r') as filein:
            o = json.load(filein)
        return jsonify(o)
    else:
        abort(404,'Task {} not completed: no output available'.format(uuid))


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
    p1 = os.path.join(WD,uuid,'origin.nii.gz')
    p2 = os.path.join(WD,uuid,'roi.nii.gz')
    if not os.path.exists(p1):
        logger.warning('Missing origin volume in task %s',uuid)
        return False
    if not os.path.exists(p2):
        logger.warning('Missing roi volume in task %s',uuid)
        return False
    return True


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
