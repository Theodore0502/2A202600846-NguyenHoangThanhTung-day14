import json
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

class ShoppingDataStore:
    """Student scaffold for mock-data lookup."""

    def __init__(self, json_path: Path) -> None:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.metadata = data.get("metadata", {})
        self.customers = data.get("customers", [])
        self.orders = data.get("orders", [])
        self.vouchers = data.get("vouchers", [])

        # Build indexes
        self.customer_by_id = {c["customer_id"]: c for c in self.customers}
        self.order_by_id = {o["order_id"]: o for o in self.orders}
        
        self.orders_by_customer_id = {}
        for o in self.orders:
            cid = o.get("customer_id")
            if cid:
                if cid not in self.orders_by_customer_id:
                    self.orders_by_customer_id[cid] = []
                self.orders_by_customer_id[cid].append(o)
                
        self.vouchers_by_customer_id = {}
        for v in self.vouchers:
            cid = v.get("customer_id")
            if cid:
                if cid not in self.vouchers_by_customer_id:
                    self.vouchers_by_customer_id[cid] = []
                self.vouchers_by_customer_id[cid].append(v)

    def get_customer_by_id(self, customer_id: str) -> dict[str, Any]:
        customer = self.customer_by_id.get(customer_id)
        if customer:
            return {"status": "ok", "customer": customer}
        return {"status": "not_found", "customer_id": customer_id}

    def get_orders_by_customer_id(self, customer_id: str, limit: int = 10) -> dict[str, Any]:
        orders = self.orders_by_customer_id.get(customer_id, [])
        # Sort by created_at descending if possible
        orders = sorted(orders, key=lambda x: x.get("created_at", ""), reverse=True)
        orders = orders[:limit]
        if orders:
            return {"status": "ok", "orders": orders}
        return {"status": "not_found", "customer_id": customer_id}

    def get_order_detail_by_order_id(self, order_id: str) -> dict[str, Any]:
        order = self.order_by_id.get(order_id)
        if order:
            return {"status": "ok", "order": order}
        return {"status": "not_found", "order_id": order_id}

    def get_vouchers_by_customer_id(
        self,
        customer_id: str,
        only_active: bool = False,
    ) -> dict[str, Any]:
        vouchers = self.vouchers_by_customer_id.get(customer_id, [])
        if only_active:
            vouchers = [v for v in vouchers if v.get("status") == "active"]
        
        if vouchers:
            return {"status": "ok", "vouchers": vouchers}
        return {"status": "not_found", "customer_id": customer_id}


def build_data_tools(store: ShoppingDataStore) -> list:
    @tool
    def get_customer_by_id(customer_id: str) -> dict[str, Any]:
        """Fetch customer profile information using their unique customer ID."""
        return store.get_customer_by_id(customer_id)

    @tool
    def get_orders_by_customer_id(customer_id: str, limit: int = 10) -> dict[str, Any]:
        """Fetch a list of recent orders for a specific customer using their customer ID."""
        return store.get_orders_by_customer_id(customer_id, limit)

    @tool
    def get_order_detail_by_order_id(order_id: str) -> dict[str, Any]:
        """Fetch the detailed information of a specific order using its order ID."""
        return store.get_order_detail_by_order_id(order_id)

    @tool
    def get_vouchers_by_customer_id(customer_id: str, only_active: bool = False) -> dict[str, Any]:
        """Fetch vouchers associated with a customer ID. Set only_active to True to filter only active/usable vouchers."""
        return store.get_vouchers_by_customer_id(customer_id, only_active)

    return [
        get_customer_by_id,
        get_orders_by_customer_id,
        get_order_detail_by_order_id,
        get_vouchers_by_customer_id,
    ]
