"""Deterministic sample report for the hackathon demo."""

DEMO_RESULT = {
    "shipment": {"origin": "China", "destination": "Kazakhstan"},
    "product": "Servers",
    "tnved": "8471",
    "customs_value": 55000,
    "duty": 5500,
    "vat": 7260,
    "total": 12760,
    "distance_km": 4200,
    "weight": 10,
    "transport_cost": 4850,
    "currency": "USD",
}


def demo_query() -> dict:
    """Return the demo request payload in the UI's neutral dictionary format."""
    return {"origin": "China", "destination": "Kazakhstan", "product": "Servers", "value": 50000, "weight": 10}
