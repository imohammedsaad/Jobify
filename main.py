from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, session
import os

from functions.generate_interview_cheatsheet import generate_interview_cheatsheet
from test import sample_json


# Initialize the Flask app
app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'tmp/'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = '6805a71287fb994a13386a341e148d09'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    # return render_template('result.html', cheatsheet=sample_json)
    return render_template('index.html')


@app.route('/cheatsheet', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect('/')

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect('/')

        try:
            if file and allowed_file(file.filename):
                file_data = BytesIO(file.read())
                job_description = request.form.get('jobDescription', '').strip()

                if not job_description:
                    flash('Job description is required.')
                    return redirect('/')

                cheatsheet_data = generate_interview_cheatsheet(file_data, job_description)
                session['cheatsheet_data'] = cheatsheet_data  # Store in session
                
                return render_template('result.html', cheatsheet=cheatsheet_data)
            else:
                flash('Invalid file format. Only PDF files are allowed.')
                return redirect('/')

        except Exception as e:
            print(f"Error processing request: {str(e)}")
            flash(f"Error processing request: {str(e)}")
            return redirect('/')

    return render_template('index.html')

@app.route('/favicon.png')
def favicon():
    return app.send_static_file('favicon.png')

@app.route('/skills')
def skills_page():
    if 'cheatsheet_data' not in session:
        flash('Please upload your resume first')
        return redirect(url_for('index'))
    
    cheatsheet_data = session.get('cheatsheet_data')
    return render_template('skills.html', cheatsheet=cheatsheet_data)

@app.route('/swot')
def swot_page():
    if 'cheatsheet_data' not in session:
        flash('Please upload your resume first')
        return redirect(url_for('index'))
    
    cheatsheet_data = session.get('cheatsheet_data')
    return render_template('swot.html', cheatsheet=cheatsheet_data)


if __name__ == '__main__':
    app.run()