import time

import psycopg2
import sqlalchemy
from fastapi import FastAPI, Request, logger
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from .version import __version__


class RealmX(FastAPI):
    def __init__(self, *, title: str = "r3almX", description: str = "r3almX API"):
        super().__init__(
            title=title,
            version=str(__version__),
            description=description,
            tags_metadata=[
                {"name": "Auth", "description": "Auth Endpoints"},
                {"name": "Chat", "description": "Chat Endpoints"},
                {"name": "Invite", "description": "Invite Endpoints"},
                {"name": "Room", "description": "Room Endpoints"},
                {"name": "Channel", "description": "Channel Endpoints"},
            ],
        )
        self.add_models()
        self.add_routes()
        self.configure_middleware()

    def configure_middleware(self):
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*", "http://localhost:3000"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.add_middleware(SessionMiddleware, secret_key="feafawefawefawefawef")

    def add_routes(self):
        from r3almX_backend.auth_service.main import auth_router
        from r3almX_backend.chat_service.channel_system.main import channel_manager
        from r3almX_backend.chat_service.invite_system.main import invite_system
        from r3almX_backend.chat_service.room_service.main import rooms_service
        from r3almX_backend.realtime_service.main import realtime

        self.include_router(auth_router)
        self.include_router(realtime)

        self.include_router(rooms_service)
        self.include_router(invite_system)
        self.include_router(channel_manager)

    def add_models(self):
        try:

            from r3almX_backend.auth_service import user_models
            from r3almX_backend.chat_service.models import rooms_model
            from r3almX_backend.database import engine

            # rooms_model.Base.metadata.drop_all(bind=engine)
            # channels_model.Base.metadata.drop_all(bind=engine)
            # user_models.Base.metadata.drop_all(bind=engine)

            user_models.Base.metadata.create_all(bind=engine)
            # channels_model.Base.metadata.create_all(bind=engine)
            # rooms_model.Base.metadata.create_all(bind=engine)
        except (sqlalchemy.exc.OperationalError, psycopg2.OperationalError) as p:

            for _ in range(0, 5):
                try:
                    from r3almX_backend.auth_service import user_models
                    from r3almX_backend.chat_service.models import rooms_model
                    from r3almX_backend.database import engine

                    # rooms_model.Base.metadata.drop_all(bind=engine)
                    # channels_model.Base.metadata.drop_all(bind=engine)
                    # user_models.Base.metadata.drop_all(bind=engine)

                    user_models.Base.metadata.create_all(bind=engine)
                    # channels_model.Base.metadata.create_all(bind=engine)
                    # rooms_model.Base.metadata.create_all(bind=engine)
                except (
                    sqlalchemy.exc.OperationalError,
                    psycopg2.OperationalError,
                ) as p:
                    print("db connection hitch, retrying")
                    time.sleep(_ * 10)
                else:
                    break
            raise Exception("Your db failed to connect bre")


r3almX = RealmX()

# import json
# import logging
# import time
# from datetime import datetime
# from urllib.parse import parse_qs, urlparse

# from colorama import init
# from rich.console import Console
# from rich.json import JSON
# from rich.panel import Panel
# from rich.table import Table
# from rich.text import Text
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.requests import Request
# from starlette.responses import Response

# init(autoreset=True)

# # Initialize the logger
# logger = logging.getLogger("uvicorn")
# logger.setLevel(logging.INFO)

# # Initialize rich console
# console = Console()


# @r3almX.middleware("http")
# async def log_requests(request: Request, call_next):
#     start_time = time.time()

#     # Gathering request details
#     ip_address = request.client.host
#     user_agent = request.headers.get("User-Agent", "N/A")
#     referrer = request.headers.get("Referer", "N/A")
#     method = request.method
#     url = str(request.url)  # Convert URL object to string
#     headers = dict(request.headers)
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

#     # Optionally read the request body (Note: Be cautious with large bodies)
#     body = await request.body()
#     request_body = body.decode("utf-8") if body else "No Body"

#     # Process the request and get the response
#     response = await call_next(request)
#     response_time = time.time() - start_time
#     status_code = response.status_code

#     # Parse URL for additional context
#     parsed_url = urlparse(url)
#     query_params = parse_qs(parsed_url.query)

#     # Create a rich table for the request details
#     table = Table(show_header=True, header_style="bold magenta")
#     table.add_column("Attribute", style="dim")
#     table.add_column("Value", overflow="fold")

#     table.add_row("IP Address", f"[green]{ip_address}[/green]")
#     table.add_row("User Agent", f"[yellow]{user_agent}[/yellow]")
#     table.add_row("Referer", f"[blue]{referrer}[/blue]")
#     table.add_row("Request Method", f"[cyan]{method}[/cyan]")
#     table.add_row("Request URL", f"[link={url}]{url}[/link]")
#     table.add_row("Timestamp", f"[white]{timestamp}[/white]")
#     table.add_row("Response Time", f"[white]{response_time:.3f} seconds[/white]")
#     table.add_row(
#         "Response Status",
#         (
#             f"[bold green]{status_code}[/bold green]"
#             if status_code < 400
#             else f"[bold red]{status_code}[/bold red]"
#         ),
#     )

#     # Display parsed query parameters if any
#     if query_params:
#         query_panel = Panel.fit(
#             JSON(json.dumps(query_params, indent=2)),
#             title="Query Parameters",
#             border_style="magenta",
#         )
#     else:
#         query_panel = None

#     # Create rich JSON formatted headers and body
#     formatted_headers = JSON(json.dumps(headers, indent=2))
#     formatted_body = JSON(json.dumps({"body": request_body}, indent=2))

#     # Print each section separately with rich console for proper rendering
#     console.print(
#         Panel(
#             "[bold cyan]HTTP Request Log[/bold cyan]",
#             title="📘",
#             border_style="blue",
#             expand=False,
#         )
#     )

#     console.print(Panel.fit(table, title="Request Details", border_style="cyan"))

#     if query_panel:
#         console.print(query_panel)

#     console.print(Panel.fit(formatted_headers, title="Headers", border_style="yellow"))

#     console.print(Panel.fit(formatted_body, title="Request Body", border_style="green"))

#     return response
