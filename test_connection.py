#!/usr/bin/env python3
"""
Test Confluent Cloud Connection
Run this to verify your setup is working
"""
import os
from dotenv import load_dotenv
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import Producer

# Load environment variables
load_dotenv()

def test_connection():
    """Test connection to Confluent Cloud"""
    print("🔍 Testing Confluent Cloud Connection...")
    print("=" * 50)

    # Get configuration
    bootstrap_servers = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS')
    api_key = os.getenv('CONFLUENT_API_KEY')
    api_secret = os.getenv('CONFLUENT_API_SECRET')

    if 'xxxxx' in bootstrap_servers:
        print("❌ ERROR: Bootstrap server still has 'xxxxx' placeholder!")
        print("👉 Please update CONFLUENT_BOOTSTRAP_SERVERS in .env")
        print("   It should look like: pkc-[your-id].us-east1.gcp.confluent.cloud:9092")
        return False

    # Create admin client config
    conf = {
        'bootstrap.servers': bootstrap_servers,
        'sasl.mechanisms': 'PLAIN',
        'security.protocol': 'SASL_SSL',
        'sasl.username': api_key,
        'sasl.password': api_secret,
    }

    try:
        # Test admin connection
        print(f"📡 Connecting to: {bootstrap_servers}")
        admin_client = AdminClient(conf)

        # List topics
        metadata = admin_client.list_topics(timeout=10)
        existing_topics = metadata.topics.keys()

        print(f"✅ Connected successfully!")
        print(f"📋 Existing topics: {list(existing_topics)}")

        # Check for required topics
        required_topics = ['weather_risks', 'social_signals']
        missing_topics = [t for t in required_topics if t not in existing_topics]

        if missing_topics:
            print(f"\n⚠️  Missing topics: {missing_topics}")
            create = input("Would you like to create them now? (y/n): ")

            if create.lower() == 'y':
                # Create missing topics
                new_topics = [
                    NewTopic(topic, num_partitions=3, replication_factor=3)
                    for topic in missing_topics
                ]

                fs = admin_client.create_topics(new_topics)

                for topic, f in fs.items():
                    try:
                        f.result()  # The result itself is None
                        print(f"✅ Topic '{topic}' created")
                    except Exception as e:
                        print(f"❌ Failed to create topic {topic}: {e}")
        else:
            print(f"✅ All required topics exist!")

        # Test producer
        print(f"\n📤 Testing message production...")
        producer = Producer(conf)

        def delivery_report(err, msg):
            if err is not None:
                print(f'❌ Message delivery failed: {err}')
            else:
                print(f'✅ Test message delivered to {msg.topic()}')

        # Send test message
        producer.produce(
            'weather_risks',
            key='test',
            value='{"test": "connection successful"}',
            callback=delivery_report
        )
        producer.flush()

        print("\n" + "=" * 50)
        print("🎉 All tests passed! Your Confluent setup is ready!")
        print("\nNext steps:")
        print("1. Run: python producers/weather_producer.py")
        print("2. Run: python producers/social_producer.py")
        print("3. Start the backend: cd backend && uvicorn main:app --reload")
        print("4. Start the frontend: cd frontend && npm install && npm run dev")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your bootstrap server URL is correct")
        print("2. Verify your API key and secret are correct")
        print("3. Ensure your cluster is running")
        return False

if __name__ == "__main__":
    test_connection()