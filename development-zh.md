# FastAPI + Next.js 项目 - 开发

## Docker Compose

- 使用 Docker Compose 启动本地环境：

```bash
docker compose watch
```

- 或者不使用 watch 直接构建并运行：

```bash
docker compose up -d --build
```

### Windows 一键脚本（推荐）

如果你在 Windows 下开发，且本机已有其他容器占用了 `5432`，请优先使用以下脚本：

```powershell
.\scripts\dev-up.ps1
```

脚本会自动：

- 检测并临时停掉占用 `5432` 的容器；
- 启动 `db/backend/frontend/mailcatcher`；
- 校验后端与前端健康检查。

结束开发后运行：

```powershell
.\scripts\dev-down.ps1
```

该脚本会关闭当前项目容器，并恢复之前被临时停掉的 `5432` 占用容器。

- 启动后可访问以下地址：

Frontend (Next.js): <http://localhost:3000>

Backend（OpenAPI JSON API）: <http://localhost:8000>

Swagger UI（后端交互式文档）: <http://localhost:8000/docs>

Adminer（数据库管理）：<http://localhost:8080>

Traefik UI（查看路由）：<http://localhost:8090>

MailCatcher（本地 SMTP UI）：<http://localhost:1080>

**注意**：首次启动可能需要一点时间，后端会等待数据库就绪并完成初始化。可以通过日志观察启动过程。

查看日志（另开终端）：

```bash
docker compose logs
```

查看某个服务的日志，例如：

```bash
docker compose logs backend
```

## MailCatcher

MailCatcher 是一个简单的本地 SMTP 服务，会捕获后端在开发环境发送的邮件，并在网页中展示。

适用于：

- 测试邮件功能
- 验证邮件内容和格式
- 调试邮件相关问题而无需发送真实邮件

本地 Docker Compose 会自动配置后端使用 MailCatcher（SMTP 端口 1025）。访问 <http://localhost:1080> 查看捕获的邮件。

## 本地开发

Docker Compose 已将每个服务暴露在 `localhost` 的不同端口。

后端和前端使用与本地开发服务器相同的端口：后端 `http://localhost:8000`，前端 `http://localhost:3000`。

这样你可以停掉某个 Docker 服务并改用本地开发服务器，端口保持一致。

本地 `docker compose` 默认将 PostgreSQL 映射到 `localhost:5432`。

例如，停掉 `frontend` 服务后启动本地前端：

```bash
docker compose stop frontend
cd frontend
pnpm dev
```

本地 Next.js 开发时需要配置 API 地址（例如在 `frontend/.env.local` 中）：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000
```

或者停掉 `backend` 服务并启动本地后端：

```bash
docker compose stop backend
cd backend
fastapi run --reload app/main.py
```

## 运行后端测试（Pytest）

后端测试会执行 destructive 初始化（`drop_all/create_all`），建议使用：

- `ENVIRONMENT=test`
- 独立测试库，例如 `POSTGRES_DB=app_test`

推荐命令（在 `backend/` 目录）：

```bash
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=changethis uv run pytest
```

测试在 `staging` 和 `production` 环境会被阻止执行。

如果你先在项目根目录启动数据库：

```bash
docker compose up -d db
```

可用以下一条命令完成最小测试环境与测试执行：

```bash
cp .env.example .env && \
sed -i 's/^ENVIRONMENT=.*/ENVIRONMENT=test/' .env && \
sed -i 's/^POSTGRES_DB=.*/POSTGRES_DB=app_test/' .env && \
cd backend && uv run pytest
```

## 使用 `localhost.tiangolo.com` 的 Docker Compose

默认情况下，Docker Compose 会使用 `localhost` 并为各服务分配不同端口。

在生产（或测试）环境中，服务通常运行在不同子域名下，例如 `api.example.com` 和 `dashboard.example.com`。

在 [deployment](deployment.md) 中有 Traefik 相关说明，它负责根据子域名将流量转发到对应服务。

如果希望在本地模拟这种子域名访问，可以修改根目录的 `.env`：

```dotenv
DOMAIN=localhost.tiangolo.com
```

Docker Compose 会使用这个域名配置服务。

Traefik 会将 `api.localhost.tiangolo.com` 路由到后端，将 `dashboard.localhost.tiangolo.com` 路由到前端。

`localhost.tiangolo.com` 是一个特殊域名，所有子域名都指向 `127.0.0.1`，便于本地测试。

修改后重新启动：

```bash
docker compose watch
```

生产环境中，Traefik 通常在 Docker Compose 之外单独部署。本地开发时，`compose.override.yml` 中包含一个 Traefik 以便测试子域名路由。

## Docker Compose 文件与环境变量

主配置文件是 `compose.yml`，`docker compose` 会默认加载它。

`compose.override.yml` 包含开发环境的覆盖配置（例如挂载源码），会自动叠加到 `compose.yml` 之上。

这些 Docker Compose 文件使用根目录的 `.env` 向容器注入环境变量。

同时也会使用脚本中设置的额外环境变量。

修改变量后请重启：

```bash
docker compose watch
```

## .env 文件

根目录 `.env` 包含 Docker 与后端配置、密钥、密码等信息。

如果项目是公开的，你需要避免提交 `.env`。建议提交 `.env.example`，并在 CI/CD 中配置真实环境变量。

本地 Next.js 开发应使用 `frontend/.env.local`（或 shell 环境变量），而不是根目录 `.env`。

## 预提交与代码规范

项目使用 [prek](https://prek.j178.dev/) 进行代码检查与格式化（现代版 Pre-commit）。

安装后，它会在 git 提交前自动运行，确保代码风格一致。

配置文件为根目录的 `.pre-commit-config.yaml`。

### 安装 prek

`prek` 已包含在项目依赖中。

在本地安装 hook（进入 `backend` 目录）：

```bash
cd backend
uv run prek install -f
```

`-f` 用于强制安装（若已存在旧的 pre-commit hook）。

之后每次 `git commit` 都会自动执行。

### 手动运行 prek

你也可以手动运行全部检查：

```bash
cd backend
uv run prek run --all-files
```

## URLs

生产或测试环境将使用相同路径，只是替换为你的域名。

### Development URLs

Frontend: <http://localhost:3000>

Backend: <http://localhost:8000>

Swagger UI: <http://localhost:8000/docs>

ReDoc: <http://localhost:8000/redoc>

Adminer: <http://localhost:8080>

Traefik UI: <http://localhost:8090>

MailCatcher: <http://localhost:1080>

### Development URLs with `localhost.tiangolo.com` Configured

Frontend: <http://dashboard.localhost.tiangolo.com>

Backend: <http://api.localhost.tiangolo.com>

Swagger UI: <http://api.localhost.tiangolo.com/docs>

ReDoc: <http://api.localhost.tiangolo.com/redoc>

Adminer: <http://localhost.tiangolo.com:8080>

Traefik UI: <http://localhost.tiangolo.com:8090>

MailCatcher: <http://localhost.tiangolo.com:1080>
