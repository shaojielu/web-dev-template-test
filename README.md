# Full Stack FastAPI + Next.js Template

全栈 Web 应用模板：**FastAPI** (Python 3.13) 后端 + **Next.js** (React 19) 前端，使用 PostgreSQL、Docker Compose 和 Traefik 反向代理。

## 技术栈

- **后端**: [FastAPI](https://fastapi.tiangolo.com) + [SQLAlchemy](https://www.sqlalchemy.org) 2.0 (异步) + [Pydantic](https://docs.pydantic.dev)
- **前端**: [Next.js](https://nextjs.org) 16 + React 19 (App Router, Server Components, Server Actions)
- **数据库**: [PostgreSQL](https://www.postgresql.org) 18 + [Alembic](https://alembic.sqlalchemy.org) 数据库迁移
- **样式**: [Tailwind CSS](https://tailwindcss.com) 4
- **认证**: JWT (HTTP Cookie) + bcrypt 密码哈希
- **测试**: [Pytest](https://pytest.org) (后端) + [Playwright](https://playwright.dev) (前端 E2E)
- **部署**: [Docker Compose](https://www.docker.com) + [Traefik](https://traefik.io) 反向代理 + 自动 HTTPS
- **开发工具**: [Mailcatcher](https://mailcatcher.me) (邮件测试) + [Adminer](https://www.adminer.org) (数据库管理) + [Sentry](https://sentry.io) (错误监控)
- **代码质量**: [Ruff](https://docs.astral.sh/ruff/) (lint/format) + [Mypy](https://mypy-lang.org) (类型检查) + [ESLint](https://eslint.org/)

## 截图

### 登录页

![Login](img/login.png)

### 管理面板

![Dashboard](img/dashboard.png)

### Dashboard - Dark Mode

![Dark Mode](img/dashboard-dark.png)

### API 文档

![API docs](img/docs.png)

## 快速开始

### 环境要求

- [Docker](https://www.docker.com/) & Docker Compose
- [Node.js](https://nodejs.org/) 20+ & [pnpm](https://pnpm.io/)
- [Python](https://www.python.org/) 3.13+ & [uv](https://docs.astral.sh/uv/)

### 1. 克隆并配置

```bash
git clone <your-repo-url>
cd web-dev-template
```

编辑 `.env` 文件，确保部署前修改以下值：

- `SECRET_KEY` — JWT 密钥
- `FIRST_SUPERUSER_PASSWORD` — 初始超级管理员密码
- `POSTGRES_PASSWORD` — 数据库密码

生成安全密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. 启动开发环境

```bash
# 启动全部服务（db, backend, frontend, mailcatcher, traefik, adminer）
docker compose watch
```

Windows 环境下如遇端口 5432 冲突，可使用：

```bash
.\scripts\dev-up.ps1    # 启动
.\scripts\dev-down.ps1  # 停止
```

### 3. 访问服务

| 服务                 | 地址                         |
| -------------------- | ---------------------------- |
| 前端                 | <http://localhost:3000>      |
| 后端 API             | <http://localhost:8000>      |
| API 文档             | <http://localhost:8000/docs> |
| Adminer (数据库管理) | <http://localhost:8080>      |
| Traefik Dashboard    | <http://localhost:8090>      |
| Mailcatcher          | <http://localhost:1080>      |

默认超级管理员账号：`admin@example.com`

## 开发

### 本地运行前端（不使用 Docker）

```bash
docker compose stop frontend
cd frontend && pnpm install && pnpm dev
```

### 本地运行后端（不使用 Docker）

```bash
docker compose stop backend
cd backend && fastapi run --reload app/main.py
```

### 后端测试

测试要求 `ENVIRONMENT=test` 且 `POSTGRES_DB` 以 `_test` 结尾。

```bash
# 确保数据库运行
docker compose up -d db

# 运行全部测试
cd backend
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost \
  POSTGRES_PORT=5432 POSTGRES_USER=postgres \
  POSTGRES_PASSWORD=aabbccpostgres uv run pytest

# 运行单个测试文件
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost \
  POSTGRES_PORT=5432 POSTGRES_USER=postgres \
  POSTGRES_PASSWORD=aabbccpostgres uv run pytest tests/api/test_users.py

# 带覆盖率报告
cd backend && uv run bash scripts/test.sh
```

### 前端 E2E 测试 (Playwright)

```bash
# 通过 Docker 运行（推荐）
docker compose up -d
docker compose run --rm playwright npx playwright test

# 运行指定测试文件
docker compose run --rm playwright npx playwright test tests/auth.spec.ts
```

### 代码检查

```bash
# 后端
cd backend
uv run ruff check app          # lint
uv run ruff format app --check # 格式检查
uv run mypy app                # 类型检查
uv run bash scripts/lint.sh    # 全部检查

# 前端
cd frontend
pnpm lint
```

### 数据库迁移 (Alembic)

```bash
cd backend
uv run alembic revision --autogenerate -m "description"  # 生成迁移
uv run alembic upgrade head                              # 执行迁移
uv run alembic downgrade -1                              # 回滚一步
```

## 项目结构

```text
├── backend/
│   ├── app/
│   │   ├── api/          # 路由处理 & 依赖注入
│   │   ├── core/         # 配置、数据库、安全
│   │   ├── models/       # SQLAlchemy ORM 模型
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   └── services/     # 业务逻辑层
│   ├── alembic/          # 数据库迁移
│   └── tests/
├── frontend/
│   ├── app/
│   │   ├── dashboard/    # 受保护路由
│   │   ├── login/        # 认证页面
│   │   ├── lib/          # API 调用、Server Actions、类型定义
│   │   └── ui/           # 可复用 UI 组件
│   └── public/
├── compose.yml           # 生产配置
├── compose.override.yml  # 开发环境覆盖
└── .env                  # 环境变量配置
```

## 部署

详见 [deployment.md](./deployment.md)。

## 更多文档

- [开发指南](./development.md)
- [后端文档](./backend/README.md)
- [前端文档](./frontend/README.md)

## License

MIT License
