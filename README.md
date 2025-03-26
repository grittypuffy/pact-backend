<h1>PACT: Prompt Auto-Correction and Testing</h1>
<h6>"A golden gateway to improve prompt-engineering skills of the users."</h6>

# Backend Development

1. Install the dependencies by creating a virtual environment

```shell
git clone https://github.com/grittypuffy/pact-backend
cd pact-backend
poetry env use python3.13
```

# Activate the virtual environment on Linux distrubutions.
```shell
source $(poetry env info --path)/bin/activate
```
# Install dependencies
```shell
poetry install
```

2. Generate self-signed certificates for HTTPS, this is needed to set cookies during local development. Install mkcert to generate it.

```shell
mkdir certs
cd certs
mkcert localhost
```

3. Start the development server in the project root directory by the following command once the environment variables have been configured correctly as per .env sample:

```shell
poetry run python -m uvicorn --ssl-certfile certs/localhost.pem --ssl-keyfile certs/localhost-key.pem --workers 4 pact_backend.server:app --reload
```

This should start the development server at https://0.0.0.0:8000/

## Docker

1. Build the Docker image using the following command:

```shell
docker buildx build -t pact-backend:latest .
```

2. Deploy it using docker run command or by pushing to a container registry (Azure Container Registry or Docker Hub) by tagging the image appropriately.