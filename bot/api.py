from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import logging
from database import Database
from api_config import APIConfig

logger = logging.getLogger(__name__)

class APIServer:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self.db = Database()
        self.config = APIConfig()
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/api/gifts/<slug>', methods=['GET'])
        def get_gift(slug):
            """Get gift data by slug"""
            try:
                gift_data = self.db.get_gift(slug)
                
                if not gift_data:
                    return jsonify({'error': 'Gift not found'}), 404
                
                return jsonify({
                    'success': True,
                    'data': gift_data['payload']
                })
                
            except Exception as e:
                logger.error(f"Error fetching gift {slug}: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({'status': 'healthy'})
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Endpoint not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500
    
    def run(self):
        """Run the API server"""
        self.app.run(
            host=self.config.API_HOST,
            port=self.config.API_PORT,
            debug=False,
            threaded=True
        )
    
    def start_in_thread(self):
        """Start the API server in a separate thread"""
        api_thread = threading.Thread(target=self.run, daemon=True)
        api_thread.start()
        logger.info(f"API server started on {self.config.API_HOST}:{self.config.API_PORT}")
        return api_thread

# For running the API server standalone
if __name__ == "__main__":
    api_server = APIServer()
    api_server.run()
