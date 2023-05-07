# from kafka import KafkaProducer
import asyncio
import json
import os
from time import sleep

import psycopg2

# З'єднання з Kafka
# producer = KafkaProducer(bootstrap_servers='kafka:9092')
POSTGIS_HOST = os.environ.get("POSTGRES_HOST")
POSTGIS_PORT = os.environ.get("POSTGRES_PORT")
POSTGIS_USER = os.environ.get("POSTGRES_USER")
POSTGIS_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGIS_DB = os.environ.get("POSTGRES_DB")
filename = 'field_centroids.geojson'

# З'єднання з базою даних PostgreSQL
def connect_to_db():
    conn = psycopg2.connect(
        host=POSTGIS_HOST,
        port=POSTGIS_PORT,
        dbname=POSTGIS_DB,
        user=POSTGIS_USER,
        password=POSTGIS_PASSWORD
    )
    return conn

# Запис даних про поля у базу даних та відправка повідомлення у Kafka
def insert_field_to_db(field):
    conn = connect_to_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO features (id, name, geometry) VALUES (%s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))", (field['id'], field['name'], json.dumps(field['geom'])))
        #cur.execute("INSERT INTO fields (id, geom) VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))", (, ))
        conn.commit()
        print(f"Field with ID {field['id']} inserted into the database.")
        # producer.send('field-reading', json.dumps(field).encode('utf-8'))
        print(f"Field data sent to Kafka.")
    except Exception as e:
        print(f"Error inserting field into the database: {str(e)}")
    finally:
        cur.close()
        conn.close()

# # Зчитування даних з файлу field_centroids.geojson та запис у базу даних
def read_fields_from_file():
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        for feature in data['features']:
            field = {
                'id': feature['properties']['id'],
                'name': feature['properties']['Name'],
                'geom': feature['geometry']}
            insert_field_to_db(field)
        os.remove(filename)
    except Exception as e:
        print(f"Error reading file: {str(e)}")

# Check and run read_fiealds_from_file() if file exists
async def check_new_file():
    while True:
        if os.path.exists(filename):
            read_fields_from_file()
            print("Data saved into db.")
        else:
            print("No file found.")
        sleep(5)

if __name__ == "__main__":
    print("Service started")
    try:
        loop = asyncio.get_event_loop()
        loop.run_forever()
        loop.create_task(check_new_file())
    except KeyboardInterrupt:
        print("Service stopped")
        loop.close()
        exit(1)