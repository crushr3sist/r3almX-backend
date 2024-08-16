import logging
import subprocess

import uvicorn

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    subprocess.Popen("fastapi dev r3almX_backend --host=0.0.0.0 --port=8000")

    # uvicorn.run(
    #     "r3almX_backend:r3almX",
    #     host="0.0.0.0",
    #     port=8000,
    #     reload=True,
    #     use_colors=True,
    #     log_level="info",
    #     access_log=True,
    # )
