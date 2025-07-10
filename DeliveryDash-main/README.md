🚚 DeliveryDash
DeliveryDash is a fully containerized, end-to-end data pipeline project that simulates and analyzes real-world courier shipment data.

It streams live shipment events using Apache Kafka, stores processed data in PostgreSQL, serves RESTful APIs via Flask, and provides a rich, interactive Streamlit dashboard — all spun up with a single Docker command.

🔧 Key Features
🔁 Real-Time Data Streaming
A Kafka producer simulates live shipments from a CSV file, while the consumer processes and stores them in PostgreSQL.

📡 RESTful API with Flask
Provides endpoints to fetch, filter, and aggregate shipment data for real-time analytics.

📊 Interactive Dashboard
A fully API-driven Streamlit web app displays:

Shipment status and delays

Courier and city-wise distributions

Shipment geolocation on a live map

🚀 One-Command Startup
Spin up Kafka, PostgreSQL, and all dependencies with Docker Compose.

🧰 Tech Stack
Languages & Frameworks: Python, Flask, Streamlit

Data Pipeline: Apache Kafka

Database: PostgreSQL

Visualization: Plotly, Streamlit

Orchestration: Docker, Docker Compose

Data Manipulation: Pandas

⚡ Quick Start
1. Start backend services
bash
Copy
Edit
docker compose up -d
2. Install Python dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. Run the streaming pipeline
In Terminal 1 (Producer):

bash
Copy
Edit
python producer.py
In Terminal 2 (Consumer):

bash
Copy
Edit
python consumer.py
4. Launch the Flask REST API
In Terminal 3:

bash
Copy
Edit
python api.py
5. Launch the Streamlit dashboard
In Terminal 4:

bash
Copy
Edit
streamlit run dashboard.py
6. Open in browser:
👉 http://localhost:8501

📁 Project Structure
text
Copy
Edit
producer.py           # Streams shipment data to Kafka
consumer.py           # Consumes from Kafka and loads into Postgres
api.py                # Flask server with shipment data APIs
dashboard.py          # Streamlit frontend (powered entirely by the API)
kafka_shipments.csv   # Simulated shipment data
requirements.txt      # Python dependencies
docker-compose.yml    # Defines and runs Kafka, Postgres, etc.
README.md             # Project documentation (this file)