import io
import os
import unittest
from unittest.mock import patch
import pymupdf
import app as service
from quotas import QuotaUnavailable


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-only', 'UPSTASH_REDIS_REST_URL': 'https://example.invalid',
            'UPSTASH_REDIS_REST_TOKEN': 'test-only', 'RATE_LIMIT_SALT': 'test-salt',
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.client = service.app.test_client()

    def pdf(self, pages=1):
        document = pymupdf.open()
        for _ in range(pages):
            document.new_page().insert_text((50, 50), 'Example syllabus')
        data = document.tobytes()
        document.close()
        return io.BytesIO(data)

    def upload(self, data=None):
        return self.client.post('/upload', data={'file': (data or self.pdf(), 'syllabus.pdf')})

    @patch('app.chat', return_value='{"course":{"title":"Example"}}')
    @patch('app.reserve', return_value=True)
    def test_success_cleans_up_file_and_hashes_ip(self, reserve, chat):
        response = self.upload()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['course']['title'], 'Example')
        self.assertFalse(os.path.exists(chat.call_args.args[0]))
        self.assertEqual(len(reserve.call_args.args[1]), 64)
        self.assertNotIn('127.0.0.1', reserve.call_args.args[1])

    @patch('app.chat')
    @patch('app.reserve')
    def test_invalid_documents_do_not_consume_quota(self, reserve, chat):
        for data in (io.BytesIO(b'not a PDF'), self.pdf(31)):
            self.assertEqual(self.upload(data).status_code, 400)
        reserve.assert_not_called()
        chat.assert_not_called()

    @patch('app.chat')
    @patch('app.reserve', return_value=False)
    def test_daily_limit_blocks_ai(self, reserve, chat):
        self.assertEqual(self.upload().status_code, 429)
        chat.assert_not_called()

    @patch('app.chat')
    @patch('app.reserve', side_effect=QuotaUnavailable())
    def test_quota_outage_fails_closed(self, reserve, chat):
        self.assertEqual(self.upload().status_code, 503)
        chat.assert_not_called()

    def test_missing_configuration_keeps_examples_only(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            self.assertFalse(self.client.get('/health').json['uploads_enabled'])
            self.assertEqual(self.upload().status_code, 503)

    def test_oversized_file(self):
        self.assertEqual(self.upload(io.BytesIO(b'x' * (10 * 1024 * 1024 + 1))).status_code, 413)

    def test_local_debug_endpoints_removed(self):
        self.assertEqual(self.client.get('/analyze-local?file=test.pdf').status_code, 404)
        self.assertEqual(self.client.get('/test-files').status_code, 404)

    def test_cors_only_allows_portfolio(self):
        allowed = self.client.get('/health', headers={'Origin': 'https://pierceseigne.com'})
        denied = self.client.get('/health', headers={'Origin': 'https://example.invalid'})
        self.assertEqual(allowed.headers.get('Access-Control-Allow-Origin'), 'https://pierceseigne.com')
        self.assertIsNone(denied.headers.get('Access-Control-Allow-Origin'))


if __name__ == '__main__':
    unittest.main()
