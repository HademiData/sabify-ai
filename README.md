# SABIFY AI

SABIFY AI is a FastAPI service that creates multiple-choice quizzes from a topic
or study material. It includes a small browser interface and uses the Hugging
Face Router to generate questions.

<img width="1673" height="991" alt="image" src="https://github.com/user-attachments/assets/7f1aa349-a165-41cb-b80a-2ba3cc386e61" />

## Run locally

Requirements: Python 3.10+ and a Hugging Face API token.

```bash
python3 -m venv .venv
source .venv/bin/actfeature/quiz-generator-frontendivate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
HF_TOKEN=your_huggingface_token
```

Start the service:

```bash
uvicorn app.main:app --reload --port 8082
```

Open the quiz interface at [http://localhost:8082](http://localhost:8082) or the
API documentation at [http://localhost:8082/docs](http://localhost:8082/docs).
The health endpoint is `/health`.

## Generate a quiz

Send a topic or study material to `POST /api/v1/quiz/generate`:

```bash
curl http://localhost:8082/api/v1/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The water cycle",
    "number_of_questions": 5,
    "difficulty": "basic"
  }'
```

You can use `material_text` instead of `topic`. The question count must be
between 1 and 20. Each response includes four options, a zero-based
`correct_answer` index, and an explanation.

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `HF_TOKEN` | Yes | — | Hugging Face API token |
| `HF_MODEL` | No | `deepseek-ai/DeepSeek-V3-0324` | Model used by the Hugging Face Router |
| `PORT` | No | `8082` | Port used when starting with `python -m app.main` |

Keep `.env` out of version control.

## Project layout

```text
app/
  api/                    HTTP routes
  core/                   Environment configuration
  models/                 Request and response schemas
  services/               Quiz generation and AI provider client
  utils/                  Shared utilities
  main.py                 FastAPI application
frontend/                 Static quiz interface
docs/                     Local and Docker setup notes
```

The API route validates incoming requests, the quiz service builds and validates
quiz content, and the Hugging Face client handles provider communication. The
frontend is served by the same FastAPI application.

## Tests

```bash
python -m unittest discover -s tests
```

## Docker

```bash
docker build -t sabify-ai .
docker run --rm -p 8082:8082 --env-file .env sabify-ai
```

See [local setup](docs/running-the-service.md) and [Docker setup](docs/docker.md)
for details.
