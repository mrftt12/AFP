# /home/ubuntu/load_forecasting_webapp/src/main.py
import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src import create_app

# Create an instance of the app
app = create_app()

if __name__ == "__main__":
    # Use port 5000 for local dev, deployment tool will handle production port
    app.run(host="0.0.0.0", port=5000, debug=True)

