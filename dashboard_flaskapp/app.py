from flask import Flask, request, jsonify, render_template
import pymysql
import boto3
from botocore.exceptions import ClientError
import json
import logging

app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_secret():
    secret_name = "prod/BeaconDashboard/mysql"
    region_name = "ap-southeast-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Error fetching secret: {e}")
        raise
    else:
        return json.loads(get_secret_value_response['SecretString'])

# Database configuration
secrets = get_secret()

app.config['MYSQL_HOST'] = secrets.get('MYSQL_HOST')
app.config['MYSQL_USER'] = secrets.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = secrets.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = secrets.get('MYSQL_DB')

try:
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )
except pymysql.MySQLError as e:
    logger.error(f"Error connecting to database: {e}")
    raise

@app.route('/')
def home():
    return "This is the Beacon Dashboard"

@app.route('/ingest', methods=['GET', 'POST'])
def ingest_data():
    if request.method == 'POST':
        try:
            data = request.json

            device_id = data.get('device_id')
            is_usb_powered = data.get('is_usb_powered')
            battery_level = data.get('battery_level')

            # Validation code starts here
            if not isinstance(device_id, int):
                return jsonify(success=False, message="Invalid device_id"), 400
            if is_usb_powered not in [0, 1]:
                return jsonify(success=False, message="Invalid is_usb_powered value"), 400

            cur = mysql.cursor()
            query = """
            INSERT INTO device_data(device_id, is_usb_powered, battery_level) 
            VALUES(%s, %s, %s)
            """
            cur.execute(query, (device_id, is_usb_powered, battery_level))
            mysql.commit()
        except pymysql.MySQLError as e:
            logger.error(f"Database error: {e}")
            return jsonify(success=False, message="Internal server error"), 500
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify(success=False, message="Internal server error"), 500
        else:
            return jsonify(success=True, message="Data inserted successfully."), 200
    else:
        return "This is the ingest endpoint. Use a POST request to send data."

@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        cur = mysql.cursor(pymysql.cursors.DictCursor)
        cur.execute("""
            SELECT d.device_id, 
                d.is_usb_powered, 
                d.battery_level, 
                d.timestamp AS latest_timestamp
            FROM device_data d
            INNER JOIN (
            SELECT device_id, MAX(timestamp) AS max_timestamp
            FROM device_data
            GROUP BY device_id
            ) subq ON d.device_id = subq.device_id AND d.timestamp = subq.max_timestamp
            ORDER BY latest_timestamp DESC
        """)
        rows = cur.fetchall()
    except pymysql.MySQLError as e:
        logger.error(f"Database error: {e}")
        return "Internal server error", 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "Internal server error", 500
    else:
        return render_template('dashboard.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
