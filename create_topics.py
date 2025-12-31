#!/usr/bin/env python3
"""
Create required Kafka topics in Confluent Cloud
"""
import os
from dotenv import load_dotenv
from confluent_kafka.admin import AdminClient, NewTopic

# Load environment variables
load_dotenv()

def create_topics():
    """Create required topics for CrisisFlow"""
    print("🚀 Creating Kafka Topics for CrisisFlow")
    print("=" * 50)

    # Configuration
    conf = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
        'sasl.mechanisms': 'PLAIN',
        'security.protocol': 'SASL_SSL',
        'sasl.username': os.getenv('CONFLUENT_API_KEY'),
        'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
    }

    try:
        # Create admin client
        admin_client = AdminClient(conf)
        print(f"✅ Connected to Confluent Cloud")

        # Define topics to create
        topics = [
            NewTopic(
                topic='weather_risks',
                num_partitions=3,
                replication_factor=3,
                config={
                    'retention.ms': '86400000',  # 24 hours
                    'cleanup.policy': 'delete'
                }
            ),
            NewTopic(
                topic='social_signals',
                num_partitions=3,
                replication_factor=3,
                config={
                    'retention.ms': '86400000',  # 24 hours
                    'cleanup.policy': 'delete'
                }
            )
        ]

        # Create topics
        print("\n📝 Creating topics...")
        fs = admin_client.create_topics(topics, request_timeout=10)

        # Check results
        for topic, f in fs.items():
            try:
                f.result()  # The result itself is None
                print(f"✅ Topic '{topic}' created successfully")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"ℹ️  Topic '{topic}' already exists")
                else:
                    print(f"❌ Failed to create topic '{topic}': {e}")

        print("\n" + "=" * 50)
        print("✅ Topic setup complete!")
        print("\nYour Confluent Cloud cluster now has:")
        print("  - weather_risks (3 partitions)")
        print("  - social_signals (3 partitions)")
        print("\n🎯 Next: Start the producers and backend!")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True

if __name__ == "__main__":
    create_topics()