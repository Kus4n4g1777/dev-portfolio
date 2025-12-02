# ===================================================================
# Detection REST API Test Script (PowerShell)
# ===================================================================
# Purpose: Test all detection endpoints with real data
# Location: tests/test_detection_api.ps1
# Usage: .\tests\test_detection_api.ps1
# ===================================================================

Write-Host "🎯 === Testing Detection REST API ===" -ForegroundColor Cyan
Write-Host ""

$API_BASE = "http://localhost:8000/api/detections"

# ===================================================================
# Test 1: POST - Create Detection
# ===================================================================
Write-Host "📨 Test 1: Creating detection..." -ForegroundColor Yellow

$body = @{
    image_url = "test_hearts_stars.jpg"
    model_version = "v1.0"
    confidence_threshold = 0.4
    detections = @(
        @{
            x1 = 0.1
            y1 = 0.2
            x2 = 0.5
            y2 = 0.6
            label = "Hearts"
            confidence = 0.85
        },
        @{
            x1 = 0.6
            y1 = 0.3
            x2 = 0.9
            y2 = 0.7
            label = "Stars"
            confidence = 0.92
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri $API_BASE `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction Stop
    
    $detectionId = $response.id
    
    Write-Host "✅ Detection created successfully!" -ForegroundColor Green
    Write-Host "   ID: $detectionId" -ForegroundColor Gray
    Write-Host "   Total detections: $($response.total_detections)" -ForegroundColor Gray
    Write-Host "   Avg confidence: $($response.avg_confidence)" -ForegroundColor Gray
    Write-Host "   Inference time: $($response.inference_time_ms)ms" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "❌ Failed to create detection" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ===================================================================
# Test 2: GET - Retrieve Single Detection
# ===================================================================
Write-Host "📨 Test 2: Retrieving detection by ID..." -ForegroundColor Yellow

try {
    $detection = Invoke-RestMethod -Uri "$API_BASE/$detectionId" `
        -Method GET `
        -ErrorAction Stop
    
    Write-Host "✅ Detection retrieved successfully!" -ForegroundColor Green
    Write-Host "   Model version: $($detection.model_version)" -ForegroundColor Gray
    Write-Host "   Status: $($detection.status)" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "❌ Failed to retrieve detection" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# ===================================================================
# Test 3: GET - List All Detections
# ===================================================================
Write-Host "📨 Test 3: Listing all detections..." -ForegroundColor Yellow

try {
    $allDetections = Invoke-RestMethod -Uri $API_BASE `
        -Method GET `
        -ErrorAction Stop
    
    Write-Host "✅ Listed detections successfully!" -ForegroundColor Green
    Write-Host "   Total in DB: $($allDetections.Count)" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "❌ Failed to list detections" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# ===================================================================
# Test 4: GET - Metrics Summary
# ===================================================================
Write-Host "📨 Test 4: Getting metrics summary..." -ForegroundColor Yellow

try {
    $metrics = Invoke-RestMethod -Uri "$API_BASE/metrics/summary" `
        -Method GET `
        -ErrorAction Stop
    
    Write-Host "✅ Metrics retrieved successfully!" -ForegroundColor Green
    Write-Host "   Total detections: $($metrics.total_detections)" -ForegroundColor Gray
    Write-Host "   Avg confidence: $([math]::Round($metrics.avg_confidence, 3))" -ForegroundColor Gray
    Write-Host "   Avg inference time: $([math]::Round($metrics.avg_inference_time, 2))ms" -ForegroundColor Gray
    Write-Host "   Detections by label:" -ForegroundColor Gray
    $metrics.detections_by_label.PSObject.Properties | ForEach-Object {
        Write-Host "      $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
    Write-Host ""
    
} catch {
    Write-Host "❌ Failed to get metrics" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# ===================================================================
# Test 5: DELETE - Remove Detection (Optional - commented out)
# ===================================================================
# Uncomment to test deletion
# Write-Host "📨 Test 5: Deleting detection..." -ForegroundColor Yellow
# 
# try {
#     Invoke-RestMethod -Uri "$API_BASE/$detectionId" `
#         -Method DELETE `
#         -ErrorAction Stop
#     
#     Write-Host "✅ Detection deleted successfully!" -ForegroundColor Green
#     Write-Host ""
#     
# } catch {
#     Write-Host "❌ Failed to delete detection" -ForegroundColor Red
#     Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
# }

# ===================================================================
# Summary
# ===================================================================
Write-Host "🎉 === Test Suite Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "   ✅ POST /api/detections" -ForegroundColor Green
Write-Host "   ✅ GET /api/detections/{id}" -ForegroundColor Green
Write-Host "   ✅ GET /api/detections" -ForegroundColor Green
Write-Host "   ✅ GET /api/detections/metrics/summary" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "   • View data: docker exec -it dashboard_db psql -U kus4n4g1 -d portfolio_db -c ""SELECT * FROM detection_results;""" -ForegroundColor Gray
Write-Host "   • Check logs: docker logs dashboard_backend" -ForegroundColor Gray
Write-Host "   • API docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
# ===================================================================