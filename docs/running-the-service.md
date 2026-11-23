# Local development

From the repository root, create and activate a virtual environment, then install
the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Add your Hugging Face token to a root-level `.env` file:

```env
HF_TOKEN=your_huggingface_token
```

Start the application:

```bash
uvicorn app.main:app --reload --port 8082
```

The interface is available at `http://localhost:8082`, API docs at
`http://localhost:8082/docs`, and health check at `http://localhost:8082/health`.
Set `HF_MODEL` or `PORT` in `.env` to override their defaults.

To try the API directly:

```bash
curl http://localhost:8082/api/v1/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"Photosynthesis","number_of_questions":3}'
```
