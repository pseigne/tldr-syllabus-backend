from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from ai import chat, parsePDF
import json

import tempfile # Add this at the top



    # ... rest of your code

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})




@app.route('/upload', methods=['POST'])
def upload_file():
    if file and file.filename.endswith('.pdf'):
        # Create a temporary file path
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, 'uploaded_syllabus.pdf')
        
        file.save(filepath)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.pdf'):
        # Save temporarily
        filepath = 'uploaded_syllabus.pdf'
        file.save(filepath)
        
        # Process with AI
        result = chat(filepath)
        return jsonify(json.loads(result)), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)