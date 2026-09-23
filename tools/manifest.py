from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
import logging

logger = logging.getLogger(__name__)


class TNVEDSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Product name or description to search for")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        return v.strip().lower()


class TNVEDSearchResponse(BaseModel):
    tn_ved: str = Field(..., pattern=r"^\d{4,10}$", description="HS code (ТН ВЭД)")
    description: str = Field(..., min_length=1, description="Product description")


class CustomsDutiesRequest(BaseModel):
    customs_value: float = Field(..., gt=0, description="Customs value in USD")
    tn_ved: str = Field(default="8471", pattern=r"^\d{4,10}$", description="HS code")
    country_origin: str = Field(default="CN", min_length=2, max_length=2, description="Origin country ISO code")
    country_dest: str = Field(default="KZ", min_length=2, max_length=2, description="Destination country ISO code")

    @field_validator("country_origin", "country_dest", mode="before")
    @classmethod
    def validate_country(cls, v):
        return v.upper()


class CustomsDutiesResponse(BaseModel):
    customs_value: float
    duty: float
    vat: float
    total: float
    duty_rate: float
    vat_rate: float


class LogisticsCostRequest(BaseModel):
    weight_kg: float = Field(..., gt=0, description="Weight in kilograms")
    volume_m3: float = Field(default=0, ge=0, description="Volume in cubic meters")
    origin: str = Field(default="China", min_length=1, description="Origin country")
    destination: str = Field(default="Kazakhstan", min_length=1, description="Destination country")
    transport_type: str = Field(default="rail", pattern=r"^(rail|truck|air|sea)$", description="Transport type")


class LogisticsCostResponse(BaseModel):
    cost: float
    currency: str = "USD"
    transport_type: str
    origin: str
    destination: str


TN_VED_DATABASE = {
    "сервер": {"tn_ved": "8471", "description": "Автоматические машины для обработки данных"},
    "server": {"tn_ved": "8471", "description": "Automatic data processing machines"},
    "ноутбук": {"tn_ved": "8471", "description": "Портативные автоматические машины"},
    "laptop": {"tn_ved": "8471", "description": "Portable automatic data processing machines"},
    "телефон": {"tn_ved": "8517", "description": "Телефонные аппараты"},
    "phone": {"tn_ved": "8517", "description": "Telephone sets"},
    "процессор": {"tn_ved": "8473", "description": "Части и аксессуары для машин"},
    "cpu": {"tn_ved": "8473", "description": "Parts and accessories for data processing machines"},
    "память": {"tn_ved": "8473", "description": "Модули памяти"},
    "memory": {"tn_ved": "8473", "description": "Memory modules"},
    "диск": {"tn_ved": "8471", "description": "Накопители данных"},
    "ssd": {"tn_ved": "8471", "description": "Solid state drives"},
    "hdd": {"tn_ved": "8471", "description": "Hard disk drives"},
}

DUTY_RATES = {
    "8471": 0.0,
    "8473": 0.0,
    "8517": 0.0,
    "9999": 0.05,
}
VAT_RATE = 0.12

TRANSPORT_RATES = {
    "rail": 2.5,
    "truck": 3.5,
    "air": 15.0,
    "sea": 1.5,
}


def search_tn_ved_database(query: str, **kwargs) -> Dict[str, Any]:
    try:
        validated = TNVEDSearchRequest(query=query)
        query_lower = validated.query
        
        for keyword, data in TN_VED_DATABASE.items():
            if keyword in query_lower:
                logger.info(f"Found TN VED for '{query}': {data['tn_ved']}")
                return TNVEDSearchResponse(**data).model_dump()
        
        logger.warning(f"No TN VED found for '{query}', using default")
        return TNVEDSearchResponse(tn_ved="9999", description="Товары прочие").model_dump()
        
    except Exception as e:
        logger.error(f"Error in search_tn_ved_database: {e}")
        raise ValueError(f"Invalid query: {str(e)}")


def calculate_customs_duties(
    customs_value: float,
    tn_ved: str = "8471",
    country_origin: str = "CN",
    country_dest: str = "KZ",
    **kwargs
) -> Dict[str, Any]:
    try:
        validated = CustomsDutiesRequest(
            customs_value=customs_value,
            tn_ved=tn_ved,
            country_origin=country_origin,
            country_dest=country_dest
        )
        
        duty_rate = DUTY_RATES.get(validated.tn_ved[:4], 0.05)
        duty = validated.customs_value * duty_rate
        vat_base = validated.customs_value + duty
        vat = vat_base * VAT_RATE
        total = duty + vat

        result = CustomsDutiesResponse(
            customs_value=validated.customs_value,
            duty=duty,
            vat=vat,
            total=total,
            duty_rate=duty_rate,
            vat_rate=VAT_RATE
        )
        logger.info(f"Calculated customs duties: duty=${duty:,.2f}, vat=${vat:,.2f}, total=${total:,.2f}")
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Error in calculate_customs_duties: {e}")
        raise ValueError(f"Invalid customs calculation parameters: {str(e)}")


def calculate_logistics_cost(
    weight_kg: float,
    volume_m3: float = 0,
    origin: str = "China",
    destination: str = "Kazakhstan",
    transport_type: str = "rail",
    **kwargs
) -> Dict[str, Any]:
    try:
        validated = LogisticsCostRequest(
            weight_kg=weight_kg,
            volume_m3=volume_m3,
            origin=origin,
            destination=destination,
            transport_type=transport_type
        )
        
        rate = TRANSPORT_RATES.get(validated.transport_type, 2.5)
        base_cost = validated.weight_kg * rate

        if validated.volume_m3 > 0:
            volumetric_weight = validated.volume_m3 * 167
            base_cost = max(base_cost, volumetric_weight * rate)

        result = LogisticsCostResponse(
            cost=round(base_cost, 2),
            currency="USD",
            transport_type=validated.transport_type,
            origin=validated.origin,
            destination=validated.destination
        )
        logger.info(f"Calculated logistics: ${base_cost:,.2f} via {validated.transport_type}")
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Error in calculate_logistics_cost: {e}")
        raise ValueError(f"Invalid logistics calculation parameters: {str(e)}")


TOOL_MANIFEST = {
    "search_tn_ved_database": search_tn_ved_database,
    "calculate_customs_duties": calculate_customs_duties,
    "calculate_logistics_cost": calculate_logistics_cost,
}

TOOL_SCHEMAS = {
    "search_tn_ved_database": TNVEDSearchRequest,
    "calculate_customs_duties": CustomsDutiesRequest,
    "calculate_logistics_cost": LogisticsCostRequest,
}