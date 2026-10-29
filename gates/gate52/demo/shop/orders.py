"""Orders in a small online shop (prices in whole rupees)."""
from dataclasses import dataclass, field


@dataclass
class Item:
    name: str
    price: int          # rupees per unit
    qty: int = 1


@dataclass
class Order:
    id: str
    items: list = field(default_factory=list)
    shipping_fee: int = 0
    discount_pct: int = 0          # a discount code, as a percentage off the items
    paid_with: str = 'card'        # 'card' or 'store_credit'
    final_sale: bool = False

    def items_total(self):
        return sum(i.price * i.qty for i in self.items)

    def discount(self):
        return self.items_total() * self.discount_pct // 100

    def total(self):
        return self.items_total() - self.discount() + self.shipping_fee
