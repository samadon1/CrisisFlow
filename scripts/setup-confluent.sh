#!/bin/bash

# CrisisFlow Confluent Cloud Setup Script
# Creates topics and configures ksqlDB

set -e

echo "🔧 Confluent Cloud Setup for CrisisFlow"
echo "========================================"

# Check for Confluent CLI
if ! command -v confluent &> /dev/null; then
    echo "❌ Confluent CLI not found"
    echo "Please install: https://docs.confluent.io/confluent-cli/current/install.html"
    exit 1
fi

# Login to Confluent Cloud
echo "Logging into Confluent Cloud..."
confluent login

# List environments
echo "Available environments:"
confluent environment list

# Select environment
read -p "Enter environment ID: " ENV_ID
confluent environment use $ENV_ID

# List clusters
echo "Available clusters:"
confluent kafka cluster list

# Select cluster
read -p "Enter cluster ID: " CLUSTER_ID
confluent kafka cluster use $CLUSTER_ID

# Create API key if needed
read -p "Do you need to create a new API key? (y/n): " CREATE_KEY
if [ "$CREATE_KEY" = "y" ]; then
    echo "Creating API key..."
    confluent api-key create --resource $CLUSTER_ID
    echo "⚠️  Save these credentials in your .env file!"
    read -p "Press Enter to continue..."
fi

# Create topics
create_topics() {
    echo "Creating Kafka topics..."

    # Weather risks topic
    echo "Creating weather_risks topic..."
    confluent kafka topic create weather_risks \
        --partitions 3 \
        --config retention.ms=86400000 \
        --if-not-exists

    # Social signals topic
    echo "Creating social_signals topic..."
    confluent kafka topic create social_signals \
        --partitions 3 \
        --config retention.ms=86400000 \
        --if-not-exists

    echo "✅ Topics created successfully!"
}

# Setup ksqlDB
setup_ksqldb() {
    echo "Setting up ksqlDB..."

    # Check if ksqlDB is available
    echo "Checking ksqlDB availability..."
    confluent ksql cluster list

    read -p "Enter ksqlDB cluster ID (or 'skip' to skip): " KSQL_ID

    if [ "$KSQL_ID" != "skip" ]; then
        echo "Configuring ksqlDB cluster: $KSQL_ID"
        confluent ksql cluster use $KSQL_ID

        echo "✅ ksqlDB configured!"
        echo ""
        echo "Next steps:"
        echo "1. Go to Confluent Cloud Console"
        echo "2. Navigate to ksqlDB"
        echo "3. Run the queries from ksqldb/queries.sql"
    fi
}

# Get bootstrap server
get_bootstrap_server() {
    echo ""
    echo "Getting bootstrap server..."
    BOOTSTRAP=$(confluent kafka cluster describe --output json | grep -o '"bootstrap_url":"[^"]*' | cut -d'"' -f4)
    echo "Bootstrap Server: $BOOTSTRAP"
    echo ""
    echo "⚠️  Update your .env file with:"
    echo "CONFLUENT_BOOTSTRAP_SERVERS=$BOOTSTRAP"
}

# Verify setup
verify_setup() {
    echo ""
    echo "Verifying setup..."

    echo "Topics:"
    confluent kafka topic list

    echo ""
    echo "✅ Confluent Cloud setup complete!"
}

# Main execution
main() {
    create_topics
    setup_ksqldb
    get_bootstrap_server
    verify_setup

    echo ""
    echo "========================================"
    echo "🎉 Setup Complete!"
    echo "========================================"
    echo ""
    echo "Don't forget to:"
    echo "1. Update .env with bootstrap server"
    echo "2. Run ksqlDB queries in the console"
    echo "3. Test producers with: python producers/weather_producer.py"
}

# Run main
main