import logging
import subprocess

import uvicorn


def ip_addy():
    ip = (
        subprocess.check_output("ipconfig")
        .decode("utf-8")
        .split("IPv4 Address. . . . . . . . . . . : ")[2]
        .split("Subnet Mask")[0]
    )
    return f"\nserver running on : https://{ip.strip()}:8000\n"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    uvicorn.run(
        "r3almX_backend:r3almX",
        host="0.0.0.0",
        port=8000,
        reload=True,
        use_colors=True,
        log_level="info",
        access_log=True,
    )
