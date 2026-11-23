# Run with Docker

Build the image from the repository root:

```bash
docker build -t sabify-ai .
```

Create a root-level `.env` file containing your Hugging Face token, then start
the container:

```bash
docker run --rm -p 8082:8082 --env-file .env sabify-ai
```

Open the interface at `http://localhost:8082`. Check the service with:

```bash
curl http://localhost:8082/health
```

The container includes both the API and its static frontend.
