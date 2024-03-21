# -*- encoding: utf-8 -*-
# Python modules
from datetime import datetime
import io
import json
import os
from bs4 import BeautifulSoup
from flask_cors import cross_origin
import pandas as pd

# Flask modules
from flask               import make_response, render_template, request, send_file, url_for, redirect, send_from_directory
from flask_login         import login_user, logout_user
from jinja2              import TemplateNotFound

import matplotlib.pyplot as plt
import io
import base64

# App modules
from app        import app, lm, bc
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
        return render_template( 'cutoff_calci.html' )
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
    filtered_data = dataset[(float(cutoff) >= dataset[community_column]) &
                           (dataset['Branch_Code'] == branch)]
    
    print(filtered_data)

    # Drop duplicate rows based on College_Name
    filtered_data.drop_duplicates(subset=['College_Name'], keep='first', inplace=True)

    # Select only the specified columns
    selected_columns = ['College_Code', 'College_Name', 'Branch_Code', 'Branch_Name', community_column, 'Placement_Percentage']
    filtered_data = filtered_data[selected_columns]

    # Convert filtered data to HTML table
    table_html = filtered_data.to_html(index=False, classes='table table-striped')

    return render_template('recommendations.html', table_data=table_html, comm=community_column)

@app.route('/export_excel', methods=['POST'])
def export_excel():
    try:
        # Get the HTML table data from the POST request
        html_table = request.form.get('html_table')

        if html_table:
            # Parse HTML table using BeautifulSoup
            soup = BeautifulSoup(html_table, 'html.parser')
            table = soup.find('table')

            if table:
                # Convert HTML table to pandas DataFrame
                df = pd.read_html(str(table))[0]  # Assuming there's only one table
                
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                print(datetime.now())
                print(timestamp)
                # Define the file path for saving the Excel file
                file_name = f'table_data_{timestamp}.xlsx'
                file_path = os.path.join(os.getcwd(), 'app\media', file_name)  # Adjust as needed

                # Export DataFrame to Excel
                with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)

                # Create response object
                response = make_response()
                
                # Set headers for file download
                response.headers['Content-Disposition'] = f'attachment; filename={file_name}'
                response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

                # Send the file as a response
                return send_file(file_path, as_attachment=True, attachment_filename=file_name)
            else:
                return "No table found in HTML data"
        else:
            return "No HTML table data received"
    except Exception as e:
        print("Error:", e)  # Print out any error that occurs for debugging
        return "Error occurred while exporting to Excel"

@app.route('/stats', methods=['POST'])
@cross_origin()
def pie_chart():
    # Get HTML table data from POST request
    html_table = request.form.get('html_table')

    # Convert HTML table to DataFrame
    table_data = pd.read_html(io.StringIO(html_table))[0]

    print('^^')
    print(table_data)

    chart_data = [['College Name', 'Placement Percentage']]
    for index, row in table_data.iterrows():
        chart_data.append([row['College_Name'], row['Placement_Percentage']])

    # Convert chart data to JSON string
    chart_data_json = json.dumps(chart_data)

    print('0_0')
    print(chart_data_json)

    return render_template('statistics.html', chart_data_json=chart_data_json)
