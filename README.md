# applications

## Database Migrations

This project uses Alembic for database migrations.

### Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Creating a Migration

To generate a new migration script after modifying `models.py`:

```bash
cd Interview_evaluation
alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations

To apply the migrations to the database:

```bash
cd Interview_evaluation
alembic upgrade head
```
