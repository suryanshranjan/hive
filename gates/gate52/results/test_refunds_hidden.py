"""Hidden acceptance tests for the refunds feature, written from policy.md before any build. Never shown to builders."""
import pytest
from shop.orders import Item, Order
from shop.refunds import refund


def o(price=1000, qty=1, ship=100, disc=0, paid='card', final=False):
    return Order('X', [Item('thing', price, qty)], shipping_fee=ship, discount_pct=disc, paid_with=paid, final_sale=final)

CASES = [
    # (order kwargs, days, reason, amount, method)
    (dict(), 3, 'changed mind', 1000, 'card'),
    (dict(), 14, 'changed mind', 1000, 'card'),
    (dict(), 15, 'changed mind', 500, 'card'),
    (dict(), 30, 'changed mind', 500, 'card'),
    (dict(), 31, 'changed mind', 0, 'card'),
    (dict(), 5, 'damaged', 1100, 'card'),
    (dict(), 60, 'damaged', 1100, 'card'),
    (dict(), 90, 'damaged', 1100, 'card'),
    (dict(), 91, 'damaged', 0, 'card'),
    (dict(disc=10), 3, 'changed mind', 900, 'card'),
    (dict(disc=10), 20, 'changed mind', 450, 'card'),
    (dict(price=333, disc=0), 20, 'changed mind', 166, 'card'),
    (dict(final=True), 3, 'changed mind', 0, 'card'),
    (dict(final=True), 3, 'damaged', 1100, 'card'),
    (dict(price=40, ship=0), 3, 'changed mind', 0, 'card'),
    (dict(price=90, ship=0), 20, 'changed mind', 0, 'card'),
    (dict(price=40, ship=20), 3, 'damaged', 60, 'card'),
    (dict(paid='store_credit'), 3, 'changed mind', 1000, 'store_credit'),
    (dict(paid='store_credit'), 20, 'damaged', 1100, 'store_credit'),
    (dict(), -2, 'changed mind', 1000, 'card'),
    (dict(price=250, qty=4, disc=20), 10, 'changed mind', 800, 'card'),
    (dict(price=250, qty=4, disc=20), 25, 'changed mind', 400, 'card'),
]

@pytest.mark.parametrize('kw,days,reason,amount,method', CASES)
def test_refund(kw, days, reason, amount, method):
    got = refund(o(**kw), days, reason)
    assert got['amount'] == amount
    assert got['method'] == method
