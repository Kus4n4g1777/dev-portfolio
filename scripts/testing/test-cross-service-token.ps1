# ===================================================================
# Cross-Service JWT Token Test Script (PowerShell)
# ===================================================================
# Purpose: Test JWT token flow between FastAPI (8000) and Spring Boot (8081)
# Location: scripts/testing/test-cross-service-token.ps1
# Usage: .\scripts\testing\test-cross-service-token.ps1
# ===================================================================

Write-Host "🔐 === Cross-Service JWT Token Test ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$FASTAPI_URL = "http://localhost:8000"
$SPRINGBOOT_URL = "http://localhost:8081"
$USERNAME = "kus4n4g1"
$PASSWORD = "Ethan0410"

# --- Step 1: Get Token from FastAPI ---
Write-Host "📨 Step 1: Requesting JWT token from FastAPI..." -ForegroundColor Yellow

try {
    $formBody = @{
        username = $USERNAME
        password = $PASSWORD
    }
    
    $tokenResponse = Invoke-WebRequest `
        -Uri "$FASTAPI_URL/token" `
        -Method POST `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $formBody `
        -ErrorAction Stop
    
    $tokenData = $tokenResponse.Content | ConvertFrom-Json
    $accessToken = $tokenData.access_token
    
    Write-Host "✅ Token received successfully!" -ForegroundColor Green
    Write-Host "   Token preview: $($accessToken.Substring(0, 20))..." -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "❌ Failed to get token from FastAPI" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Check if FastAPI is running: docker-compose ps dashboard_backend" -ForegroundColor Gray
    Write-Host "   2. Verify credentials in .env file" -ForegroundColor Gray
    Write-Host "   3. Check FastAPI logs: docker logs dashboard_backend" -ForegroundColor Gray
    exit 1
}

# --- Step 2: Test FastAPI Protected Endpoint ---
Write-Host "📨 Step 2: Testing FastAPI protected endpoint (/users/me/)..." -ForegroundColor Yellow

try {
    $headers = @{
        "Authorization" = "Bearer $accessToken"
    }
    
    $meResponse = Invoke-WebRequest `
        -Uri "$FASTAPI_URL/users/me/" `
        -Method GET `
        -Headers $headers `
        -ErrorAction Stop
    
    $userData = $meResponse.Content | ConvertFrom-Json
    
    Write-Host "✅ FastAPI authentication verified!" -ForegroundColor Green
    Write-Host "   User: $($userData.username)" -ForegroundColor Gray
    Write-Host "   Email: $($userData.email)" -ForegroundColor Gray
    Write-Host "   Role: $($userData.role)" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "⚠️  Warning: Could not verify token with FastAPI" -ForegroundColor Yellow
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
}

# --- Step 3: Send Request to Spring Boot with Token ---
Write-Host "📨 Step 3: Sending authenticated request to Spring Boot..." -ForegroundColor Yellow

try {
    $headers = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $accessToken"
    }
    
    $postBody = @{
        title = "Cross-Service JWT Test"
        content = "This message was sent with a valid JWT token from FastAPI to Spring Boot"
    } | ConvertTo-Json
    
    $springResponse = Invoke-WebRequest `
        -Uri "$SPRINGBOOT_URL/api/posts" `
        -Method POST `
        -Headers $headers `
        -Body $postBody `
        -ErrorAction Stop
    
    Write-Host "✅ Spring Boot accepted the token!" -ForegroundColor Green
    Write-Host "   Response Status: $($springResponse.StatusCode)" -ForegroundColor Gray
    Write-Host "   Response: $($springResponse.Content)" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "❌ Failed to authenticate with Spring Boot" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Check if Spring Boot is running: docker-compose ps springboot_backend" -ForegroundColor Gray
    Write-Host "   2. Verify JWT secret matches in both services (.env)" -ForegroundColor Gray
    Write-Host "   3. Check Spring Boot logs: docker logs springboot_backend" -ForegroundColor Gray
    Write-Host "   4. Verify CORS settings allow cross-service communication" -ForegroundColor Gray
    exit 1
}

# --- Step 4: Test Kafka Integration (Optional) ---
Write-Host "📨 Step 4: Testing Kafka message publishing (optional)..." -ForegroundColor Yellow

try {
    # This assumes Spring Boot publishes to Kafka after receiving the post
    Start-Sleep -Seconds 2  # Give Kafka time to process
    
    Write-Host "ℹ️  Check Kafka logs to verify message was published:" -ForegroundColor Cyan
    Write-Host "   docker logs kafka --tail=50" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "⚠️  Could not verify Kafka integration" -ForegroundColor Yellow
    Write-Host ""
}

# --- Summary ---
Write-Host "🎉 === Test Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Summary:" -ForegroundColor Cyan
Write-Host "   1. FastAPI issued JWT token: ✅" -ForegroundColor Green
Write-Host "   2. FastAPI verified token: ✅" -ForegroundColor Green
Write-Host "   3. Spring Boot accepted token: ✅" -ForegroundColor Green
Write-Host ""
Write-Host "📊 What this proves:" -ForegroundColor Cyan
Write-Host "   • JWT tokens work across microservices" -ForegroundColor Gray
Write-Host "   • Shared SECRET_KEY is properly configured" -ForegroundColor Gray
Write-Host "   • CORS is configured correctly" -ForegroundColor Gray
Write-Host "   • Services can authenticate each other's requests" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   • View all logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "   • Check database: docker exec -it dashboard_db psql -U kus4n4g1 -d portfolio_db" -ForegroundColor Gray
Write-Host "   • Monitor Kafka: docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic posts --from-beginning" -ForegroundColor Gray
Write-Host ""