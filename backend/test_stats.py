from app.services.container_stats_service import container_stats_service

# Test if we can get stats for a specific container
test_container_id = "35bd522053e9"  # private-test container

print(f"Testing stats collection for container: {test_container_id}")
print("="* 60)

stats = container_stats_service.get_container_stats(test_container_id)

if stats:
    print("✅ SUCCESS! Stats collected:")
    print(f"  CPU: {stats['cpu_percent']}%")
    print(f"  Memory: {stats['memory_usage_mb']} MB / {stats['memory_limit_mb']} MB")
    print(f"  Memory %: {stats['memory_percent']}%")
    print(f"  Network RX: {stats['network_rx_mb']} MB")
    print(f"  Network TX: {stats['network_tx_mb']} MB")
else:
    print("❌ FAILED! Could not collect stats")
    print(f"  Client status: {container_stats_service.client}")
