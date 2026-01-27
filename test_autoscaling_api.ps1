# Auto-Scaling API Test Script
# This tests the auto-scaling feature end-to-end via API

# 1. Login
$loginBody = "username=testisqckb@test.com&password=password"
$loginResponse = Invoke-WebRequest -Method POST -Uri "http://localhost:8000/auth/login" `
    -Headers @{"Content-Type" = "application/x-www-form-urlencoded"} `
    -Body $loginBody | ConvertFrom-Json
$token = $loginResponse.access_token
Write-Host "✓ Logged in successfully" -ForegroundColor Green

# 2. List existing policies
Write-Host "`n=== Checking existing policies ===" -ForegroundColor Cyan
try {
    $existingPolicies = Invoke-WebRequest -Method GET `
        -Uri "http://localhost:8000/autoscaling/policies" `
        -Headers @{"Authorization" = "Bearer $token"} | ConvertFrom-Json
    Write-Host "Found $($existingPolicies.Count) existing policy/policies"
    $existingPolicies | Format-Table -Property id, container_id, enabled, min_replicas, max_replicas
} catch {
    Write-Host "No existing policies or error fetching: $_" -ForegroundColor Yellow
}

# 3. Delete existing policy for container 18 if it exists
$existingPolicyForContainer18 = $existingPolicies | Where-Object { $_.container_id -eq 18 }
if ($existingPolicyForContainer18) {
    Write-Host "`n⚠ Found existing policy for container 18. Deleting it first..." -ForegroundColor Yellow
    Invoke-WebRequest -Method DELETE `
        -Uri "http://localhost:8000/autoscaling/policies/$($existingPolicyForContainer18.id)" `
        -Headers @{"Authorization" = "Bearer $token"} | Out-Null
    Write-Host "✓ Deleted old policy" -ForegroundColor Green
    Start-Sleep -Seconds 1
}

# 4. Create new policy
Write-Host "`n=== Creating new auto-scaling policy ===" -ForegroundColor Cyan
$policyBody = @{
    container_id = 18
    scale_up_cpu_threshold = 10.0
    scale_up_memory_threshold = 20.0
    scale_down_cpu_threshold = 5.0
    scale_down_memory_threshold = 15.0
    min_replicas = 1
    max_replicas = 3
    cooldown_period = 60
    evaluation_period = 60
    enabled = $true
    load_balancer_enabled = $false
} | ConvertTo-Json

try {
    $newPolicy = Invoke-WebRequest -Method POST `
        -Uri "http://localhost:8000/autoscaling/policies" `
        -Headers @{"Authorization" = "Bearer $token"; "Content-Type" = "application/json"} `
        -Body $policyBody | ConvertFrom-Json
    
    Write-Host "✓ Policy created successfully!" -ForegroundColor Green
    Write-Host "  Policy ID: $($newPolicy.id)"
    Write-Host "  Container ID: $($newPolicy.container_id)"
    Write-Host "  Scale Up CPU Threshold: $($newPolicy.scale_up_cpu_threshold)%"
    Write-Host "  Scale Up Memory Threshold: $($newPolicy.scale_up_memory_threshold)%"
    Write-Host "  Min Replicas: $($newPolicy.min_replicas)"
    Write-Host "  Max Replicas: $($newPolicy.max_replicas)"
    Write-Host "  Enabled: $($newPolicy.enabled)"
} catch {
    Write-Host "✗ Error creating policy: $_" -ForegroundColor Red
    Write-Host "Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 1
}

# 5. Trigger manual evaluation
Write-Host "`n=== Triggering manual policy evaluation ===" -ForegroundColor Cyan
$evalResponse = Invoke-WebRequest -Method POST `
    -Uri "http://localhost:8000/autoscaling/evaluate-now" `
    -Headers @{"Authorization" = "Bearer $token"} | ConvertFrom-Json
Write-Host "✓ Evaluation triggered: $($evalResponse.message)" -ForegroundColor Green

# 6. Wait for background task to run
Write-Host "`n=== Waiting 90 seconds for auto-scaler to run ===" -ForegroundColor Cyan
Write-Host "The background task runs every 30 seconds, so we'll wait for 3 cycles..."
for ($i = 90; $i -gt 0; $i--) {
    Write-Progress -Activity "Waiting for auto-scaler" -Status "$i seconds remaining" -PercentComplete ((90 - $i) / 90 * 100)
    Start-Sleep -Seconds 1
}
Write-Progress -Activity "Waiting for auto-scaler" -Completed

# 7. Check for scaling events
Write-Host "`n=== Checking for scaling events ===" -ForegroundColor Cyan
try {
    $events = Invoke-WebRequest -Method GET `
        -Uri "http://localhost:8000/autoscaling/events?container_id=18&limit=10" `
        -Headers @{"Authorization" = "Bearer $token"} | ConvertFrom-Json
    
    if ($events.Count -eq 0) {
        Write-Host "⚠ No scaling events found yet" -ForegroundColor Yellow
        Write-Host "This might mean:" -ForegroundColor Yellow
        Write-Host "  - Metrics haven't crossed thresholds yet (random 3-15% CPU, 10-30% Memory)" -ForegroundColor Yellow
        Write-Host "  - Background task hasn't run yet" -ForegroundColor Yellow
        Write-Host "  - Container metrics generation is working but below threshold" -ForegroundColor Yellow
    } else {
        Write-Host "✓ Found $($events.Count) scaling event(s)!" -ForegroundColor Green
        $events | Format-Table -Property id, action, trigger_metric, metric_value, replica_count_before, replica_count_after, created_at
    }
} catch {
    Write-Host "Error fetching events: $_" -ForegroundColor Red
}

# 8. Check current replica count
Write-Host "`n=== Checking replica containers ===" -ForegroundColor Cyan
try {
    $containers = Invoke-WebRequest -Method GET `
        -Uri "http://localhost:8000/containers/" `
        -Headers @{"Authorization" = "Bearer $token"} | ConvertFrom-Json
    
    $mainContainer = $containers.containers | Where-Object { $_.id -eq 18 }
    $replicas = $containers.containers | Where-Object { $_.parent_id -eq 18 }
    
    Write-Host "Main container (ID 18): $($mainContainer.name) - Status: $($mainContainer.status)"
    if ($replicas.Count -gt 0) {
        Write-Host "✓ Found $($replicas.Count) replica(s):" -ForegroundColor Green
        $replicas | Format-Table -Property id, name, status, port
    } else {
        Write-Host "No replicas created yet (this is normal if no scale-up event occurred)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error fetching containers: $_" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
Write-Host "Next step: Test via UI at http://localhost:5173/admin/autoscaling" -ForegroundColor Cyan
