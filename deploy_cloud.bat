@echo off
echo ========================================================
echo Deploying TCH Ingest Backend to Google Cloud Run
echo Project: tch-production
echo Service: tch-ingest-backend
echo ========================================================
echo.

gcloud run deploy tch-ingest-backend ^
    --source .\cloud_backend ^
    --project tch-production ^
    --region us-central1 ^
    --allow-unauthenticated ^
    --set-env-vars="GEMINI_MODEL=gemini-3.6-flash,GEMINI_API_KEY=%GEMINI_API_KEY%"

echo.
echo Deployment triggered.
pause
