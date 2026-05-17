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

    from .services.db import init_db, maybe_migrate_orders_json
    init_db(app.config["DB_PATH"])
    maybe_migrate_orders_json(app.config["DB_PATH"], app.config["ORDERS_PATH"])

    from .routes.orders import bp as orders_bp
    from .routes.menu import bp as menu_bp
    from .routes.health import bp as health_bp
    from .routes.printers import bp as printers_bp
    from .routes.reports import bp as reports_bp
    from .routes.admin import bp as admin_bp

    app.register_blueprint(orders_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(printers_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    return app
