from flask import Flask

app = Flask(__name__)

@app.route('/')
def welcome():
    return 'Welcome. This is (python-)microservice template to wrap model and algorithm task of MolimOncoBrain project'

@app.route('/name')
def getName():
    return 'Your model name'

@app.route('/desc')
def description():
    return 'A short description of your model...'
