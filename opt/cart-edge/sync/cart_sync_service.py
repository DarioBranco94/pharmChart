import sqlite3
import time
import os
import paho.mqtt.publish as publish

def main():
    db = sqlite3.connect('/opt/cart-edge/db/cart.db')
    cur = db.cursor()
    while True:
        cur.execute('SELECT id, topic, payload FROM mqtt_outbox WHERE sent = 0')
        rows = cur.fetchall()
        for row in rows:
            publish.single(row[1], row[2], hostname=os.getenv('MQTT_HOST', 'localhost'))
            cur.execute('UPDATE mqtt_outbox SET sent = 1 WHERE id = ?', (row[0],))
            db.commit()
        time.sleep(5)

if __name__ == '__main__':
    main()
