from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from ai import chat
import json
import tempfile
from pathlib import Path


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


BASE_DIR = Path(__file__).resolve().parents[1]
TESTS_DIR = BASE_DIR / "tests"


def _resolve_local_test_pdf(filename: str) -> Path:
    """Resolve a local test PDF safely to prevent path traversal."""
    candidate = (TESTS_DIR / filename).resolve()
    if TESTS_DIR.resolve() not in candidate.parents:
        raise ValueError("Invalid file path")
    if not candidate.exists() or candidate.suffix.lower() != ".pdf":
        raise FileNotFoundError("PDF not found in tests directory")
    return candidate


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
    if file and file.filename.lower().endswith('.pdf'):
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


@app.route('/test-files', methods=['GET'])
def list_test_files():
    if not TESTS_DIR.exists():
        return jsonify({'error': 'tests directory not found'}), 404

    files = sorted([p.name for p in TESTS_DIR.glob('*.pdf')])
    return jsonify({'files': files}), 200


@app.route('/analyze-local', methods=['GET'])
def analyze_local_file():
    filename = request.args.get('file', '').strip()
    if not filename:
        return jsonify({'error': "Missing 'file' query parameter"}), 400

    try:
        filepath = _resolve_local_test_pdf(filename)
        result = chat(str(filepath))
        return jsonify(json.loads(result)), 200
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# @app.route('/save-local', methods=['GET'])
# def save_local_file():
#     """Analyze a PDF from the `tests` directory and save the parsed JSON to disk.

#     This endpoint does not return the parsed JSON content—only a status message.
#     Use the `file` query parameter to pick a file from the `tests` folder.
#     """
#     filename = request.args.get('file', '').strip()
#     if not filename:
#         return jsonify({'error': "Missing 'file' query parameter"}), 400

#     try:
#         filepath = _resolve_local_test_pdf(filename)
#         result = chat(str(filepath))

#         # Ensure output dir exists inside repository
#         out_dir = BASE_DIR / 'saved_outputs'
#         out_dir.mkdir(parents=True, exist_ok=True)

#         out_path = out_dir / (Path(filename).stem + '.json')
#         with open(out_path, 'w') as f:
#             f.write(result)

#         return jsonify({'message': f'Saved parsed syllabus to {str(out_path)}'}), 200
#     except FileNotFoundError as e:
#         return jsonify({'error': str(e)}), 404
#     except ValueError as e:
#         return jsonify({'error': str(e)}), 400
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)