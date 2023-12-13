from flask import Flask, request, jsonify
import pyotp, hashlib, os, psycopg2

app = Flask(__name__)

def connect_to_db(dbname, user, password, host):
    """Connect to the PostgreSQL database server"""
    conn = None
    try:
        # Connect to the PostgreSQL server
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        print("Connected to the database")
    except Exception as e:
        print(f"The error '{e}' occurred")
    return conn

def generate_totp_sha256(secret):
    """
    Generate a TOTP code based on the given secret using SHA256 algorithm.

    Args:
    secret (str): The secret key for the TOTP generation.

    Returns:
    str: The TOTP code.
    """
    totp = pyotp.TOTP(secret, digest=hashlib.sha256)
    return totp


def validate_otp_local(otp):
    # Retrieve the secret key from an environment variable
    secret_key = os.getenv('OTPSECRET')

    if not otp:
        return False

    # Validate OTP code
    totp = generate_totp_sha256(secret_key)
    validation_result = totp.verify(otp)

    return validation_result

@app.route('/otp/validate', methods=['POST'])
def validate_otp():
    # Retrieve the secret key from an environment variable
    secret_key = os.getenv('OTPSECRET')

    # Get OTP code from the request
    input_otp = request.json.get('otp')
    if not input_otp:
        return jsonify({'error': 'OTP code is required'}), 400

    # Validate OTP code
    totp = generate_totp_sha256(secret_key)
    validation_result = totp.verify(input_otp)

    return jsonify({'valid': validation_result})

# Delete database table
# requires:
# - otp
# - table name
@app.route('/db/table/delete', methods=['POST'])
def delete_table():
    # # Run OTP validation to ensure the request is authorized
    # if not validate_otp_local(request.json.get('otp')):
    #     return jsonify({'error': 'OTP code is invalid'}), 401
    
    """Connect to the PostgreSQL database server"""
    try:
        # Connect to the PostgreSQL server
        conn = connect_to_db(request.json.get('db_name'), request.json.get('db_user'), request.json.get('db_password'), request.json.get('host'))
        print("Connected to the database")
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS {};".format(request.json.get('table_name')))
        conn.commit()
        print("Table deleted successfully")
        cursor.close()
        conn.close()
        return jsonify({'status': True})
    except Exception as e:
        print(f"The error '{e}' occurred")
        return jsonify({'status': False, 'error': str(e)})

# requires:
# - otp
# - db_name
# - db_user
# - db_password
# - host
# - table_name
# - schema
@app.route('/db/table/create', methods=['POST'])
def create_table():
    # # Run OTP validation to ensure the request is authorized
    # if not validate_otp_local(request.json.get('otp')):
    #     return jsonify({'error': 'OTP code is invalid'}), 401
    
    """Connect to the PostgreSQL database server"""
    try:
        # Connect to the PostgreSQL server
        conn = connect_to_db(request.json.get('db_name'), request.json.get('db_user'), request.json.get('db_password'), request.json.get('host'))
        print("Connected to the database")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS {} ({});".format(request.json.get('table_name'), request.json.get('schema')))
        conn.commit()
        print("Table created successfully")

        cursor.close()
        conn.close()
        return jsonify({'status': True})
    except Exception as e:
        print(f"The error '{e}' occurred")
        return jsonify({'status': False, 'error': str(e)})

# requires:
# - otp
# - db_name
# - db_user
# - db_password
# - host
# - table_name
# - schema
# - values
@app.route('/db/table/insert', methods=['POST'])
def insert_into_table():
    # # Run OTP validation to ensure the request is authorized
    # if not validate_otp_local(request.json.get('otp')):
    #     return jsonify({'error': 'OTP code is invalid'}), 401
    
    """Connect to the PostgreSQL database server"""
    try:
        # Connect to the PostgreSQL server
        conn = connect_to_db(request.json.get('db_name'), request.json.get('db_user'), request.json.get('db_password'), request.json.get('host'))
        print("Connected to the database")
        cursor = conn.cursor()
        insert_query = "INSERT INTO {} ({}) VALUES (%s, %s, %s);".format(request.json.get('table_name'), ", ".join(x for x in request.json.get('columns')))
        for record in request.json.get('values'):
            cursor.execute(insert_query, record)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': True, "inserted_records": request.json.get('values')})
    except Exception as e:
        print(f"The error '{e}' occurred")
        return jsonify({'status': False, 'error': str(e), 'query': insert_query})

@app.route('/db/table/view', methods=['GET'])
def view_table():
    # # Run OTP validation to ensure the request is authorized
    # if not validate_otp_local(request.json.get('otp')):
    #     return jsonify({'error': 'OTP code is invalid'}), 401
    
    """Connect to the PostgreSQL database server"""
    try:
        # Connect to the PostgreSQL server
        conn = connect_to_db(request.json.get('db_name'), request.json.get('db_user'), request.json.get('db_password'), request.json.get('host'))
        print("Connected to the database")
        cursor = conn.cursor()

        # Query the table and fetch all data
        cursor.execute("SELECT * FROM {};".format(request.json.get('table_name')))
        rows = cursor.fetchall()
        table_name = request.json.get('table_name')
        # SQL query to get the table's schema information
        schema_query = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}';"

        # Execute the query
        cursor.execute(schema_query)

        # Fetch all the rows (columns and data types)
        table_schema = cursor.fetchall()

        return jsonify({'data': rows, 'schema': table_schema})
            
    except Exception as e:
        print(f"The error '{e}' occurred")
        return jsonify({'status': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
