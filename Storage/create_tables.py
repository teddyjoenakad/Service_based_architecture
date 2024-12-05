import mysql.connector

db_conn = mysql.connector.connect(
    host="kafka-group35.westus.cloudapp.azure.com",
    user="user",
    password="password",
    database="events"
)

db_cursor = db_conn.cursor()

db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS parking_status (
        id INT NOT NULL AUTO_INCREMENT,
        trace_id VARCHAR(100) NOT NULL,
        meter_id INT NOT NULL,
        device_id VARCHAR(250) NOT NULL,
        status BOOLEAN NOT NULL,
        spot_number INT NOT NULL,
        timestamp VARCHAR(100) NOT NULL,
        date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id)
    )
''')

db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_event (
        id INT NOT NULL AUTO_INCREMENT,
        trace_id VARCHAR(100) NOT NULL,
        meter_id INT NOT NULL,
        device_id VARCHAR(250) NOT NULL,
        amount FLOAT NOT NULL,
        duration INT NOT NULL,
        timestamp VARCHAR(100) NOT NULL,
        date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id)
    )
''')

db_conn.commit()
db_conn.close()
