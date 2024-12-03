# Deploying Your Chatbot to Azure

## Step 0: Docker Hub Setup

1. Create Docker Hub Account:
   - Go to https://hub.docker.com/
   - Click "Sign Up"
   - Fill in your details and create account
   - Your Docker Hub username is what you chose during signup

2. Get Docker Hub Username:
   - Go to https://hub.docker.com/
   - Click "Sign In" if not already signed in
   - Your username appears in the top right corner
   - Or check the URL after login: https://hub.docker.com/u/yourusername

3. Login to Docker Hub in terminal:
```bash
docker login
# Enter your Docker Hub username and password when prompted
```

## Step 1: Deploy Backend (Flask API)

1. Create App Service:
```bash
# Create App Service Plan
az appservice plan create --name dream-ai-plan --resource-group DreamAIAgentGroup --sku B1 --is-linux

# Create Web App
az webapp create --resource-group DreamAIAgentGroup --plan dream-ai-plan --name dream-ai-backend --runtime "PYTHON:3.11"
```

2. Deploy backend code:
```bash
# Navigate to backend directory
cd backend

# Build Docker image
docker build -t yourdockerhubusername/dream-ai-backend:latest .

# Login to Docker Hub
docker login

# Push to Docker Hub
docker push yourdockerhubusername/dream-ai-backend:latest

# Configure web app to use Docker image
az webapp config container set \
    --name dream-ai-backend \
    --resource-group DreamAIAgentGroup \
    --docker-custom-image-name yourdockerhubusername/dream-ai-backend:latest \
    --docker-registry-server-url https://index.docker.io
```

3. Set backend environment variables:
```bash
az webapp config appsettings set --resource-group DreamAIAgentGroup --name dream-ai-backend --settings \
    AZURE_OPENAI_ENDPOINT="your-openai-endpoint" \
    AZURE_OPENAI_API_KEY="your-openai-key" \
    AZURE_OPENAI_DEPLOYMENT="your-openai-deployment" \
    DALLE_ENDPOINT="your-dalle-endpoint" \
    DALLE_API_KEY="your-dalle-key" \
    DALLE_DEPLOYMENT="your-dalle-deployment" \
    WEBSITES_PORT=8000
```

Your backend will be available at: `https://dream-ai-backend.azurewebsites.net`

## Step 2: Deploy Frontend (Next.js)

1. Update frontend configuration:
```bash
# Open frontend/app/config.ts and update API_URL
export const API_URL = 'https://dream-ai-backend.azurewebsites.net';
```

2. Deploy frontend:
```bash
# Navigate to frontend directory
cd frontend

# Build Docker image
docker build -t yourdockerhubusername/dream-ai-frontend:latest .

# Push to Docker Hub
docker push yourdockerhubusername/dream-ai-frontend:latest

# Create frontend web app
az webapp create --resource-group DreamAIAgentGroup --plan dream-ai-plan --name dream-ai-frontend --runtime "NODE:18-lts"

# Configure web app to use Docker image
az webapp config container set \
    --name dream-ai-frontend \
    --resource-group DreamAIAgentGroup \
    --docker-custom-image-name yourdockerhubusername/dream-ai-frontend:latest \
    --docker-registry-server-url https://index.docker.io

# Set frontend environment variables
az webapp config appsettings set --resource-group DreamAIAgentGroup --name dream-ai-frontend --settings \
    NEXT_PUBLIC_API_URL="https://dream-ai-backend.azurewebsites.net" \
    PORT=3000
```

Your frontend will be available at: `https://dream-ai-frontend.azurewebsites.net`

## Step 3: Verify Deployment

1. Check if backend is running:
```bash
curl https://dream-ai-backend.azurewebsites.net/
```

2. Check if frontend is running by visiting:
`https://dream-ai-frontend.azurewebsites.net`

## Troubleshooting

If you see "Application Error":

1. Check backend logs:
```bash
az webapp log tail --name dream-ai-backend --resource-group DreamAIAgentGroup
```

2. Check frontend logs:
```bash
az webapp log tail --name dream-ai-frontend --resource-group DreamAIAgentGroup
```

3. Verify environment variables:
```bash
# Backend
az webapp config appsettings list --name dream-ai-backend --resource-group DreamAIAgentGroup

# Frontend
az webapp config appsettings list --name dream-ai-frontend --resource-group DreamAIAgentGroup
```

4. Restart the apps if needed:
```bash
# Restart backend
az webapp restart --name dream-ai-backend --resource-group DreamAIAgentGroup

# Restart frontend
az webapp restart --name dream-ai-frontend --resource-group DreamAIAgentGroup
```

## Quick Fixes for Common Issues

1. If backend shows "Application Error":
   - Check if WEBSITES_PORT=8000 is set
   - Verify all OpenAI environment variables are set
   - Check container logs for specific error messages

2. If frontend can't connect to backend:
   - Verify NEXT_PUBLIC_API_URL is set correctly
   - Check if backend URL is accessible
   - Verify CORS is properly configured in backend

3. If container fails to start:
   - Check if Docker image exists in Docker Hub
   - Verify container configuration in Azure
   - Check container logs for startup errors

4. Docker Hub Issues:
   - If `docker login` fails, try logging in through the Docker Desktop app
   - If push fails, make sure you're logged in and the image name matches your username
   - Check Docker Hub website to verify your images are uploaded

Remember to:
1. Create Docker Hub account if you don't have one
2. Replace 'yourdockerhubusername' with your actual Docker Hub username (found at https://hub.docker.com/ after login)
3. Set all OpenAI-related environment variables with your actual values
4. Make sure both services are running before testing the chatbot

After deployment, anyone can access your chatbot by visiting:
`https://dream-ai-frontend.azurewebsites.net`
