from shop.orders import Item, Order


def test_total_with_discount_and_shipping():
    o = Order('A1', [Item('mug', 300, 2), Item('tea', 200)], shipping_fee=50, discount_pct=10)
    assert o.items_total() == 800
    assert o.discount() == 80
    assert o.total() == 770


def test_empty_order():
    assert Order('A2').total() == 0
