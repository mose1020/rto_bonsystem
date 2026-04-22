import pytest

from app.services.order_service import build_order


MENU = {
    "currency": "EUR",
    "categories": [
        {"id": "drinks", "name": "Drinks", "items": [
            {"id": "bier", "name": "Bier", "price": 4.0},
        ]},
    ],
}


def test_build_order_sums_correctly():
    order = build_order(MENU, [{"id": "bier", "quantity": 3}])
    assert order["total"] == 12.0
    assert order["items"][0]["line_total"] == 12.0


def test_build_order_unknown_item_raises():
    with pytest.raises(ValueError):
        build_order(MENU, [{"id": "zigarre", "quantity": 1}])


def test_build_order_empty_raises():
    with pytest.raises(ValueError):
        build_order(MENU, [])
