import os
import logging
import threading
from flask import Flask

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a minimal in-memory database for local development
class LocalDB:
    def __init__(self):
        self.session_instance = self
        self.Model = object  # Base class for models
    
    def session(self):
        return self.session_instance
    
    def init_app(self, app):
        logger.info("Using in-memory database for local development")
    
    def create_all(self):
        logger.info("Creating in-memory data structures")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def add(self, obj):
        # Do nothing, simulated add
        pass
    
    def commit(self):
        # Do nothing, simulated commit
        pass
    
    def query(self, model):
        # Return empty results for any query
        class QueryResult:
            def filter(self, *args, **kwargs):
                return self
            
            def filter_by(self, **kwargs):
                return self
                
            def order_by(self, *args):
                return self
                
            def first(self):
                return None
                
            def all(self):
                return []
                
            def limit(self, n):
                return []
        
        return QueryResult()

# Create a global instance of the local database
db = LocalDB()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Initialize the app with our local database
db.init_app(app)

# Create background thread for simulation and monitoring
simulation_thread = None
monitoring_active = False

# Function to start the monitoring and simulation in a background thread
def start_background_tasks():
    global simulation_thread, monitoring_active
    
    if simulation_thread is None or not simulation_thread.is_alive():
        from network_simulation import start_simulation
        from attack_detector import start_monitoring
        
        def run_background_tasks():
            logger.info("Starting background tasks")
            # Start network simulation
            start_simulation()
            # Start attack monitoring
            start_monitoring()
            
        simulation_thread = threading.Thread(target=run_background_tasks)
        simulation_thread.daemon = True
        simulation_thread.start()
        monitoring_active = True
        logger.info("Background tasks started")

# Register routes
def register_routes():
    from routes import init_routes
    init_routes(app)
    logger.info("Routes registered")

# Create database tables
with app.app_context():
    # Import models so SQLAlchemy can create tables
    from models import NetworkStats, AttackEvent, NetworkNode, NetworkEdge
    
    # Create tables if they don't exist
    db.create_all()
    
    # Initialize the database handlers
    from database_handlers import init_mongo_db, init_neo4j_db
    init_mongo_db()
    init_neo4j_db()
    
    # Register Flask routes
    register_routes()
    
    # Start the background tasks
    start_background_tasks()
