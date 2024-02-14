#!/bin/bash
# Constants of services
PRIMARY_HOST="192.168.56.6"
PRIMARY_PORT=12345
TO_PUSH1=("key:khar" "key:jend" "key:shash" "key:kir")
TO_PUSH2=("key:fuck" "key:kir")
# Push some items in the queue
for data in "${TO_PUSH1[@]}"; do
    echo "Pushing $data"
    (echo "push:$data"; sleep 1) | ncat "$PRIMARY_HOST" "$PRIMARY_PORT"
    echo # simple new line
done
# Kill a slave
echo "Slave..."
docker compose stop vbox-slave-1
sleep 5
# Connect to secondry and push again
for data in "${TO_PUSH2[@]}"; do
    echo "Pushing $data"
    (echo "push:$data"; sleep 1) | ncat "$PRIMARY_HOST" "$PRIMARY_PORT"
    echo # Simple newline
done
# Read everything back
for data in "${TO_PUSH1[@]}"; do
    echo "Expecting $data"
    (echo "pull"; sleep 1) | ncat "$PRIMARY_HOST" "$PRIMARY_PORT"
    echo # Simple newline
done
for data in "${TO_PUSH2[@]}"; do
    echo "Expecting $data"
    (echo "pull"; sleep 1) | ncat "$PRIMARY_HOST" "$PRIMARY_PORT"
    echo # Simple newline
done