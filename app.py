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
    # 1. Check if the file part exists
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # 2. Check if user selected a file
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # 3. Save and Process
    if file and file.filename.endswith('.pdf'):
        # Correctly use tempfile for cloud compatibility
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, 'uploaded_syllabus.pdf')
        
        try:
            file.save(filepath)
            
            # Pass the absolute path to your AI function
            result = chat(filepath)
            
            # Clean up: delete the temp file after reading
            os.remove(filepath)
            
            return jsonify(json.loads(result)), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)