import unittest
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/example', methods=['GET'])
def example():
    return jsonify({'message': 'Hello, World!'}), 200

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_example_route(self):
        response = self.app.get('/api/example')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'message': 'Hello, World!'})

if __name__ == '__main__':
    unittest.main()