import argparse
import configparser
import os
import pandas as pd
from joblib import load
import json

def get_names_list(filename_in):
    # 2) read the column names input file
    with open(filename_in) as f:
        in_names = f.read()

    out_names= [name.strip() for name in in_names.splitlines()]

    return out_names

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

    if not 'feature_list_file_path' in config_data['GENERAL']:
        print('MISSING FEATURE LIST FILEPATH! ')
        flag_ok = False
    else:
        if config_data['GENERAL'].get('feature_list_file_path') is None \
                or config_data['GENERAL'].get('feature_list_file_path') == '':
            print('FEATURE LIST FILEPATH NOT SPECIFIED! ')
            flag_ok = False
        else:
            file = config_data['GENERAL'].get('feature_list_file_path')
            if not os.path.isfile(file):
                print('WRONG FEATURE LIST FILEPATH! ')
                flag_ok = False

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

    ## output
    if not 'result_file_path' in config_data['OUTPUT_DATA']:
        print('MISSING INPUT FILEPATH! ')
        flag_ok = False
    else:
        if config_data['OUTPUT_DATA'].get('result_file_path') is None \
                or config_data['OUTPUT_DATA'].get('result_file_path') == '':
            print('OUTPUT FILEPATH NOT SPECIFIED! ')
            flag_ok = False

    if not 'output_format' in config_data['OUTPUT_DATA']:
        print('MISSING OUTPUT FORMAT! ')
        flag_ok = False
    else:
        if config_data['OUTPUT_DATA'].get('output_format') is None \
                or config_data['OUTPUT_DATA'].get('output_format') == '':
            print('OUTPUT FORMAT NOT SPECIFIED! ')
            flag_ok = False
        else:
            in_format = config_data['OUTPUT_DATA'].get('output_format')
            if not in_format in available_formats:
                print('WRONG OUTPUT FORMAT! ')
                flag_ok = False

    return flag_ok


if __name__ == "__main__":

    ''' the input parser '''
    parser = argparse.ArgumentParser(description='MOLIM general Predictor')
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
    path_featlist_in = config['GENERAL'].get('feature_list_file_path')
    path_sample_in = config['INPUT_DATA'].get('sample_file_path')
    in_format = config['INPUT_DATA'].get('input_format')
    out_format = config['OUTPUT_DATA'].get('output_format')
    path_result = config['OUTPUT_DATA'].get('result_file_path')

    # read the feature list
    feature_col_list=get_names_list(path_featlist_in)

    if in_format=='csv':
        X_in = pd.read_csv(path_sample_in, delimiter=';', quotechar='"', skipinitialspace=True, decimal=",",
                    index_col=0)
    else: # assumes json
        X_in = pd.read_json(path_sample_in, orient='index')


    try:
        # ensure the column are the right ones and in the proper order!
        X = X_in[feature_col_list].iloc[:, :].values

        # load the model and the scaler, scale and  and predict
        scaler = load(path_scaler_in)
        X_pred = scaler.transform(X)
        clf = load(path_model)
        try:
            lbl = clf.predict(X_pred)
            # now write out the result
            try:
                if out_format == 'csv':
                    fs = open(path_result,'w')
                    for i in range(0, len(X)):
                        print("For sample " + X_in.index.values[i] + " the predicted label is: " + str(lbl[i]))
                        fs.write(X_in.index.values[i]+";"+ str(lbl[i]) +"\n")
                else:  # assumes json
                    res={}
                    fs= open(path_result, 'w')
                    for i in range(0, len(X)):
                        print("For sample " + X_in.index.values[i] + " the predicted label is: " + str(lbl[i]))
                        res[X_in.index.values[i]]=str(lbl[i])
                    json.dump(res, fs)
            except:
                print('ERRORE: WRITE DEI RISULTATI FALLITA')
        except:
            print('ERRORE: PREDICT SUI DATI NON FUNZIONA')
    except:
        print('ERRORE: I DATI IN INPUT SONO ERRATI O INCOMPLETI')




