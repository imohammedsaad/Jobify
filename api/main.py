from flask import Flask, render_template, request, jsonify
import os
from functions.generate_interview_cheatsheet import generate_interview_cheatsheet
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Create uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Generate cheatsheet from the uploaded file
            result = generate_interview_cheatsheet(filepath)
            
            # Clean up - delete the uploaded file
            os.remove(filepath)
            
            if result:
                return jsonify(result)
            else:
                return jsonify({'error': 'Error generating cheatsheet'}), 500
                
        except Exception as e:
            # Clean up in case of error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
