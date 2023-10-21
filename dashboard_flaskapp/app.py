from flask import Flask, request, jsonify
import pymysql
from flask import Flask, request, jsonify, render_template


app = Flask(__name__)

# Database configuration
app.config['MYSQL_HOST'] = '3.26.117.249'  # IP address of your AWS EC2 instance
app.config['MYSQL_USER'] = 'greenthumb'  # MySQL username
app.config['MYSQL_PASSWORD'] = 'Br34k0ut'  # MySQL password
app.config['MYSQL_DB'] = 'BeaconDB'

mysql = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB']
)

@app.route('/')
def home():
    return "This is the Beacon Dashboard"

@app.route('/ingest', methods=['GET', 'POST'])
def ingest_data():
    if request.method == 'POST':
        try:
            data = request.json
            device_id = data['device_id']
            is_usb_powered = data['is_usb_powered']
            battery_level = data['battery_level']

            cur = mysql.cursor()
            query = "INSERT INTO device_data(device_id, is_usb_powered, battery_level) VALUES(%s, %s, %s)"
            cur.execute(query, (device_id, is_usb_powered, battery_level))
            mysql.commit()

            return jsonify(success=True, message="Data inserted successfully."), 200

        except Exception as e:
            return jsonify(success=False, message=str(e)), 500
    else: 
         # Handle GET request logic here
        return "This is the ingest endpoint. Use a POST request to send data."
    
@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        cur = mysql.cursor(pymysql.cursors.DictCursor)  # Using DictCursor to fetch results as dictionary
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
        
        return render_template('dashboard.html', rows=rows)
        # return jsonify(rows)  # Temporarily return the data as JSON

    except Exception as e:
        return str(e)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
