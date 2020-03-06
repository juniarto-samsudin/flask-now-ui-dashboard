# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

# Python modules
import os, logging 

# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory, flash, session
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort

# App modules
from app        import app, lm, db, bc
from app.models import User, DeploymentLatest
from app.forms  import LoginForm, RegisterForm, DeployAppForm, QueryDevEnvVarsForm, SetDevEnvVarsForm

# From old dashboard
import os
import simplejson as json
import requests


TOKEN = "iIJZep7sYmgERjqxZ5sIBWnzcOkwUe1Q"

# provide login manager with load_user callback
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Logout user
@app.route('/logout.html')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Register a new user
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    
    # declare the Registration Form
    form = RegisterForm(request.form)

    msg = None

    if request.method == 'GET': 

        return render_template('layouts/default.html',
                                content=render_template( 'pages/register.html', form=form, msg=msg ) )

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 
        email    = request.form.get('email'   , '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        # filter User out of database through username
        user_by_email = User.query.filter_by(email=email).first()

        if user or user_by_email:
            msg = 'Error: User exists!'
        
        else:         

            pw_hash = password #bc.generate_password_hash(password)

            user = User(username, email, pw_hash)

            user.save()

            msg = 'User created, please <a href="' + url_for('login') + '">login</a>'     

    else:
        msg = 'Input error'     

    return render_template('layouts/default.html',
                            content=render_template( 'pages/register.html', form=form, msg=msg ) )

# Authenticate user
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    
    # Declare the login form
    form = LoginForm(request.form)

    # Flask message injected into the page, in case of any errors
    msg = None

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        if user:
            
            #if bc.check_password_hash(user.password, password):
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
            else:
                msg = "Wrong password. Please try again."
        else:
            msg = "Unkkown user"

    return render_template('layouts/default.html',
                            content=render_template( 'pages/login.html', form=form, msg=msg ) )

# App main route + generic routing
@app.route('/', defaults={'path': 'device-status.html'},methods=['POST','GET'])
@app.route('/<path>',methods=['POST','GET'])
def index(path):

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    content = None

    try:
        #IF DOCKER
        PROVURL = os.getenv('PROVISINIONG_REST_URL')

        #IF NOT DOCKER
        if (PROVURL == None):
            PROVURL = "http://vaultsonchain.com:5004/"

        #PROVREST = os.getenv('PROVISIONING_REST_URL') + 'devs-apps-simple'
        #PROVREST = PROVURL + 'devs-apps-simple'

        #print(PROVREST)
        #response = requests.get(PROVREST)
        # try to match the pages defined in -> pages/<input file>
        if  (path=="device-status.html"):
            PROVREST = PROVURL + 'devs-apps-simple'
            response = requests.get(PROVREST)
            responseJSON = json.loads(response.content)

            apps = DeploymentLatest.query.all() #Get from deployment-database
            #add image and release keys to the responseJSON
            i = 0
            j = 0
            while i < len(responseJSON):
                while j < len(apps):
                    if (responseJSON[i]['app_name'] == apps[j].app):
                        responseJSON[i]['image'] = apps[j].image
                        responseJSON[i]['release'] = apps[j].release
                    j+=1
                j=0
                i+=1

            print(responseJSON)

            return render_template('layouts/default.html',
                                content=render_template( 'pages/'+path, msg=responseJSON, page="device-status") )
        elif (path=="app-deployment.html"):
            #GET APPLICATION LIST
            PROVREST = PROVURL + 'applications-only'
            response = requests.get(PROVREST)
            responseJSON = json.loads(response.content)

            choiceAppList = []

            i = 0
            while i < len(responseJSON):
                print (responseJSON[i])
                choiceAppTuple = (responseJSON[i]['value'], responseJSON[i]['name'])
                choiceAppList.append(choiceAppTuple)
                i+=1

            #GET IMAGE LIST
            PROVREST = PROVURL + 'images'
            response = requests.get(PROVREST)
            responseJSON = json.loads(response.content)

            choiceImageList = []

            i = 0
            while i < len(responseJSON):
                print (responseJSON[i])
                choiceImageTuple = (responseJSON[i]['value'], responseJSON[i]['name'])
                choiceImageList.append(choiceImageTuple)
                i+=1


            # Declare Form
            form = DeployAppForm(request.form)
            form.application.choices = choiceAppList
            form.image.choices = choiceImageList

            if request.method == 'GET':
                return render_template('layouts/default.html',
                                   content=render_template('pages/app-deployment.html', form=form, page="app-deployment"))
            if form.validate_on_submit():
                session['application'] = form.application.data
                session['image'] = form.image.data
                PROVREST = PROVURL + "app-deploy" + "/" + session['application'] + "/" + session['image']
                print (PROVREST)
                response = requests.get(PROVREST)
                responseJSON = json.loads(response.content)
                print(responseJSON['release'])
                if (responseJSON['release'] == 'deploy failed!' or responseJSON['release'] == 'login failed'):
                    print("DEPLOY FAILED")
                    message = "Deployment of {} to {} application FAILED"
                    flash(message.format(session['image'],session['application']))
                    return render_template('layouts/default.html',
                                           content=render_template('pages/app-deployment.html', form=form, page="app-deployment"))
                else:
                    print("DEPLOY SUCCESS")

                    #DataBase Operation
                    #Check whether app exist
                    app = DeploymentLatest.query.filter_by(app=responseJSON['app']).first()
                    print("APP.IMAGE:" + app.image)
                    print("APP.RELEASE:" + app.release)

                    if app is None:   #Create new record
                        deployment = DeploymentLatest(responseJSON['app'], responseJSON['image'], responseJSON['release'])
                        deployment.save()
                    else:
                        app.image = responseJSON['image']
                        app.release = responseJSON['release']
                        app.save()


                    message = "Deployment of {} to {} application SUCCESSFUL"
                    flash(message.format(session['image'],session['application']))
                    return render_template('layouts/default.html',
                                           content=render_template('pages/app-deployment.html', form=form, page="app-deployment"))
                '''
                if "Successfully" in output:
                    command1 = "balena deploy " + application + " " + image
                    print (command1)
                    stream = os.popen(command1)
                    output = stream.read()
                    if "succeeded!" in output:
                        print("Deploy Successfull")
                        return redirect(url_for('index'))
                '''
        elif (path=="device-env-vars.html"):
            #GET DEVICE LIST
            PROVREST = PROVURL + 'devs-apps-simple'
            response = requests.get(PROVREST)
            responseJSON = json.loads(response.content)

            choiceDevList = []

            for device in responseJSON:
                choiceAppTuple = (device['uuid'], device['device_name'])
                choiceDevList.append(choiceAppTuple)

            #Declare Form
            form = QueryDevEnvVarsForm(request.form)
            form.device.choices = choiceDevList

            #Declare Set
            settings = SetDevEnvVarsForm(request.form)
            settings.device.choices = choiceDevList


            if request.method == 'GET':
                return render_template('layouts/default.html',
                                   content=render_template('pages/'+path, form=form, settings=settings, page="device-env-vars"))
            if form.validate_on_submit():
                session['device'] = form.device.data
                PROVREST = PROVURL + "dev-env-vars-simple" + "/" + session['device']
                print (PROVREST)
                response = requests.get(PROVREST)
                responseJSON = json.loads(response.content)
                print(responseJSON)
                return render_template('layouts/default.html',
                                       content=render_template('pages/'+path, form=form, settings=settings,  page="device-env-vars", msg=responseJSON))
    except:
        
        return render_template('layouts/auth-default.html',
                                content=render_template( 'pages/404.html' ) )

# Return sitemap 
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')


# FROM OLD DASHBOARD
'''
config = None

with open('config.json') as f:
    config = json.load(f)
    print("config          :", config)
    print("config['device']:", config['device'])
    print(config['device']['Intel Edison']['image'][0])

def getJsonDeviceName(name):
    if (name == "edison"):
        return "Intel Edison"
    elif (name == "rasp"):
        return "Raspberry"
    elif (name == "nano"):
        return "Nvidia Jetson Nano"

def getJsonImageName(name):
    if (name == "azure-rasp_main"):
        return "Raspberry Azure Simulation"
    elif (name == "simple-mqtt_main"):
        return "Raspberry ThingsBoard Simulation"
    elif (name == "none-raspberry_main"):
        return "Raspberry NoImage"
    elif (name == "azure-rasp-yocto_main"):
        return "Raspberry Azure W/Temp.Sensor"
    elif (name == "tb-rasp-yocto_main"):
        return "Raspberry ThingsBoard W/Temp.Sesnor"
    elif (name == "azure-edison_main"):
        return "Edison Azure Simulation"
    elif (name == "simple-mqtt-edison_main"):
        return "Edison ThingsBoard Simulation"
    elif (name == "none-edison_main"):
        return "Edison NoImage"
    elif (name == "azure-nano_main"):
        return "Nano Azure Simulation"
    elif (name == "simple-mqtt-nano_main"):
        return "Nano ThingsBoard Simulation"
    elif (name == "none-nano_main"):
        return "Nano NoImage"
    elif (name == "azure-nano-yocto_main"):
        return "Nano Azure W/Temp.Sensor"
    elif (name == "tb-nano-yocto_main"):
        return "Nano ThingsBoard W/Temp.Sensor"

def createResponse(data):
    print ("createResponse",data)
    response = app.response_class(
            response=json.dumps(data, use_decimal=True),
            status=200,
            mimetype='application/json'
            )
    print ("RESPONSE", response)
    return response

@app.route('/device-status', methods=['GET'])
def deviceStatus():
    stream = os.popen("balena apps")
    output = stream.read()
    content = [line.split() for line in output.splitlines()]
    content.pop(0)
    return createResponse(content)

@app.route('/device-image', methods=['GET'])
def deviceImage():
    config={}
    with open('config.json') as f:
        config = json.load(f)
    return createResponse(config)

@app.route('/device-deploy/<device>/<image>',methods=['POST','GET'])
def deviceDeploy(device=None,image=None):
    print ("device:", device)
    print ("image :", image)
    command = "balena deploy " + device + " " +image
    print (command)
    stream = os.popen(command)
    output = stream.read()
    if "succeeded!" in output:
        print("deviceDeploy succeeded!")
        deviceNameJson = getJsonDeviceName(device)
        imageNameJson  = getJsonImageName(image)
        config['device'][deviceNameJson]['deployedImage'] = imageNameJson
        with open('config.json', 'w') as f:
            json.dump(config, f)
        print("CONFIG NEW:", config)
        return createResponse(config)
    else:
        print("deviceDeploy failed!")
        return createResponse(1)


@app.route('/getEnvVar/<uuid>', methods=['GET'])
def getEnvVar(uuid=None):
    print ("uuid:", uuid)
    command = "balena envs --device " + uuid
    print (command)
    stream = os.popen(command)
    output = stream.read()
    return createResponse(output)
'''
