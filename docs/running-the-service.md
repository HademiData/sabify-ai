# Running the SABIFY AI Service

This document explains how to set up, configure, run, test, and troubleshoot the SABIFY AI Service locally.

The AI service is a Python/FastAPI microservice that provides AI functionality to the SABIFY Go LMS.

---

# Prerequisites

Before running the service, make sure the following are installed:

* Python 3.10+
* pip
* Git
* Internet connection
* A Hugging Face API token

Verify Python:

```bash
python3 --version
```

Verify pip:

```bash
pip3 --version
```

---

# Project Location

Navigate to the AI service directory:

```bash
cd path/to/sabify/ai-service
```

The service should contain a structure similar to:

```text
ai-service/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── main.py
├── docs/
│   └── running-the-service.md
├── .env
├── requirements.txt
└── README.md
```

---

# 1. Create a Virtual Environment

It is recommended to run the AI service inside a Python virtual environment.

Create one:

```bash
python3 -m venv .venv
```

Activate it:

### Linux/macOS

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

After activation, the terminal should show something similar to:

```text
(.venv) user@computer:~/sabify/ai-service$
```

---

# 2. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

If dependencies need to be updated:

```bash
pip install --upgrade -r requirements.txt
```

---

# 3. Configure Environment Variables

Create a `.env` file in the root of the AI service:

```text
ai-service/
├── .env
├── app/
└── requirements.txt
```

Add the Hugging Face API token:

```env
HF_TOKEN=your_huggingface_token
```

The token is required because the service communicates with the Hugging Face Router.

### Important

Never commit the `.env` file to Git.

Make sure `.gitignore` contains:

```gitignore
.env
.venv/
__pycache__/
```

---

# 4. Start the AI Service

The SABIFY Go LMS currently expects the AI service to run on port `8082`.

Start FastAPI with:

```bash
uvicorn app.main:app --reload --port 8082
```

Expected output should look similar to:

```text
INFO:     Will watch for changes in these directories: [...]
INFO:     Uvicorn running on http://127.0.0.1:8082
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

The AI service is now running at:

```text
http://localhost:8082
```

---

# 5. Verify the Service Is Running

Open the FastAPI documentation in your browser:

```text
http://localhost:8082/docs
```

FastAPI provides an interactive Swagger UI.

You should see the available API endpoints, including:

```text
POST /api/v1/quiz/generate
```

You can use this page to manually test the API.

---

# 6. Test Quiz Generation

The main endpoint is:

```text
POST /api/v1/quiz/generate
```

A basic request is:

```json
{
  "topic": "Biology",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

Using `curl`:

```bash
curl -X POST http://localhost:8082/api/v1/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Biology",
    "number_of_questions": 5,
    "difficulty": "basic",
    "question_type": "multiple_choice"
  }'
```

---

# 7. Expected Response

A successful response has this structure:

```json
{
  "questions": [
    {
      "question": "What is the outermost layer of the skin called?",
      "options": [
        "Epidermis",
        "Dermis",
        "Hypodermis",
        "Stratum corneum"
      ],
      "correct_answer": 0,
      "explanation": "The epidermis is the outermost layer of the skin, providing a waterproof barrier and creating our skin tone."
    }
  ]
}
```

When five questions are requested, the response should contain exactly five questions.

---

# 8. Understanding `correct_answer`

The `correct_answer` field uses a zero-based index:

```text
0 → Option A
1 → Option B
2 → Option C
3 → Option D
```

For example:

```json
{
  "options": [
    "Epidermis",
    "Dermis",
    "Hypodermis",
    "Stratum corneum"
  ],
  "correct_answer": 0
}
```

means:

```text
Correct answer → Epidermis
```

The Python service subsequently shuffles the answer options so that the correct answer is not always in the same position.

---

# 9. Test Different Subjects

It is recommended to test multiple subjects to verify that the model follows the requested topic.

## Biology

```json
{
  "topic": "Human Digestive System",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

## Physics

```json
{
  "topic": "Newton's Laws of Motion",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

## English

```json
{
  "topic": "Figures of Speech",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

The questions should remain strictly relevant to the requested subject.

---

# 10. Test With Course Material

The service also supports generating questions from provided material.

Example:

```json
{
  "material_text": "Photosynthesis is the process by which green plants convert light energy into chemical energy...",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

When `material_text` is provided, it is used as the primary context for question generation.

---

# 11. Start the Go LMS

The AI service must be running before the Go LMS attempts to generate a quiz.

The Go LMS uses:

```env
AI_SERVICE_URL=http://localhost:8082
```

Therefore, the local architecture is:

```text
Browser
   |
   v
Go LMS
localhost:8080
   |
   | HTTP
   v
Python AI Service
localhost:8082
   |
   v
Hugging Face Router
   |
   v
DeepSeek-V3-0324
```

---

# 12. Run Both Services

For local development, two terminals can be used.

## Terminal 1 — AI Service

```bash
cd ai-service
source .venv/bin/activate
uvicorn app.main:app --reload --port 8082
```

## Terminal 2 — Go LMS

Navigate to the SABIFY Go project and start the LMS using the project's normal development command.

The Go application's `.env` must contain:

```env
AI_SERVICE_URL=http://localhost:8082
```

Both services must be running.

---

# 13. Test Through SABIFY

Once both services are running:

1. Open SABIFY in the browser.
2. Log in as a teacher.
3. Open **Create Quiz**.
4. Select a course.
5. Enter a quiz title.
6. Enter a description.
7. Click **Generate Quiz with AI**.
8. Wait for generation to complete.
9. Review the generated questions.
10. Edit questions if necessary.
11. Add or remove questions if necessary.
12. Click **Create Quiz**.

The AI service only generates the questions.

The Go LMS remains responsible for saving the final quiz to PostgreSQL.

---

# 14. AI Generation Flow

The complete local flow is:

```text
Teacher
   |
   | Generate Quiz
   v
Browser
   |
   | POST /teacher/quizzes/generate
   v
Go LMS
   |
   | Validate authenticated teacher
   | Validate course ownership
   |
   | POST /api/v1/quiz/generate
   v
Python AI Service
   |
   | Build prompt
   v
Hugging Face Router
   |
   v
DeepSeek-V3-0324
   |
   | Generated JSON
   v
Python AI Service
   |
   | Clean JSON
   | Validate response
   | Shuffle options
   |
   v
Go LMS
   |
   v
Browser
   |
   | Teacher reviews
   v
Create Quiz
   |
   v
PostgreSQL
```

---

# 15. Common Problems

## Problem: `HF_TOKEN` is missing

### Error

The service may fail when attempting to communicate with Hugging Face.

### Solution

Check `.env`:

```env
HF_TOKEN=your_huggingface_token
```

Then restart the FastAPI service.

---

# Problem: AI Service Is Not Running

### Symptom

The Go LMS reports that it cannot connect to the AI service.

### Check

Verify that port `8082` is running:

```bash
curl http://localhost:8082/docs
```

If the service is running, the request should return the FastAPI documentation page.

---

# Problem: Wrong Port

The Go LMS currently expects:

```env
AI_SERVICE_URL=http://localhost:8082
```

If FastAPI is running on another port, update the Go LMS configuration accordingly.

For example:

```env
AI_SERVICE_URL=http://localhost:9000
```

if FastAPI is running on:

```bash
uvicorn app.main:app --reload --port 9000
```

Both values must match.

---

# Problem: `Failed to fetch` in the Browser

The SABIFY AI generation request can take several seconds because the request passes through:

```text
Go
 ↓
Python
 ↓
Hugging Face
 ↓
LLM
 ↓
Python
 ↓
Go
 ↓
Browser
```

The Go server must therefore allow enough time for the AI request.

The Go LMS currently uses:

```go
WriteTimeout: 60 * time.Second,
```

The Python HTTP client also uses:

```python
httpx.Client(timeout=60.0)
```

If the Go server's `WriteTimeout` is too short, the browser can report:

```text
TypeError: Failed to fetch
```

even when the AI service successfully generated the response.

After changing the Go server timeout, **restart the Go server**.

---

# Problem: AI Generates Questions About the Wrong Subject

### Symptom

For example, a request for:

```text
Biology
```

may produce unrelated programming questions.

### Solution

The quiz generator prompt contains explicit topic-relevance instructions.

The model is instructed to:

* Follow the provided topic.
* Avoid unrelated subjects.
* Generate questions directly related to the requested topic.
* Avoid substituting another subject.

If this problem occurs again, inspect:

```text
app/services/quiz_generator.py
```

particularly the:

```python
system_prompt
```

and:

```python
user_prompt
```

---

# Problem: All Correct Answers Are Option A

### Symptom

The AI may initially return:

```text
Question 1 → A
Question 2 → A
Question 3 → A
Question 4 → A
Question 5 → A
```

### Solution

The AI service shuffles answer options after generation.

The correct answer index is updated after shuffling.

Therefore, the final response can contain:

```text
Question 1 → C
Question 2 → A
Question 3 → D
Question 4 → B
Question 5 → C
```

while keeping every correct answer accurate.

---

# Problem: Incorrect Number of Questions

If five questions are requested:

```json
{
  "number_of_questions": 5
}
```

the AI service requires exactly five questions.

If the model returns fewer or more, the service rejects the response.

Error:

```text
AI returned an incorrect number of questions.
```

---

# Problem: Placeholder Options

The service rejects placeholder answers such as:

```text
Option 0
Option 1
Option 2
Option 3
```

and:

```text
string
```

If these are returned by the model, the AI service rejects the response instead of sending unusable questions to the LMS.

---

# Problem: Invalid JSON From the Model

The LLM is instructed to return JSON only.

However, LLMs can sometimes return additional text or markdown.

The service contains JSON-cleaning logic that handles:

* Markdown code fences
* DeepSeek reasoning tokens
* Extra text around JSON
* Extraction of the outer JSON object

If JSON parsing still fails, check the FastAPI terminal logs.

---

# 16. Useful Development Commands

## Activate virtual environment

```bash
source .venv/bin/activate
```

## Start development server

```bash
uvicorn app.main:app --reload --port 8082
```

## Stop server

```text
Ctrl+C
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Check installed packages

```bash
pip list
```

## Test FastAPI

```bash
curl http://localhost:8082/docs
```

## Test quiz endpoint

```bash
curl -X POST http://localhost:8082/api/v1/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Newton'\''s Laws of Motion",
    "number_of_questions": 5,
    "difficulty": "basic",
    "question_type": "multiple_choice"
  }'
```

---

# 17. Development Checklist

Before testing AI quiz generation, verify:

```text
[ ] Python virtual environment is activated
[ ] Dependencies are installed
[ ] .env exists
[ ] HF_TOKEN is configured
[ ] FastAPI is running on port 8082
[ ] http://localhost:8082/docs opens
[ ] Go LMS is running
[ ] AI_SERVICE_URL points to port 8082
[ ] User is logged in as a teacher
[ ] Teacher owns the selected course
```

---

# 18. Production Considerations

The commands in this document are intended primarily for local development.

For production:

* Do not use `--reload`.
* Store secrets securely.
* Do not commit `.env`.
* Use HTTPS.
* Configure appropriate timeouts.
* Add authentication between the LMS and AI service if required.
* Add logging and monitoring.
* Consider rate limiting.
* Consider request quotas.
* Consider asynchronous/background processing for long AI requests.
* Use a production ASGI server configuration.

For example, development uses:

```bash
uvicorn app.main:app --reload --port 8082
```

Production should use an appropriate deployment configuration rather than development reload mode.

---

# Summary

To run the SABIFY AI Service locally:

```bash
cd ai-service
```

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure:

```env
HF_TOKEN=your_huggingface_token
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --port 8082
```

Verify:

```text
http://localhost:8082/docs
```

Then start the Go LMS with:

```env
AI_SERVICE_URL=http://localhost:8082
```

The AI quiz generation system is now ready to use through SABIFY.
