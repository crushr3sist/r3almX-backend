import subprocess

subprocess.Popen("uvicorn dev src --port=8501", shell=True)
