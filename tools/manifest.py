def search_tn_ved_database(query: str, **kwargs) -> dict:
    query_lower = query.lower()
    if "сервер" in query_lower or "server" in query_lower:
        return {"tn_ved": "8471", "description": "Автоматические машины для обработки данных"}
    if "ноутбук" in query_lower or "laptop" in query_lower:
        return {"tn_ved": "8471", "description": "Портативные автоматические машины"}
    if "телефон" in query_lower or "phone" in query_lower:
        return {"tn_ved": "8517", "description": "Телефонные аппараты"}
    return {"tn_ved": "9999", "description": "Товары прочие"}


def calculate_customs_duties(
    customs_value: float,
    tn_ved: str = "8471",
    country_origin: str = "CN",
    country_dest: str = "KZ",
    **kwargs
) -> dict:
    duty_rates = {
        "8471": 0.0,
        "8517": 0.0,
        "9999": 0.05,
    }
    vat_rate = 0.12
    duty_rate = duty_rates.get(tn_ved[:4], 0.05)

    duty = customs_value * duty_rate
    vat_base = customs_value + duty
    vat = vat_base * vat_rate
    total = duty + vat

    return {
        "customs_value": customs_value,
        "duty": duty,
        "vat": vat,
        "total": total,
        "duty_rate": duty_rate,
        "vat_rate": vat_rate,
    }


def calculate_logistics_cost(
    weight_kg: float,
    volume_m3: float = 0,
    origin: str = "China",
    destination: str = "Kazakhstan",
    transport_type: str = "rail",
    **kwargs
) -> dict:
    rates = {
        "rail": 2.5,
        "truck": 3.5,
        "air": 15.0,
        "sea": 1.5,
    }
    rate = rates.get(transport_type, 2.5)
    base_cost = weight_kg * rate

    if volume_m3 > 0:
        volumetric_weight = volume_m3 * 167
        base_cost = max(base_cost, volumetric_weight * rate)

    return {
        "cost": base_cost,
        "currency": "USD",
        "transport_type": transport_type,
        "origin": origin,
        "destination": destination,
    }


TOOL_MANIFEST = {
    "search_tn_ved_database": search_tn_ved_database,
    "calculate_customs_duties": calculate_customs_duties,
    "calculate_logistics_cost": calculate_logistics_cost,
}