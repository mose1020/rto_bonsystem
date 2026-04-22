from __future__ import annotations

from flask import Blueprint, current_app, render_template

from ..services.menu_service import load_menu


bp = Blueprint("menu", __name__)


@bp.get("/")
def index():
    menu = load_menu(current_app.config["MENU_PATH"])
    return render_template("order.html", menu=menu)


@bp.get("/api/menu")
def api_menu():
    menu = load_menu(current_app.config["MENU_PATH"])
    return menu
