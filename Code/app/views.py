# -*- encoding: utf-8 -*-


# Python modules
import os, logging 
import pandas as pd


# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort
from jinja2              import TemplateNotFound

# App modules
from app        import app, lm, db, bc
from app.models import Users
from app.forms  import LoginForm, RegisterForm

dataset = pd.read_excel('dataset.xlsx')

# provide login manager with load_user callback
@lm.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Logout user
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Register a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    
    # declare the Registration Form
    form = RegisterForm(request.form)

    msg     = None
    success = False

    if request.method == 'GET': 

        return render_template( 'register.html', form=form, msg=msg )

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 
        email    = request.form.get('email'   , '', type=str) 

        # filter User out of database through username
        user = Users.query.filter_by(user=username).first()

        # filter User out of database through username
        user_by_email = Users.query.filter_by(email=email).first()

        if user or user_by_email:
            msg = 'Error: User exists!'
        
        else:         

            pw_hash = bc.generate_password_hash(password)

            user = Users(username, email, pw_hash)

            user.save()

            msg     = 'User created, please <a href="' + url_for('login') + '">login</a>'     
            success = True

    else:
        msg = 'Input error'     

    return render_template( 'register.html', form=form, msg=msg, success=success )

# Authenticate user
@app.route('/login', methods=['GET', 'POST'])
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
        user = Users.query.filter_by(user=username).first()

        if user:
            
            if bc.check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('calci'))
            else:
                msg = "Wrong password. Please try again."
        else:
            msg = "Unknown user"

    return render_template( 'login.html', form=form, msg=msg )

# App main route + generic routing
@app.route('/', defaults={'path': 'index'})
@app.route('/<path>')
def index(path):

    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))

    try:

        return render_template( 'index.html' )
    
    except TemplateNotFound:
        return render_template('page-404.html'), 404
    
    except:
        return render_template('page-500.html'), 500

@app.route('/details')
def details():

    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))

    try:

        return render_template( 'details.html' )
    
    except TemplateNotFound:
        return render_template('page-404.html'), 404
    
    except:
        return render_template('page-500.html'), 500
    
@app.route('/calci')
def calci():
    try:
        return render_template( 'CutOffCalci.html' )
    except TemplateNotFound:
        return render_template('page-404.html'), 404 
    except:
        return render_template('page-500.html'), 500

# Return sitemap
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')

@app.route('/recommendations', methods=['POST'])
def recommendations():
    # Get user inputs from the form
    cutoff = request.form['cut-off']
    branch = request.form['branch']
    community = request.form['community']
    location = request.form['location']

    print(cutoff, branch, community, location, sep=" ")

    community_column = ''
    if community == 'OC':
        community_column = 'OC'
    elif community == 'BCM':
        community_column = 'BCM'
    elif community == 'BC':
        community_column = 'BC'
    elif community == 'MBC':
        community_column = 'MBC'
    elif community == 'SCA':
        community_column = 'SCA'
    elif community == 'SC':
        community_column = 'SC'
    elif community == 'ST':
        community_column = 'ST'

    # Filter the dataset based on user inputs
    filtered_data = dataset[(dataset[community_column] >= float(cutoff)) &
                           (dataset['Branch_Name'] == 'Civil Engineering')]

 # Drop duplicate rows based on College_Name
    filtered_data.drop_duplicates(subset=['College_Name'], keep='first', inplace=True)

    # Select only the specified columns
    selected_columns = ['College_Code', 'College_Name', 'Branch_Code', 'Branch_Name', community_column]
    filtered_data = filtered_data[selected_columns]

    # Convert filtered data to HTML table
    table_html = filtered_data.to_html(index=False, classes='table table-striped')
    
    # Convert filtered data to HTML table
    table_html = filtered_data.to_html()

    return render_template('recommendations.html', table=table_html)