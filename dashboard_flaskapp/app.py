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
app.config['MYSQL_HOST'] = secrets['MYSQL_HOST']
app.config['MYSQL_USER'] = secrets['MYSQL_USER']
app.config['MYSQL_PASSWORD'] = secrets['MYSQL_PASSWORD']
app.config['MYSQL_DB'] = secrets['MYSQL_DB']


def get_db_connection():
    try:
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )
        return connection
    except pymysql.MySQLError as e:
        logger.error(f"Error connecting to database: {e}")
        raise


@app.route('/')
def home():
    return "This is the Beacon Dashboard"

@app.route('/ingest', methods=['GET', 'POST'])
def ingest_data():
    connection = get_db_connection()
    try:
        # existing code...
        cur = connection.cursor()
        # existing code...
        connection.commit()
    except pymysql.MySQLError as e:
        logger.error(f"Database error: {e}")
        return jsonify(success=False, message="Internal server error"), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify(success=False, message="Internal server error"), 500
    finally:
        connection.close()

    return jsonify(success=True, message="Data inserted successfully."), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    connection = get_db_connection()
    try:
        cur = connection.cursor(pymysql.cursors.DictCursor)
        # existing code...
        rows = cur.fetchall()
    except pymysql.MySQLError as e:
        logger.error(f"Database error: {e}")
        return "Internal server error", 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "Internal server error", 500
    finally:
        connection.close()

    return render_template('dashboard.html', rows=rows)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
