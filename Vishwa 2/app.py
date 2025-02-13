from flask import Flask, request, render_template, redirect, url_for, flash, session,jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Connection
client = MongoClient('mongodb://localhost:27017/')
db = client['job_portal']

# Ensure the upload directory exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_ADDRESS = 'your_email@example.com'
EMAIL_PASSWORD = 'your_email_password'




@app.route('/')
def home():
    return render_template('index.html')

@app.route('/emregister')
def emregister():
    return render_template('Emregister.html')

@app.route('/jobregister')
def jobregister():
    return render_template('Jobregister.html')



@app.route('/contact')
def contact():
    return render_template('contant.html')


@app.route('/emcontact')
def emcontact():
    return render_template('emcontact.html')


@app.route('/freecourse')
def freecourse():
    return render_template('freecourse.html')


@app.route('/register_employee', methods=['POST'])
def register_employee():
    data = request.form.to_dict()
    files = request.files

    # Check if email or phone already exists
    existing_user = db.employees.find_one({
        '$or': [
            {'email': data.get('email')},
            {'phone': data.get('phone')}
        ]
    })

    if existing_user:
        error_message = f"User with email {data.get('email')} or phone {data.get('phone')} is already registered!"
        return render_template('Emregister.html', error_message=error_message, form_data=data)

    # Handle file uploads
    if files:
        profile_photo = files.get('profile_photo')
        resume_photo = files.get('resume_photo')
        if profile_photo:
            profile_photo.save(os.path.join(UPLOAD_FOLDER, profile_photo.filename))
            data['profile_photo_path'] = profile_photo.filename
        if resume_photo:
            resume_photo.save(os.path.join(UPLOAD_FOLDER, resume_photo.filename))
            data['resume_photo_path'] = resume_photo.filename

    # Insert new employee data into the database
    db.employees.insert_one(data)

    # Redirect to the employee login page
    return redirect(url_for('emlogin'))

@app.route('/register_job', methods=['POST'])
def register_job():
    data = request.form.to_dict()
    logo = request.files.get('logo')
    if logo and logo.filename:
        filename = secure_filename(logo.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logo.save(file_path)
        data['logo_path'] = f"uploads/{filename}"

    db.jobs.insert_one(data)
    return redirect(url_for('joblogin'))



@app.route('/emlogin', methods=['GET', 'POST'])
def emlogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = db.employees.find_one({'email': email})
        if user and user['password'] == password:
            session['email'] = email
            flash('Login successful', 'success')
            return redirect(url_for('emhome'))
        flash('Invalid email or password', 'danger')
    return render_template('emlogin.html')

@app.route('/joblogin', methods=['GET', 'POST'])
def joblogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Query the jobs collection
        user = db.jobs.find_one({'email': email})
        
        if user:
            if user.get('password') == password:
                session['email'] = email
                flash('Login successful', 'success')
                return redirect(url_for('jobhome'))
            else:
                flash('Invalid password', 'danger')
        else:
            flash('Invalid email', 'danger')
    
    return render_template('joblogin.html')

@app.route('/emhome')
def emhome():
    if 'email' not in session:
        return redirect(url_for('emlogin'))

    email = session['email']
    employee = db.employees.find_one({'email': email})

    if not employee:
        flash("Employee not found. Please contact support.")
        return redirect(url_for('emlogin'))

    # Retrieve query parameters for filtering
    location_filter = request.args.get('location', '').strip()
    job_name_filter = request.args.get('job_name', '').strip()

    # Build query
    query = {}
    if location_filter:
        query['location'] = {'$regex': location_filter, '$options': 'i'}
    if job_name_filter:
        query['job_name'] = {'$regex': job_name_filter, '$options': 'i'}

    jobs = list(db.job_posts.find(query))
    return render_template(
        'emhome.html',
        full_name=employee.get('full_name', 'User'),
        email=email,
        jobs=jobs
    )



@app.route('/apply/<job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    if 'email' not in session:
        return redirect(url_for('emlogin'))

    email = session['email']
    employee = db.employees.find_one({'email': email})

    job = db.job_posts.find_one({'_id': ObjectId(job_id)})
    if not job:
        flash('Job not found!', 'danger')
        return redirect(url_for('emhome'))

    application = {
        'job_id': str(job['_id']),
        'job_name': job.get('job_name'),
        'company_email': job.get('company_email'),
        'employee_email': email,
        'employee_details': {
            'full_name': employee.get('full_name'),
            'email': employee.get('email'),
            'phone': employee.get('phone'),
            'address': employee.get('address'),
            'skills': employee.get('skills'),
            'work_experience': employee.get('work_experience'),
            'tenth_percentage': employee.get('tenth_percentage'),
            'twelfth_percentage': employee.get('twelfth_percentage'),
            'degree_cgpa': employee.get('degree_cgpa'),
            'professional_summary': employee.get('professional_summary'),
            'salary_expectations': employee.get('salary_expectations'),
            'employment_type': employee.get('employment_type'),
            'references': employee.get('references'),
            'profile_photo_path': employee.get('profile_photo_path'),
            'resume_photo_path': employee.get('resume_photo_path')
        }
    }

    db.job_applications.insert_one(application)
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('emhome'))


@app.route('/addjob', methods=['GET', 'POST'])
def add_job():
    # Check if the user is logged in
    if 'email' not in session:
        return redirect(url_for('joblogin'))

    # Handle form submission
    if request.method == 'POST':
        # Collect the job details from the form
        data = request.form.to_dict()

        # Get the company email from the session
        company_email = session.get('email')

        # Fetch the company details from the database using the company email
        company = db.jobs.find_one({'email': company_email})

        if not company:
            flash('Company not found!', 'danger')
            return redirect(url_for('jobhome'))

        # Add company email and company name to the job post data
        data['company_email'] = company_email
        data['company_name'] = company.get('company_name', 'Unknown Company')

        # Insert the job post into the database
        db.job_posts.insert_one(data)

        flash('Job added successfully!', 'success')
        return redirect(url_for('jobhome'))  # Redirect back to the job home page

    # Retrieve the company details from the database using the logged-in user's email
    email = session.get('email')
    company = db.jobs.find_one({'email': email})

    # Ensure company data is found and pass relevant fields to the template
    company_name = company.get('company_name', 'Unknown Company')
    industry = company.get('industry', 'Unknown Industry')
    location = company.get('location', 'Unknown Location')
    logo_path = company.get('logo_path', 'uploads/default.png') if company else 'uploads/default.png'
    
    # Pass the company details to the template
    return render_template(
        'Addjob.html',
        company_name=company_name,
        industry=industry,
        location=location,
        logo_path=logo_path
    )


@app.route('/jobhome')
def jobhome():
    if 'email' not in session:
        return redirect(url_for('joblogin'))

    email = session['email']
    company = db.jobs.find_one({'email': email})
    job_requests = list(db.job_applications.find({'company_email': email}))

    for job_request in job_requests:
        employee_details = job_request.get('employee_details', {})
        employee_details.setdefault('profile_photo_path', '../static/uploads/default_profile.png')
        employee_details.setdefault('resume_photo_path', '../static/uploads/default_resume.png')

    return render_template(
        'jobhome.html',
        company_name=company.get('company_name', 'Unknown Company'),
        logo_path=company.get('logo_path', '../static/uploads/default.png'),
        job_requests=job_requests
    )
    



@app.route('/approve_application/<application_id>', methods=['POST'])
def approve_application(application_id):
    try:
        # Update the application's status to "approved"
        result = db.job_applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {'status': 'approved'}}
        )
        if result.matched_count > 0:
            return jsonify({'success': True, 'message': 'Application approved.'})
        else:
            return jsonify({'success': False, 'message': 'Application not found.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Reject an application
@app.route('/reject_application/<application_id>', methods=['POST'])
def reject_application(application_id):
    try:
        # Update the application's status to "rejected"
        result = db.job_applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {'status': 'rejected'}}
        )
        if result.matched_count > 0:
            return jsonify({'success': True, 'message': 'Application rejected.'})
        else:
            return jsonify({'success': False, 'message': 'Application not found.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Display all applications
@app.route('/display', methods=['GET'])
def display():
    approved = list(db.job_applications.find({'status': 'approved'}))
    rejected = list(db.job_applications.find({'status': 'rejected'}))
    return render_template('display.html', approved=approved, rejected=rejected)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
