import logging
import subprocess

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    subprocess.Popen("fastapi dev r3almX_backend.main:r3almX  --port=8080")
