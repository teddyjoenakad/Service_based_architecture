import mysql.connector

db_conn = mysql.connector.connect(
    host="kafka-group35.westus.cloudapp.azure.com",
    user="user",
    password="password",
    database="events"
)

db_cursor = db_conn.cursor()

db_cursor.execute('DROP TABLE IF EXISTS parking_status')
db_cursor.execute('DROP TABLE IF EXISTS payment_event')

db_conn.commit()
db_conn.close()