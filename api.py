from flask import Flask, jsonify, request
import psycopg2
import pandas as pd

app = Flask(__name__)

DB_HOST = "localhost"
DB_NAME = "logistics"
DB_USER = "admin"
DB_PASS = "admin123"
DB_PORT = "5432"

def get_df(query, params=None):
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

@app.route('/')
def home():
    return jsonify({"msg": "Courier Track API running!", "endpoints": ["/shipments", "/shipment/<id>", "/analytics"]})

@app.route('/shipments')
def get_shipments():
    status = request.args.get('status')
    carrier = request.args.get('carrier')
    city = request.args.get('city')

    query = "SELECT * FROM shipment_data WHERE 1=1"
    params = {}
    if status:
        query += " AND status=%(status)s"
        params['status'] = status
    if carrier:
        query += " AND carrier=%(carrier)s"
        params['carrier'] = carrier
    if city:
        query += " AND current_city=%(city)s"
        params['city'] = city

    df = get_df(query, params or None)
    return df.to_json(orient="records")

@app.route('/shipment/<shipment_id>')
def get_one_shipment(shipment_id):
    df = get_df("SELECT * FROM shipment_data WHERE shipment_id = %s", (shipment_id,))
    if df.empty:
        return jsonify({"error": "Shipment not found"}), 404
    return df.iloc[0].to_dict()

@app.route('/analytics')
def analytics():
    df = get_df("SELECT * FROM shipment_data")
    total = len(df)
    delivered = int(df["delivered"].sum())
    on_time_pct = (100 * delivered / total) if total else 0

    stats = {
        "total_shipments": total,
        "delivered_shipments": delivered,
        "on_time_percent": round(on_time_pct, 1),
        "by_status": df["status"].value_counts().to_dict(),
        "by_carrier": df["carrier"].value_counts().to_dict(),
        "avg_rating_by_carrier": df.groupby("carrier")["rating"].mean().round(2).to_dict(),
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)
