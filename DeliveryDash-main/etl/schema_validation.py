shipment_schema = {
    "type": "object",
    "properties": {
        "shipment_id": {"type": "string"},
        "timestamp": {"type": "string"},
        "source_city": {"type": "string"},
        "destination_city": {"type": "string"},
        "current_city": {"type": "string"},
        "status": {"type": "string"},
        "weight_kg": {"type": "number"},
        "carrier": {"type": "string"},
        "estimated_delivery": {"type": "string"},
        "delay_reason": {"type": ["string", "null"]},
        "rating": {"type": "integer"},
        "delivered": {"type": "boolean"}
    },
    "required": ["shipment_id", "timestamp", "source_city", "destination_city", "current_city", "status", "weight_kg", "carrier", "estimated_delivery", "delivered", "rating"]
}
