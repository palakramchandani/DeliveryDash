from kafka import KafkaConsumer
import json
import psycopg2
from schema_validation import shipment_schema
from jsonschema import validate

consumer = KafkaConsumer(
    'shipments',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

conn = psycopg2.connect(
    dbname="logistics",
    user="admin",
    password="admin123",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

for message in consumer:
    data = message.value
    try:
        validate(instance=data, schema=shipment_schema)
        cur.execute("""
            INSERT INTO shipment_data (
                shipment_id, timestamp, source_city, destination_city,
                current_city, status, weight_kg, carrier,
                estimated_delivery, delay_reason, rating, delivered
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data['shipment_id'], data['timestamp'], data['source_city'], data['destination_city'],
            data['current_city'], data['status'], data['weight_kg'], data['carrier'],
            data['estimated_delivery'], data['delay_reason'], data['rating'], data['delivered']
        ))
        conn.commit()
        print(f"Inserted: {data['shipment_id']}")
    except Exception as e:
        print("Validation/Insert Error:", e)
