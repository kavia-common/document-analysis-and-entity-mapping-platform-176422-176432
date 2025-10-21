# Database setup

1) Copy .env.example to .env and set DATABASE_URL to an asyncpg URL:
   postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME

2) Install dependencies (handled by CI using requirements.txt).

3) Run migrations:
   alembic -c alembic.ini upgrade head

4) Auto-generate future revisions:
   alembic -c alembic.ini revision --autogenerate -m "your message"
   alembic -c alembic.ini upgrade head
