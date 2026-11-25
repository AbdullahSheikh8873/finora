# Finora — Personal Finance Management Platform

Finora is a full-stack personal finance app: accounts, transactions, transfers, budgets, dashboards and reports. It runs on FastAPI + PostgreSQL with a server-rendered Jinja2 UI, and is deployed on AWS EC2 using Docker, Amazon ECR and Nginx.

## Demo

▶ Demo video: https://github.com/user-attachments/assets/8dde6a5b-2624-45ea-9101-6f632a1a2f0b

> The AWS environment was shut down after testing to avoid extra cost. The video shows the full working app on EC2.

## Features

- Email/password auth with JWT (httpOnly cookie), bcrypt password hashing
- Multiple accounts (bank, cash, savings, credit card, wallet) with live balances
- Income/expense transactions with categories, search, filters and pagination
- Atomic money transfers between accounts
- Monthly budgets per category with safe / warning / critical status
- Dashboard with SQL-aggregated stats and Chart.js charts
- Reports with flexible date ranges and CSV export
- In-app notifications (budget alerts, large expenses)
- Light/dark theme, responsive design
- Per-user data isolation enforced in the service layer

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, python-jose (JWT), passlib/bcrypt, Uvicorn + Gunicorn |
| Database | PostgreSQL |
| Frontend | Jinja2, vanilla JavaScript, Chart.js, custom CSS |
| Containers | Docker, Docker Compose |
| Registry | Amazon ECR |
| Compute | AWS EC2 (t3.micro, Ubuntu 24.04) |
| Reverse proxy | Nginx |
| Version control | Git & GitHub |

## Architecture & Deployment Flow

```
Developer → GitHub → Docker build → Amazon ECR → EC2 (pull image & deploy) → Nginx (port 80) → FastAPI app (8000) → PostgreSQL (5432)
```

- Nginx is the only container with a published port. It proxies requests to the FastAPI app over Docker's internal network.
- Only the app talks to PostgreSQL. PostgreSQL is never exposed to the host or the internet.
- The Docker image is built once, pushed to ECR, and pulled on EC2.

## Project Structure

```
finora/
├── app/
│   ├── main.py
│   ├── core/          # config, database, security, deps, logging
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── api/           # routers
│   ├── services/      # business logic, ownership checks
│   ├── templates/     # Jinja2 pages
│   └── static/        # css, js
├── alembic/           # migrations
├── tests/             # pytest suite (real PostgreSQL)
├── scripts/seed_demo.py
├── deploy/nginx.conf
├── docs/finora-architecture.png
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## Run Locally (Docker)

```bash
git clone https://github.com/AbdullahSheikh8873/finora.git
cd finora
cp .env.example .env
# edit .env: SECRET_KEY, POSTGRES_PASSWORD, DATABASE_URL
docker compose up -d --build
```

Open http://localhost. Migrations (`alembic upgrade head`) run automatically when the app starts.

Generate a strong secret key:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Useful commands:

```bash
docker compose logs -f app     # app logs
docker compose down            # stop
docker compose down -v         # stop and delete the database volume
```

## Environment Variables

See `.env.example`. Never commit a real `.env`.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs JWTs (long, random, secret) |
| `DATABASE_URL` | SQLAlchemy connection string |
| `JWT_EXPIRE_MINUTES` | Session length |
| `POSTGRES_*` | Initialises the PostgreSQL container |
| `COOKIE_SECURE` | Set `true` once served over HTTPS |
| `CORS_ORIGINS` | Allowed origins, comma-separated |
| `DEFAULT_CURRENCY` | Default currency for new users |

## Deploy to AWS (EC2 + ECR)

**1. Build and push the image to ECR (from your machine)**

```bash
aws ecr create-repository --repository-name finora --region <region>

aws ecr get-login-password --region <region> | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

docker build -t finora .
docker tag finora:latest <account-id>.dkr.ecr.<region>.amazonaws.com/finora:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/finora:latest
```

**2. Launch EC2**

- Ubuntu 24.04 LTS, `t3.micro`, 20 GB gp3 storage
- Security Group inbound: 22 (SSH, your IP only), 80 (HTTP). Keep 5432 and 8000 closed.
- Attach an IAM role that allows pulling from ECR (for example `AmazonEC2ContainerRegistryReadOnly`).

**3. Install Docker on the instance**

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
```

**4. Pull the image and start the stack**

```bash
aws ecr get-login-password --region <region> | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

git clone https://github.com/AbdullahSheikh8873/finora.git && cd finora
cp .env.example .env && nano .env      # APP_ENV=production, DEBUG=false, strong SECRET_KEY and POSTGRES_PASSWORD
# in docker-compose.yml, set the app service to: image: <account-id>.dkr.ecr.<region>.amazonaws.com/finora:latest
docker compose pull app
docker compose up -d
```

**5. Verify**

```bash
curl http://localhost/health
# {"status":"healthy","database":"ok"}
```

Then open `http://<EC2_PUBLIC_IP>` in the browser.

**Update the app**

```bash
# on your machine: build, tag, push a new image
# on EC2:
docker compose pull app && docker compose up -d app
```

## Database Migrations

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
alembic downgrade -1
```

Inside Docker: `docker compose exec app alembic upgrade head`.

## Tests

The tests run against a real PostgreSQL database, so constraints and numeric precision match production.

```bash
createdb finora_test
pytest -v
```

They cover auth, account and transaction CRUD, atomic transfers, budget thresholds, dashboard aggregation, and cross-user data isolation.

## PostgreSQL Backup

```bash
docker compose exec postgres pg_dump -U finora finora > finora_backup_$(date +%Y%m%d).sql
```

Store backups off the instance (for example in S3).

## Security Notes

- Passwords are hashed with bcrypt and never logged.
- JWTs are sent as httpOnly, SameSite=Lax cookies.
- Every service function that touches user data checks `resource.user_id == current_user.id`.
- Money values use PostgreSQL `NUMERIC(14,2)`, never floating point.
- PostgreSQL is reachable only from the app container.
- `.env`, keys and state files are in `.gitignore`.

## Future Improvements

- HTTPS with a domain and Certbot
- Recurring transactions and scheduled bills
- Multi-currency accounts with live exchange rates
- PDF report export
- Rate limiting on auth endpoints
- CI/CD pipeline to build and push to ECR automatically

## Author

Abdullah Sheikh — [GitHub](https://github.com/AbdullahSheikh8873)
