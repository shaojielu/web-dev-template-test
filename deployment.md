# FastAPI + Next.js Project - Deployment


You can deploy the project to a remote server using Docker Swarm, enabling zero-downtime updates.

The project relies on a Traefik proxy to handle public traffic and HTTPS certificates.

You can use a CI/CD (Continuous Integration and Continuous Deployment) system to deploy automatically. GitHub Actions configuration is already provided in the repository.

Before getting started, some configuration is required.

## Prerequisites

* Have a remote server ready.
* Point your domain's DNS records to the server's IP address.
* Configure a wildcard subdomain for your domain so that different services can use different subdomains, e.g. `*.fastapi-project.example.com`. This will be used for `dashboard.fastapi-project.example.com`, `api.fastapi-project.example.com`, `traefik.fastapi-project.example.com`, etc., as well as for `staging`, e.g. `dashboard.staging.fastapi-project.example.com`.
* Install and configure Docker Engine (not Docker Desktop) on the server.

### Initialize Docker Swarm

Initialize Docker Swarm on the server:

```bash
docker swarm init
```

If the server has multiple network interfaces, specify the IP to use:

```bash
docker swarm init --advertise-addr <SERVER_IP>
```

A single node is sufficient to use all Swarm orchestration features (rolling updates, health checks, automatic rollbacks, etc.).

## Public Traefik

We need a Traefik proxy to handle external connections and HTTPS certificates.

The following steps only need to be performed once.

### Traefik Configuration Files

* Create a remote directory to store the Traefik configuration files:

```bash
mkdir -p /root/code/traefik-public/
```

Copy the Traefik Swarm configuration file to the server. You can use `rsync` from your local terminal:

```bash
rsync -a compose.traefik-swarm.yml root@your-server.example.com:/root/code/traefik-public/
```

### Traefik Public Network

This Traefik setup expects a Docker overlay network named `traefik-public` to communicate with the project stack.

This provides a single public Traefik proxy handling external HTTP/HTTPS traffic, and you can attach one or more project stacks with different domains behind it, even on the same server.

Run the following command on the remote server to create the `traefik-public` overlay network:

```bash
docker network create --driver overlay --attachable traefik-public
```

Note: When using Docker Swarm, the `overlay` driver must be used instead of the default `bridge` driver. The `--attachable` flag allows standalone containers to connect to this network as well.

### Traefik Environment Variables

The Traefik configuration file requires some environment variables to be set in the terminal before starting. You can run the following commands on the remote server:

* Create the HTTP Basic Auth username, for example:

```bash
export USERNAME=admin
```

* Create the HTTP Basic Auth password environment variable, for example:

```bash
export PASSWORD=changethis
```

* Use openssl to generate a hash of the HTTP Basic Auth password and store it in an environment variable:

```bash
export HASHED_PASSWORD=$(openssl passwd -apr1 $PASSWORD)
```

You can print the hash to verify it was generated correctly:

```bash
echo $HASHED_PASSWORD
```

* Set the server domain, for example:

```bash
export DOMAIN=fastapi-project.example.com
```

* Set the email address used by Let's Encrypt, for example:

```bash
export EMAIL=admin@example.com
```

Note: You must use a real email address; `@example.com` will not work.

### Start Traefik

Once the environment variables are set and `compose.traefik-swarm.yml` is in place, deploy Traefik using Docker Stack:

```bash
cd /root/code/traefik-public/
docker stack deploy -c compose.traefik-swarm.yml traefik
```

Verify the Traefik service status:

```bash
docker stack services traefik
```

## Deploy the FastAPI + Next.js Project

Once Traefik is configured, you can deploy the project.

Note: You can also skip ahead to the GitHub Actions Continuous Deployment section.

## Copy the Code

```bash
rsync -av --filter=":- .gitignore" ./ root@your-server.example.com:/root/code/app/
```

Explanation: The `--filter=":- .gitignore"` flag makes `rsync` use the same ignore rules as git, skipping ignored files such as Python virtual environments.

## Environment Variables

Some environment variables need to be set before deployment.

### Generate Secret Keys

Some environment variables in the `.env` file have placeholder values that must be replaced with real secret keys. You can generate them using the following command:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output to use as a password or secret key, and run the command again to generate another one.

### Required Environment Variables

Set `ENVIRONMENT` — the default is `local` (development). When deploying to a server, it is recommended to set it to `staging` or `production`:

```bash
export ENVIRONMENT=production
```

Set `DOMAIN` — the default is `localhost`. When deploying, use your domain name, for example:

```bash
export DOMAIN=fastapi-project.example.com
```

Set `POSTGRES_PASSWORD` to a non-placeholder value:

```bash
export POSTGRES_PASSWORD="changethis"
```

Set `SECRET_KEY`, used for signing tokens:

```bash
export SECRET_KEY="changethis"
```

Set `FIRST_SUPERUSER_PASSWORD` to a non-placeholder value:

```bash
export FIRST_SUPERUSER_PASSWORD="changethis"
```

Set `FRONTEND_HOST`, used by the backend to generate links:

```bash
export FRONTEND_HOST="https://dashboard.${DOMAIN?Variable not set}"
```

Set `BACKEND_CORS_ORIGINS`, including the frontend domain:

```bash
export BACKEND_CORS_ORIGINS="https://dashboard.${DOMAIN?Variable not set},https://api.${DOMAIN?Variable not set}"
```

Set the Docker image paths (using GHCR):

```bash
export DOCKER_IMAGE_BACKEND="ghcr.io/<owner>/<repo>/backend"
export DOCKER_IMAGE_FRONTEND="ghcr.io/<owner>/<repo>/frontend"
export TAG="latest"
```

Set the stack name:

```bash
export STACK_NAME="my-app-production"
```

You can also set the following optional environment variables:

* `PROJECT_NAME`: The project name, used in API documentation and emails.
* `FIRST_SUPERUSER`: The email address of the first superuser.
* `SMTP_HOST`: SMTP server address.
* `SMTP_USER`: SMTP username.
* `SMTP_PASSWORD`: SMTP password.
* `SMTP_PORT`: SMTP port.
* `SMTP_TLS`: Whether to enable SMTP TLS.
* `EMAILS_FROM_EMAIL`: The email address used to send emails.
* `POSTGRES_SERVER`: PostgreSQL server address. When using Docker Swarm, the default `db` is typically kept.
* `POSTGRES_PORT`: PostgreSQL port.
* `POSTGRES_USER`: Postgres username.
* `POSTGRES_DB`: Database name.
* `SENTRY_DSN`: Sentry DSN (if needed).

## GitHub Actions Environment Variables

The following environment variables are only used in GitHub Actions:

* `LATEST_CHANGES`: A personal access token used by the GitHub Action [latest-changes](https://github.com/tiangolo/latest-changes) to generate release notes.
* `SMOKESHOW_AUTH_KEY`: Used to publish test coverage reports (Smokeshow). Please create one according to the Smokeshow documentation (free).

### Deploy with Docker Swarm

Once the environment variables are set, first build and push the images to the container registry:

```bash
cd /root/code/app/

# Build and push the backend image
docker build -t ${DOCKER_IMAGE_BACKEND}:${TAG} -f backend/Dockerfile .
docker push ${DOCKER_IMAGE_BACKEND}:${TAG}

# Build and push the frontend image
docker build -t ${DOCKER_IMAGE_FRONTEND}:${TAG} \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.${DOMAIN} \
  --build-arg API_BASE_URL=https://api.${DOMAIN} \
  --build-arg NODE_ENV=production \
  -f frontend/Dockerfile .
docker push ${DOCKER_IMAGE_FRONTEND}:${TAG}
```

Then deploy the application stack:

```bash
docker stack deploy -c compose.yml -c compose.swarm.yml --with-registry-auth ${STACK_NAME}
```

Check the service status:

```bash
docker stack services ${STACK_NAME}
```

View the logs for a specific service:

```bash
docker service logs ${STACK_NAME}_backend
```

### Zero-Downtime Updates

Docker Swarm uses rolling updates to achieve zero-downtime deployments. During an update:

1. New containers start first (`start-first` strategy)
2. Once the new containers pass health checks, the old containers are stopped
3. If the new containers fail health checks, an automatic rollback to the previous version is performed

Manually roll back a service:

```bash
docker service rollback ${STACK_NAME}_backend
```

## Continuous Deployment (CD)

You can use GitHub Actions to deploy the project automatically.

Multiple environments can be deployed; `staging` and `production` are currently configured.

The GitHub Actions workflows automatically perform the following steps:

1. Build Docker images and push them to GitHub Container Registry (ghcr.io)
2. Initialize Swarm and overlay network (idempotent operation)
3. Deploy using `docker stack deploy`, which automatically triggers a rolling update

### Install the GitHub Actions Runner

* Create a GitHub Actions user on the remote server:

```bash
sudo adduser github
```

* Grant Docker permissions to the `github` user:

```bash
sudo usermod -aG docker github
```

* Temporarily switch to the `github` user:

```bash
sudo su - github
```

* Navigate to the `github` user's home directory:

```bash
cd
```

* Follow the official documentation to install the self-hosted runner:
  [Adding self-hosted runners to a repository](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/adding-self-hosted-runners#adding-a-self-hosted-runner-to-a-repository)

* When setting labels, add an environment label such as `production`. You can also add it later.

After installation, the documentation will prompt you to run a command to start the runner. However, this will stop when the terminal is closed or the connection is lost.

To make it start automatically with the system and run persistently, you can install it as a system service. First, exit the `github` user and return to `root`:

```bash
exit
```

Then switch to `root` (if you haven't already):

```bash
sudo su
```

* As the `root` user, navigate to the `actions-runner` directory inside the `github` user's home directory:

```bash
cd /home/github/actions-runner
```

* Install the runner as a system service (running as the `github` user):

```bash
./svc.sh install github
```

* Start the service:

```bash
./svc.sh start
```

* Check the service status:

```bash
./svc.sh status
```

For more information, refer to the official documentation:
[Configuring the self-hosted runner application as a service](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/configuring-the-self-hosted-runner-application-as-a-service).

### Configure Secrets

Configure the required secrets in the repository (matching the environment variables described above, including `SECRET_KEY`, etc.). Refer to the official documentation:
[Creating secrets for a repository](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository)

The current GitHub Actions workflows require the following secrets:

* `DOMAIN_PRODUCTION`
* `DOMAIN_STAGING`
* `STACK_NAME_PRODUCTION`
* `STACK_NAME_STAGING`
* `EMAILS_FROM_EMAIL`
* `FIRST_SUPERUSER`
* `FIRST_SUPERUSER_PASSWORD`
* `POSTGRES_PASSWORD`
* `SECRET_KEY`
* `SMTP_HOST`
* `SMTP_USER`
* `SMTP_PASSWORD`
* `SMTP_PORT`
* `SMTP_TLS`
* `SENTRY_DSN` (optional)
* `POSTGRES_USER` (optional, defaults to `postgres`)
* `POSTGRES_DB` (optional, defaults to `app`)
* `POSTGRES_PORT` (optional, defaults to `5432`)
* `LATEST_CHANGES`
* `SMOKESHOW_AUTH_KEY`

Note: `DOCKER_IMAGE_BACKEND`, `DOCKER_IMAGE_FRONTEND`, `TAG`, `FRONTEND_HOST`, `BACKEND_CORS_ORIGINS`, and `POSTGRES_SERVER` are automatically computed by the workflows and do not need to be configured as secrets.

## GitHub Action Deployment Workflows

The `.github/workflows` directory contains GitHub Action workflows for deploying to environments (using labeled runners):

* `staging`: Triggered on push (or merge) to the `main` branch
* `production`: Triggered on release publication

The workflows automatically build images, push them to GHCR, and perform zero-downtime rolling updates via `docker stack deploy`.

To add new environments, adjust the existing workflows as needed.

## URLs

Replace `fastapi-project.example.com` with your domain.

### Traefik Dashboard

Traefik UI: `https://traefik.fastapi-project.example.com`

### Production

Frontend: `https://dashboard.fastapi-project.example.com`

Backend API docs: `https://api.fastapi-project.example.com/docs`

Backend API base URL: `https://api.fastapi-project.example.com`

### Staging

Frontend: `https://dashboard.staging.fastapi-project.example.com`

Backend API docs: `https://api.staging.fastapi-project.example.com/docs`

Backend API base URL: `https://api.staging.fastapi-project.example.com`
