from __future__ import annotations

import logging
from flask import Flask

from .config import Config


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config or Config())

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    from .routes.orders import bp as orders_bp
    from .routes.menu import bp as menu_bp
    from .routes.health import bp as health_bp

    app.register_blueprint(orders_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(health_bp)

    return app
