import pytest

from app.services.order_service import build_order


MENU = {
    "currency": "EUR",
    "categories": [
        {"id": "drinks", "name": "Drinks", "items": [
            {"id": "bier", "name": "Bier", "price": 4.0, "deposit": 2.0},
            {"id": "wasser", "name": "Wasser", "price": 2.5},
            {"id": "sponsor-essen", "name": "Gratis Essen", "price": 0.0},
        ]},
    ],
}


def test_build_order_handles_gratis_items():
    order = build_order(MENU, [{"id": "sponsor-essen", "quantity": 2}])
    assert order["subtotal"] == 0.0
    assert order["deposit_total"] == 0.0
    assert order["total"] == 0.0
    assert order["items"][0]["unit_price"] == 0.0
    assert order["items"][0]["line_total"] == 0.0


def test_build_order_sums_correctly():
    order = build_order(MENU, [{"id": "wasser", "quantity": 3}])
    assert order["total"] == 7.5
    assert order["subtotal"] == 7.5
    assert order["deposit_total"] == 0.0
    assert order["items"][0]["line_total"] == 7.5
    assert order["items"][0]["deposit"] == 0.0


def test_build_order_includes_deposit():
    order = build_order(MENU, [{"id": "bier", "quantity": 2}])
    assert order["subtotal"] == 8.0
    assert order["deposit_total"] == 4.0
    assert order["total"] == 12.0
    assert order["items"][0]["unit_price"] == 4.0
    assert order["items"][0]["deposit"] == 2.0
    assert order["items"][0]["line_total"] == 12.0


def test_build_order_mixed_deposit_and_plain():
    order = build_order(
        MENU,
        [{"id": "bier", "quantity": 2}, {"id": "wasser", "quantity": 1}],
    )
    assert order["subtotal"] == 10.5
    assert order["deposit_total"] == 4.0
    assert order["total"] == 14.5


def test_build_order_without_tendered_has_no_change():
    order = build_order(MENU, [{"id": "wasser", "quantity": 2}])
    assert order["tendered"] is None
    assert order["change"] is None


def test_build_order_with_tendered_calculates_change():
    order = build_order(MENU, [{"id": "bier", "quantity": 1}], tendered=10.0)
    assert order["total"] == 6.0
    assert order["tendered"] == 10.0
    assert order["change"] == 4.0


def test_build_order_with_tendered_short_returns_negative_change():
    order = build_order(MENU, [{"id": "bier", "quantity": 2}], tendered=5.0)
    assert order["total"] == 12.0
    assert order["change"] == -7.0


def test_build_order_unknown_item_raises():
    with pytest.raises(ValueError):
        build_order(MENU, [{"id": "zigarre", "quantity": 1}])


def test_build_order_empty_raises():
    with pytest.raises(ValueError):
        build_order(MENU, [])
