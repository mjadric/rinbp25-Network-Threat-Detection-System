from app import app
from routes import init_routes

if __name__ == "__main__":
    init_routes(app)
    app.run(host="0.0.0.0", port=5000, debug=True)
