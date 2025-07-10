CREATE TABLE shipment_data (
    shipment_id VARCHAR PRIMARY KEY,
    timestamp TIMESTAMP,
    source_city VARCHAR,
    destination_city VARCHAR,
    current_city VARCHAR,
    status VARCHAR,
    weight_kg FLOAT,
    carrier VARCHAR,
    estimated_delivery TIMESTAMP,
    delay_reason VARCHAR,
    rating INT,
    delivered BOOLEAN
);
