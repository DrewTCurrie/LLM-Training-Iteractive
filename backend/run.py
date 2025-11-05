from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables from .env file
# Make sure we're loading from the correct path
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

print(f"Loading .env from: {env_path}")
print(f"N_GPU_LAYERS from env: {os.getenv('N_GPU_LAYERS')}")

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
