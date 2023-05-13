import os

import psycopg2
from kafka import KafkaConsumer, KafkaProducer


consumer = KafkaConsumer(
    'field-reading',
    bootstrap_servers='kafka:9092',
    group_id='field-reading-group'
)
producer = KafkaProducer(bootstrap_servers='kafka:9092')
POSTGIS_HOST = os.environ.get("POSTGRES_HOST")
POSTGIS_PORT = os.environ.get("POSTGRES_PORT")
POSTGIS_USER = os.environ.get("POSTGRES_USER")
POSTGIS_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGIS_DB = os.environ.get("POSTGRES_DB")


def connect_to_db():
    conn = psycopg2.connect(
        host=POSTGIS_HOST,
        port=POSTGIS_PORT,
        dbname=POSTGIS_DB,
        user=POSTGIS_USER,
        password=POSTGIS_PASSWORD
    )
    return conn


def read_message():
    for message in consumer:
        payload = message.value.decode('utf-8')
        process_message(payload)
        consumer.commit()

def process_message(message):
    if message == "Data received":
        with open('POI.txt', 'r') as f:
            poi = []
            for i in f:
                points = i.strip().split(",")
                nearest_point = get_nearest_point(points)
                print(i.strip().split(","))
                send_to_field_processing(nearest_point[2], nearest_point[2], points)


def get_nearest_point(points):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
    Select id, name, ST_X(geometry), ST_Y(geometry), ST_Distance(geometry, 'SRID=4326;Point(%s %s)'::geometry)   
    from features
    order by ST_Distance(geometry, 'SRID=4326;Point(%s %s)'::geometry)
    limit 1;""", (float(points[0]), float(points[1]), float(points[0]), float(points[1])))
    
    nearest_point = cursor.fetchone()
    cursor.close()
    conn.close()
    return nearest_point

def send_to_field_processing(nearest_point_X, nearest_point_Y, poi):
    producer.send('field-processing', f"Nearest point: [{nearest_point_X}, {nearest_point_Y}], POI: [{poi}]".encode("UTF-8"))
    print(f"Field data sent to Kafka.")


if __name__ == "__main__":
    print("Service started")
    try:
        read_message()
    except KeyboardInterrupt:
        print("Service stopped")
