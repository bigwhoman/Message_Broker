#!/bin/bash
# Constants of services
PRIMARY_HOST="192.168.56.6"
PRIMARY_PORT=12345
SECONDRY_HOST="192.168.56.6"
SECONDRY_PORT=12346
TO_PUSH1=("key:khar" "key:jend" "key:shash" "key:kir")
TO_PUSH2=("key:fuck" "key:kir")
# Push some items in the queue
for data in "${TO_PUSH1[@]}"; do
    echo "Pushing $data"
    (echo "push:$data"; sleep 1) | ncat "$PRIMARY_HOST" "$PRIMARY_PORT"
    echo # simple new line
done
# Wait a little to sync everything
sleep 10
# Kill the master
echo "Killing master..."
docker compose stop primary-lb
# Wait a little bit more to connect to secondry
sleep 10
# Connect to secondry and push again
for data in "${TO_PUSH2[@]}"; do
    echo "Pushing $data"
    (echo "push:$data"; sleep 1) | ncat "$SECONDRY_HOST" "$SECONDRY_PORT"
    echo # Simple newline
done
# Read everything back
for data in "${TO_PUSH1[@]}"; do
    echo "Expecting $data"
    (echo "pull"; sleep 1) | ncat "$SECONDRY_HOST" "$SECONDRY_PORT"
    echo # Simple newline
done
for data in "${TO_PUSH2[@]}"; do
    echo "Expecting $data"
    (echo "pull"; sleep 1) | ncat "$SECONDRY_HOST" "$SECONDRY_PORT"
    echo # Simple newline
done