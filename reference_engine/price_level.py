from __future__ import annotations

from typing import Iterator, Optional
from reference_engine.models import Order

# ---
# Doubly-Linked List Node representing an order wrapper in PriceLevelImpl
# ---

class PriceLevelNode:
    """A node in the PriceLevelImpl doubly-linked list wrapping an Order."""

    def __init__(self, order: Order) -> None:
        """Initializes a PriceLevelNode."""
        self._order = order
        self._prev: Optional[PriceLevelNode] = None
        self._next: Optional[PriceLevelNode] = None

    @property
    def order(self) -> Order:
        """Returns the Order object wrapped by this node."""
        return self._order

    @property
    def prev(self) -> Optional[PriceLevelNode]:
        """Returns the previous node in the list."""
        return self._prev

    @prev.setter
    def prev(self, node: Optional[PriceLevelNode]) -> None:
        """Sets the previous node in the list."""
        self._prev = node

    @property
    def next(self) -> Optional[PriceLevelNode]:
        """Returns the next node in the list."""
        return self._next

    @next.setter
    def next(self, node: Optional[PriceLevelNode]) -> None:
        """Sets the next node in the list."""
        self._next = node


# ---
# Price Level implementation maintaining order time priority
# ---

class PriceLevelImpl:
    """Manages active orders at a specific price level using a doubly-linked list."""

    def __init__(self, price: int) -> None:
        """Initializes the PriceLevelImpl."""
        self._price = price
        self._head: Optional[PriceLevelNode] = None
        self._tail: Optional[PriceLevelNode] = None
        self._order_map: dict[int, PriceLevelNode] = {}

    @property
    def price(self) -> int:
        """Returns the price associated with this level."""
        return self._price

    @property
    def total_quantity(self) -> int:
        """Returns the combined leaves quantity of all active orders at this price."""
        return sum(node.order.leaves_qty for node in self._order_map.values())

    @property
    def order_count(self) -> int:
        """Returns the number of active orders at this price level."""
        return len(self._order_map)

    def add_order(self, order: Order) -> None:
        """Appends an order to the end of the doubly-linked list (FIFO priority)."""
        if order.order_id in self._order_map:
            return
        node = PriceLevelNode(order)
        self._order_map[order.order_id] = node
        if not self._head:
            self._head = node
            self._tail = node
        else:
            assert self._tail is not None
            self._tail.next = node
            node.prev = self._tail
            self._tail = node

    def remove_order(self, order_id: int) -> Optional[Order]:
        """Removes an order by its identifier and returns it."""
        node = self._order_map.pop(order_id, None)
        if not node:
            return None
        if node.prev:
            node.prev.next = node.next
        else:
            self._head = node.next
        if node.next:
            node.next.prev = node.prev
        else:
            self._tail = node.prev
        node.prev = None
        node.next = None
        return node.order

    def reduce_quantity(self, order_id: int, qty: int) -> None:
        """Reduces the remaining quantity of a specific order in this level."""
        # Remaining quantity is managed by Order.fill or similar, but let's allow it or ensure it.
        pass

    def front(self) -> Optional[Order]:
        """Returns the front-most order (highest priority) in the queue without removing it."""
        return self._head.order if self._head else None

    def is_empty(self) -> bool:
        """Checks if there are no active orders at this price level."""
        return self._head is None

    def __iter__(self) -> Iterator[Order]:
        """Returns an iterator over the orders at this price level, front-to-back."""
        curr = self._head
        while curr:
            yield curr.order
            curr = curr.next

    def __len__(self) -> int:
        """Returns the number of orders in this price level."""
        return len(self._order_map)

