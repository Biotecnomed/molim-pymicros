import argparse
import configparser
import json
import os
#import pandas as pd
from joblib import load


def check_config(config_data):
    available_formats= ['csv','json']
    flag_ok=True
    ## general params
    if not 'model_file_path' in config_data['GENERAL']:
        print('MISSING MODEL FILEPATH! ')
        flag_ok=False
    else:
        if config_data['GENERAL'].get('model_file_path') is None \
                or config_data['GENERAL'].get('model_file_path') == '':
            print('MODEL FILEPATH NOT SPECIFIED! ')
            flag_ok=False
        else:
            file=config_data['GENERAL'].get('model_file_path')
            if not os.path.isfile(file):
                print('WRONG MODEL FILEPATH! ')
                flag_ok=False

    if not 'scaler_file_path' in config_data['GENERAL']:
        print('MISSING SCALER FILEPATH! ')
        flag_ok=False
    else:
        if config_data['GENERAL'].get('scaler_file_path') is None \
                or config_data['GENERAL'].get('scaler_file_path') == '':
            print('SCALER FILEPATH NOT SPECIFIED! ')
            flag_ok=False
        else:
            file=config_data['GENERAL'].get('scaler_file_path')
            if not os.path.isfile(file):
                print('WRONG SCALER FILEPATH! ')
                flag_ok=False

    if not 'sample_file_path' in config_data['INPUT_DATA']:
        print('MISSING INPUT FILEPATH! ')
        flag_ok = False
    else:
        if config_data['INPUT_DATA'].get('sample_file_path') is None \
                or config_data['INPUT_DATA'].get('sample_file_path') == '':
            print('INPUT FILEPATH NOT SPECIFIED! ')
            flag_ok = False
        else:
            file = config_data['INPUT_DATA'].get('sample_file_path')
            if not os.path.isfile(file):
                print('WRONG INPUT FILEPATH! ')
                flag_ok = False

    if not 'input_format' in config_data['INPUT_DATA']:
        print('MISSING INPUT FORMAT! ')
        flag_ok = False
    else:
        if config_data['INPUT_DATA'].get('input_format') is None \
                or config_data['INPUT_DATA'].get('input_format') == '':
            print('INPUT FORMAT NOT SPECIFIED! ')
            flag_ok = False
        else:
            in_format = config_data['INPUT_DATA'].get('input_format')
            if not in_format in available_formats:
                print('WRONG INPUT FORMAT! ')
                flag_ok = False

    return flag_ok


if __name__ == "__main__":

    ''' the input parser '''
    parser = argparse.ArgumentParser(description='MOLIM ALZHEIMER DEMENTIA Predictor')
    parser.add_argument('--dir_ini_file', metavar='DIR',
                        help='path to directory containing the config parameter file', required=True)

    args = parser.parse_args()
    # check if the input dirs exists
    if not os.path.isfile(args.dir_ini_file):
        print(" CONFIG FILE WRONG OR NOT EXISTING ! ")
        print(args.dir_ini_file)
        exit()

    # read the config and check data correctness
    config = configparser.ConfigParser()
    config.read(args.dir_ini_file)
    if not check_config(config):
        exit()

    # take the info
    path_model = config['GENERAL'].get('model_file_path')
    path_scaler_in = config['GENERAL'].get('scaler_file_path')
    path_sample_in = config['INPUT_DATA'].get('sample_file_path')
    in_format = config['INPUT_DATA'].get('input_format')

    ## workaround
    f = open('MOBL_AD_test_SAMPLE.json', 'r')
    input = json.load(f)

    X_pred = list(input['UNICZFDGAD038'].values())
    X_pred = [[float(x) for x in X_pred]]

#    if in_format=='csv':
#        X = pd.read_csv(path_sample_in, delimiter=';', quotechar='"', skipinitialspace=True, decimal=",",
 #                   index_col=0)
 #   else: # assumes json
 #       X = pd.read_json(path_sample_in, orient='index')

 #   print("Processing sample " + X.index.values[0])
    #the input values
 #   X_pred = X.values
    # normalize them
    scaler = load(path_scaler_in)
    X_pred = scaler.transform(X_pred)
    # load the model and predict
    clf = load(path_model)
    lbl=clf.predict(X_pred)

    print("Predicted_label is: " + str(lbl[0]))

