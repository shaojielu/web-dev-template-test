# FastAPI + Next.js 项目 - 部署

你可以使用 Docker Swarm 将项目部署到远程服务器，实现零停机更新。

该项目依赖 Traefik 代理处理公网流量和 HTTPS 证书。

你可以使用 CI/CD（持续集成与持续部署）系统自动部署，仓库中已提供 GitHub Actions 的配置。

在开始之前，需要先完成一些配置。

## 准备

- 准备一台可用的远程服务器。
- 将域名的 DNS 记录指向这台服务器的 IP。
- 配置域名的通配符子域名，这样可以为不同服务使用不同子域名，例如 `*.fastapi-project.example.com`。这会用于 `dashboard.fastapi-project.example.com`、`api.fastapi-project.example.com`、`traefik.fastapi-project.example.com` 等，也适用于 `staging`，如 `dashboard.staging.fastapi-project.example.com`。
- 在服务器上安装并配置 Docker Engine（不是 Docker Desktop）。

### 初始化 Docker Swarm

在服务器上初始化 Docker Swarm：

```bash
docker swarm init
```

如果服务器有多个网络接口，指定使用的 IP：

```bash
docker swarm init --advertise-addr <SERVER_IP>
```

单节点即可使用 Swarm 的所有编排功能（滚动更新、健康检查、自动回滚等）。

## 公网 Traefik

我们需要 Traefik 代理来处理外部连接和 HTTPS 证书。

下面的步骤只需要执行一次。

### Traefik 配置文件

- 创建远程目录用于存放 Traefik 的配置文件：

```bash
mkdir -p /root/code/traefik-public/
```

将 Traefik 的 Swarm 配置文件复制到服务器。你可以在本地终端使用 `rsync`：

```bash
rsync -a compose.traefik-swarm.yml root@your-server.example.com:/root/code/traefik-public/
```

### Traefik 公网网络

该 Traefik 期望存在一个名为 `traefik-public` 的 Docker overlay 网络，用于与项目栈通信。

这样就会有一个统一的公网 Traefik 代理处理对外的 HTTP/HTTPS 流量，后面可以挂载一个或多个拥有不同域名的项目栈，即使都在同一台服务器上也没有问题。

在远程服务器上运行以下命令创建 `traefik-public` overlay 网络：

```bash
docker network create --driver overlay --attachable traefik-public
```

注意：使用 Docker Swarm 时必须使用 `overlay` 驱动而不是默认的 `bridge` 驱动。`--attachable` 允许独立容器也能连接该网络。

### Traefik 环境变量

Traefik 的配置文件在启动前需要在终端设置一些环境变量。你可以在远程服务器执行以下命令：

- 创建 HTTP Basic Auth 的用户名，例如：

```bash
export USERNAME=admin
```

- 创建 HTTP Basic Auth 的密码环境变量，例如：

```bash
export PASSWORD=changethis
```

- 使用 openssl 生成 HTTP Basic Auth 密码的哈希值并保存到环境变量：

```bash
export HASHED_PASSWORD=$(openssl passwd -apr1 $PASSWORD)
```

可以输出查看哈希值是否正确：

```bash
echo $HASHED_PASSWORD
```

- 设置服务器域名，例如：

```bash
export DOMAIN=fastapi-project.example.com
```

- 设置 Let's Encrypt 使用的邮箱，例如：

```bash
export EMAIL=admin@example.com
```

注意：必须使用真实邮箱，`@example.com` 不可用。

### 启动 Traefik

设置好环境变量且 `compose.traefik-swarm.yml` 就位后，使用 Docker Stack 部署 Traefik：

```bash
cd /root/code/traefik-public/
docker stack deploy -c compose.traefik-swarm.yml traefik
```

验证 Traefik 服务状态：

```bash
docker stack services traefik
```

## 部署 FastAPI + Next.js 项目

Traefik 配置完成后，就可以部署项目了。

注意：你也可以直接跳到 GitHub Actions 的持续部署章节。

## 拷贝代码

```bash
rsync -av --filter=":- .gitignore" ./ root@your-server.example.com:/root/code/app/
```

说明：`--filter=":- .gitignore"` 会让 `rsync` 使用与 git 相同的忽略规则，跳过诸如 Python 虚拟环境等被忽略的文件。

## 环境变量

在部署前需要设置一些环境变量。

### 生成密钥

`.env` 文件里的一些环境变量是占位值，必须改成真正的密钥。你可以使用以下命令生成：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

复制输出结果作为密码或密钥，再运行一次生成另一份安全密钥。

### 必需环境变量

设置 `ENVIRONMENT`，默认是 `local`（开发环境）。部署到服务器时建议设置为 `staging` 或 `production`：

```bash
export ENVIRONMENT=production
```

设置 `DOMAIN`，默认是 `localhost`。部署时使用你的域名，例如：

```bash
export DOMAIN=fastapi-project.example.com
```

设置 `POSTGRES_PASSWORD` 为非占位值：

```bash
export POSTGRES_PASSWORD="changethis"
```

设置用于签名 token 的 `SECRET_KEY`：

```bash
export SECRET_KEY="changethis"
```

设置 `FIRST_SUPERUSER_PASSWORD` 为非占位值：

```bash
export FIRST_SUPERUSER_PASSWORD="changethis"
```

设置后端生成链接使用的 `FRONTEND_HOST`：

```bash
export FRONTEND_HOST="https://dashboard.${DOMAIN?Variable not set}"
```

设置 `BACKEND_CORS_ORIGINS`，包含前端域名：

```bash
export BACKEND_CORS_ORIGINS="https://dashboard.${DOMAIN?Variable not set},https://api.${DOMAIN?Variable not set}"
```

设置 Docker 镜像路径（使用 GHCR）：

```bash
export DOCKER_IMAGE_BACKEND="ghcr.io/<owner>/<repo>/backend"
export DOCKER_IMAGE_FRONTEND="ghcr.io/<owner>/<repo>/frontend"
export TAG="latest"
```

设置栈名称：

```bash
export STACK_NAME="my-app-production"
```

你还可以设置其他环境变量：

- `PROJECT_NAME`：项目名称，用于 API 文档和邮件。
- `FIRST_SUPERUSER`：首个超级用户邮箱。
- `SMTP_HOST`：SMTP 服务地址。
- `SMTP_USER`：SMTP 用户名。
- `SMTP_PASSWORD`：SMTP 密码。
- `SMTP_PORT`：SMTP 端口。
- `SMTP_TLS`：是否启用 SMTP TLS。
- `EMAILS_FROM_EMAIL`：发送邮件的账号。
- `POSTGRES_SERVER`：PostgreSQL 服务器地址。使用 Docker Swarm 时通常保持默认 `db`。
- `POSTGRES_PORT`：PostgreSQL 端口。
- `POSTGRES_USER`：Postgres 用户名。
- `POSTGRES_DB`：数据库名称。
- `SENTRY_DSN`：Sentry DSN（如需使用）。

## GitHub Actions 环境变量

以下环境变量仅在 GitHub Actions 中使用：

- `LATEST_CHANGES`：GitHub Action [latest-changes](https://github.com/tiangolo/latest-changes) 使用的个人访问令牌，用于生成发布说明。
- `SMOKESHOW_AUTH_KEY`：用于发布测试覆盖率报告（Smokeshow）。请根据 Smokeshow 文档创建（可免费）。

### 使用 Docker Swarm 部署

设置好环境变量后，首先构建并推送镜像到容器仓库：

```bash
cd /root/code/app/

# 构建并推送后端镜像
docker build -t ${DOCKER_IMAGE_BACKEND}:${TAG} -f backend/Dockerfile .
docker push ${DOCKER_IMAGE_BACKEND}:${TAG}

# 构建并推送前端镜像
docker build -t ${DOCKER_IMAGE_FRONTEND}:${TAG} \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.${DOMAIN} \
  --build-arg API_BASE_URL=https://api.${DOMAIN} \
  --build-arg NODE_ENV=production \
  -f frontend/Dockerfile .
docker push ${DOCKER_IMAGE_FRONTEND}:${TAG}
```

然后部署应用栈：

```bash
docker stack deploy -c compose.yml -c compose.swarm.yml --with-registry-auth ${STACK_NAME}
```

查看服务状态：

```bash
docker stack services ${STACK_NAME}
```

查看某个服务的日志：

```bash
docker service logs ${STACK_NAME}_backend
```

### 零停机更新

Docker Swarm 使用滚动更新实现零停机部署。更新时：

1. 新容器先启动（`start-first` 策略）
2. 新容器通过健康检查后，旧容器被停止
3. 如果新容器健康检查失败，自动回滚到上一版本

手动回滚某个服务：

```bash
docker service rollback ${STACK_NAME}_backend
```

## 持续部署（CD）

你可以使用 GitHub Actions 自动部署项目。

可以部署多个环境，当前已配置 `staging` 和 `production`。

GitHub Actions 工作流会自动完成以下步骤：

1. 构建 Docker 镜像并推送到 GitHub Container Registry (ghcr.io)
2. 初始化 Swarm 和 overlay 网络（幂等操作）
3. 使用 `docker stack deploy` 部署，自动触发滚动更新

### 安装 GitHub Actions Runner

- 在远程服务器上创建 GitHub Actions 用户：

```bash
sudo adduser github
```

- 给 `github` 用户添加 Docker 权限：

```bash
sudo usermod -aG docker github
```

- 临时切换到 `github` 用户：

```bash
sudo su - github
```

- 进入 `github` 用户的主目录：

```bash
cd
```

- 按照官方文档安装自托管 Runner：
  [Adding self-hosted runners to a repository](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/adding-self-hosted-runners#adding-a-self-hosted-runner-to-a-repository)

- 设置 label 时，添加环境标签，例如 `production`。你也可以稍后添加。

安装完成后，文档会提示你运行命令启动 Runner。但这会在终端关闭或连接断开后停止。

要让它随系统启动并常驻运行，可以将其安装为系统服务。先退出 `github` 用户并回到 `root`：

```bash
exit
```

然后切换到 `root`（如果还没切换）：

```bash
sudo su
```

- 在 `root` 用户下进入 `github` 用户目录中的 `actions-runner`：

```bash
cd /home/github/actions-runner
```

- 将 Runner 安装为系统服务（用户为 `github`）：

```bash
./svc.sh install github
```

- 启动服务：

```bash
./svc.sh start
```

- 查看服务状态：

```bash
./svc.sh status
```

更多信息请参考官方文档：
[Configuring the self-hosted runner application as a service](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/configuring-the-self-hosted-runner-application-as-a-service).

### 设置 Secrets

在仓库中配置所需的 Secrets（与上面的环境变量一致，包括 `SECRET_KEY` 等）。请参考官方文档：
[Creating secrets for a repository](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository)

当前 GitHub Actions 工作流需要的 Secrets：

- `DOMAIN_PRODUCTION`
- `DOMAIN_STAGING`
- `STACK_NAME_PRODUCTION`
- `STACK_NAME_STAGING`
- `EMAILS_FROM_EMAIL`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `SMTP_HOST`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_PORT`
- `SMTP_TLS`
- `SENTRY_DSN`（可选）
- `POSTGRES_USER`（可选，默认 `postgres`）
- `POSTGRES_DB`（可选，默认 `app`）
- `POSTGRES_PORT`（可选，默认 `5432`）
- `LATEST_CHANGES`
- `SMOKESHOW_AUTH_KEY`

注意：`DOCKER_IMAGE_BACKEND`、`DOCKER_IMAGE_FRONTEND`、`TAG`、`FRONTEND_HOST`、`BACKEND_CORS_ORIGINS`、`POSTGRES_SERVER` 由工作流自动计算，无需配置为 Secret。

## GitHub Action 部署工作流

`.github/workflows` 目录里已有用于部署环境的 GitHub Action 工作流（使用带标签的 Runner）：

- `staging`：推送（或合并）到 `master` 分支后触发
- `production`：发布 release 后触发

工作流会自动构建镜像、推送到 GHCR、并通过 `docker stack deploy` 实现零停机滚动更新。

如需新增环境，可在现有工作流基础上调整。

## URLs

请将 `fastapi-project.example.com` 替换为你的域名。

### Traefik 控制面板

Traefik UI: `https://traefik.fastapi-project.example.com`

### Production

Frontend: `https://dashboard.fastapi-project.example.com`

Backend API docs: `https://api.fastapi-project.example.com/docs`

Backend API base URL: `https://api.fastapi-project.example.com`

### Staging

Frontend: `https://dashboard.staging.fastapi-project.example.com`

Backend API docs: `https://api.staging.fastapi-project.example.com/docs`

Backend API base URL: `https://api.staging.fastapi-project.example.com`
