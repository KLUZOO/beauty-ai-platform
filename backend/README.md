# beauty-ai-platform(backend)

## Running the Project with Docker

To build the Docker images and start all required services (Django, Celery, Celery Beat, and Redis), run the following command from the project root:

```bash
  docker compose -f docker-compose.yml up --build
```

This command will:

- Build the Docker images.
- Start the Django development server.
- Start the Celery worker.
- Start the Celery Beat scheduler.
- Start the Redis server.

After the containers are running, the application will be available at:

- **Django:** http://localhost:8000
- **Swagger-ui:** http://localhost:8000/api/schema/swagger-ui/
