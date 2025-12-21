$PROJECT_ID = "gen-lang-client-0005433326"
$REGION = "us-central1"

# Enable required APIs
Write-Host "Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable firestore.googleapis.com

# Set project
gcloud config set project $PROJECT_ID

Write-Host "Building and deploying Agent service..."
gcloud run deploy smartsolve-agent `
    --source . `
    --dockerfile Dockerfile.agent `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10

Write-Host "Building and deploying Backend service..."
gcloud run deploy smartsolve-backend `
    --source . `
    --dockerfile Dockerfile.backend `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 5

Write-Host "Building and deploying Frontend service..."
gcloud run deploy smartsolve-frontend `
    --source . `
    --dockerfile Dockerfile.frontend `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --memory 256Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 3

Write-Host "Deployment complete!"
Write-Host "Get service URLs:"
gcloud run services list --platform managed
