import hashlib
import hmac
import json
import os
import tempfile
import threading
from datetime import datetime, timezone

import pymupdf
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import APIError, APITimeoutError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix
from ai import chat
from quotas import QuotaUnavailable, reserve

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 + 65536
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
CORS(app, origins=os.getenv('ALLOWED_ORIGINS', 'https://pierceseigne.com').split(','))
processing = threading.BoundedSemaphore(1)


def configured():
    return all(os.getenv(key) for key in ('OPENAI_API_KEY', 'UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN', 'RATE_LIMIT_SALT'))


@app.get('/health')
def health():
    return jsonify(status='ok', uploads_enabled=configured())


@app.errorhandler(RequestEntityTooLarge)
def too_large(_error):
    return jsonify(error='Choose a PDF smaller than 10 MB.'), 413


@app.post('/upload')
def upload():
    if not configured():
        return jsonify(error='Uploads are unavailable. You can still explore the example syllabi.'), 503
    file = request.files.get('file')
    if not file or not file.filename or not file.filename.lower().endswith('.pdf'):
        return jsonify(error='Choose a PDF syllabus.'), 400
    with tempfile.TemporaryDirectory(prefix='syllabus-') as folder:
        path = os.path.join(folder, 'syllabus.pdf')
        file.save(path)
        if os.path.getsize(path) > 10 * 1024 * 1024:
            return too_large(None)
        try:
            with pymupdf.open(path) as document:
                if not document.is_pdf or document.needs_pass or not 1 <= document.page_count <= 30:
                    return jsonify(error='Choose an unlocked PDF with 1–30 pages.'), 400
        except (RuntimeError, ValueError):
            return jsonify(error='This file could not be read as a PDF.'), 400
        if not processing.acquire(blocking=False):
            return jsonify(error='The analyzer is busy. Try again in a moment.'), 429, {'Retry-After': '30'}
        try:
            visitor = hmac.new(os.environ['RATE_LIMIT_SALT'].encode(), (request.remote_addr or 'unknown').encode(), hashlib.sha256).hexdigest()
            day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            if not reserve(day, visitor):
                return jsonify(error='The daily upload limit has been reached. Explore an example syllabus or return tomorrow.'), 429
            return jsonify(json.loads(chat(path)))
        except QuotaUnavailable:
            return jsonify(error='Uploads are temporarily unavailable. Please explore an example syllabus.'), 503
        except APITimeoutError:
            return jsonify(error='Analysis took too long. Please try again later.'), 504
        except APIError:
            app.logger.warning('AI provider request failed')
            return jsonify(error='The analysis service is temporarily unavailable.'), 503
        except ValueError:
            return jsonify(error='This PDF could not be analyzed. Try a shorter, text-based syllabus.'), 400
        except Exception:
            app.logger.exception('Syllabus processing failed')
            return jsonify(error='This syllabus could not be processed.'), 500
        finally:
            processing.release()


if __name__ == '__main__':
    app.run(port=5001)
