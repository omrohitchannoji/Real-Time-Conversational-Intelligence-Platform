from kafka import KafkaConsumer
import json
from config import BOOTSTRAP_SERVER, TOPIC

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVER,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="chat-group",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

print("Waiting for messages...\n")

for message in consumer:
    print("Received:")
    print(message.value)
    print("-" * 50)