from confluent_kafka import Consumer

c = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "taxi-trip-consumer-group-1",
    "auto.offset.reset": "earliest" # Start reading from the beginning of the topic
})

c.subscribe(["taxi_trips"])

print("Consumer started. Waiting for messages...")

try:
    while True:
        msg = c.poll(1.0) # Timeout of 1 second

        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        print(f"Received message: key='{msg.key().decode('utf-8')}', value='{msg.value().decode('utf-8')}'")
except KeyboardInterrupt:
    print("Stopping consumer.")
finally:
    # Cleanly close the consumer
    c.close()