import logging
import subprocess

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # subprocess.Popen("granian --interface asgi r3almX_backend:r3almX  --port=8000")
    subprocess.Popen("fastapi dev r3almX_backend  --port=8000")

    # uvicorn.run(
    #     "r3almX_backend:r3almX",
    #     host="0.0.0.0",
    #     port=8000,
    #     reload=True,
    #     use_colors=True,
    #     log_level="info",
    #     access_log=True,
    # )
