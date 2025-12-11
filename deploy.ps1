
# Deployment Script for Quick Conversation Lab
# Deploys Backend to Cloud Run and Frontend to Firebase Hosting

$PROJECT_ID = "quick-conversation-lab"
$REGION = "asia-northeast1"
$SERVICE_NAME = "voice-model-lab-backend"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting Deployment to $PROJECT_ID" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Check Prerequisites
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "gcloud CLI is not installed."
    exit 1
}
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    Write-Error "firebase CLI is not installed."
    exit 1
}

# 2. Deploy Backend to Cloud Run
Write-Host "`n[1/3] Deploying Backend to Cloud Run..." -ForegroundColor Yellow

# Parse .env file for environment variables
$envFile = "./backend/.env"
$envVars = @()
if (Test-Path $envFile) {
    $lines = Get-Content $envFile
    foreach ($line in $lines) {
        $line = $line.Trim()
        if ($line -match '^([^#=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            # Remove inline comments (naive: assumes # starts comment if preceded by space)
            if ($value -match '^(.*?)(\s+#.*)$') {
                $value = $matches[1].Trim()
            }
            
            # Remove surrounding quotes
            if ($value -match '^"(.*)"$') { $value = $matches[1] }
            elseif ($value -match "^'(.*)'$") { $value = $matches[1] }
            
            # Escape commas for gcloud
            $value = $value -replace ',', '\,'
            
            $envVars += "$key=$value"
        }
    }
}
$envString = $envVars -join ","

if (-not $envString) {
    Write-Warning "No environment variables found in $envFile or file missing."
    $backendDeployCommand = "gcloud run deploy $SERVICE_NAME --source ./backend --region $REGION --project $PROJECT_ID --allow-unauthenticated"
}
else {
    Write-Host "Found environment variables, injecting into deployment (truncated for security):"
    $envVars | ForEach-Object { 
        if ($_.StartsWith("DATABASE_URL")) { Write-Host $_ } 
        else { Write-Host ($_.Split('=')[0] + "=[REDACTED]") }
    }
    $backendDeployCommand = "gcloud run deploy $SERVICE_NAME --source ./backend --region $REGION --project $PROJECT_ID --allow-unauthenticated --set-env-vars ""$envString"""
}

Write-Host "Executing: $backendDeployCommand"
Invoke-Expression $backendDeployCommand

if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend deployment failed."
    exit $LASTEXITCODE
}

Write-Host "Backend deployed successfully." -ForegroundColor Green
Write-Host "IMPORTANT: Make sure to set 'DATABASE_URL' and 'GEMINI_API_KEY' in Cloud Run environment variables if you haven't already." -ForegroundColor Magenta

# 3. Build Frontend
Write-Host "`n[2/3] Building Frontend..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Error "Frontend build failed."
    exit $LASTEXITCODE
}

# 4. Deploy Frontend to Firebase Hosting
Write-Host "`n[3/3] Deploying Frontend to Firebase Hosting..." -ForegroundColor Yellow
$firebaseDeployCommand = "firebase deploy --only hosting --project $PROJECT_ID"
Write-Host "Executing: $firebaseDeployCommand"
Invoke-Expression $firebaseDeployCommand

if ($LASTEXITCODE -ne 0) {
    Write-Error "Frontend deployment failed."
    exit $LASTEXITCODE
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "Frontend URL: https://$PROJECT_ID.web.app" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
