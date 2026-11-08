# Espera o contêiner lab-app ficar "healthy". Se não ficar, mostra os logs e reprova o pipeline.
$ok = $false
for ($i = 1; $i -le 45; $i++) {
    $status = (docker inspect --format '{{.State.Health.Status}}' lab-app 2>$null)
    Write-Host "tentativa ${i}: $status"
    if ($status -eq 'healthy') { $ok = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $ok) {
    Write-Host "O sistema nao ficou saudavel. Ultimos logs:"
    docker-compose logs --tail 60
    exit 1
}
Write-Host "Sistema saudavel em http://localhost:8080"
exit 0
