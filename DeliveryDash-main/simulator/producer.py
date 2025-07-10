import pandas as pd
import json
import time
from kafka import KafkaProducer

# Load the CSV file
df = pd.read_csv('C:\\Users\\palak\\OneDrive\\Desktop\\CLASS_MATERIAL_VIII\\PROGRESS\\PROJECTS\\TrackFlow-main\\TrackFlow-main\\simulator\\kafka_shipments.csv')
# Create Kafka Producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',  # ✅ Corrected from 0.0.0.0 to localhost
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send each row as a Kafka message
for _, row in df.iterrows():
    msg = {
        "shipment_id": str(row['ID']),
        "timestamp": row['timestamp'],
        "source_city": row['source_city'],
        "destination_city": row['destination_city'],
        "current_city": row['current_city'],
        "status": row['Mode_of_Shipment'],
        "weight_kg": round(row['Weight_in_gms'] / 1000, 2),
        "carrier": row['carrier'],
        "estimated_delivery": row['estimated_delivery'],
        "delay_reason": row['delay_reason'],
        "rating": int(row['Customer_rating']),
        "delivered": bool(row['Reached.on.Time_Y.N'] == 0)
    }

    producer.send("shipments", value=msg)  # Sends to topic 'shipments'
    print(f"Sent: {msg}")
    time.sleep(1)  # Wait between messages

# Optional: flush to make sure all messages are delivered
producer.flush()
