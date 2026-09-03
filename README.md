# SABIFY AI Service

The SABIFY AI Service is a Python-based AI microservice responsible for providing artificial intelligence capabilities to the SABIFY Learning Management System (LMS).

The service is currently focused on **AI-powered multiple-choice quiz generation**. It is designed as a separate service so that AI functionality can evolve independently from the main Go LMS application.

---

# Table of Contents

* [Overview](#overview)
* [Architecture](#architecture)
* [Technology Stack](#technology-stack)
* [Project Structure](#project-structure)
* [Configuration](#configuration)
* [Running the Service](#running-the-service)
* [API Endpoint](#api-endpoint)
* [Quiz Generation](#quiz-generation)

  * [Request Fields](#request-fields)
  * [Response Fields](#response-fields)
  * [Request Example](#request-example)
  * [Response Example](#response-example)
* [How Quiz Generation Works](#how-quiz-generation-works)
* [Topic-Based Generation](#topic-based-generation)
* [Material-Based Generation](#material-based-generation)
* [Correct Answer Handling](#correct-answer-handling)
* [Input and Output Contract](#input-and-output-contract)
* [Validation](#validation)
* [Error Handling](#error-handling)
* [Known Problems and Solutions](#known-problems-and-solutions)
* [Testing](#testing)
* [Integration With the Go LMS](#integration-with-the-go-lms)
* [Current Limitations](#current-limitations)
* [Future Improvements](#future-improvements)

---

# Overview

SABIFY uses a separate Python AI service to handle AI-related operations.

The main SABIFY LMS is built with Go, while AI functionality is implemented in Python.

The current architecture is:

```text
                    SABIFY LMS
                   Go Application
                        |
                        |
                        | HTTP POST
                        v
              +----------------------+
              |   Python AI Service  |
              |      FastAPI         |
              +----------------------+
                        |
                        v
              Hugging Face Router
                        |
                        v
              DeepSeek-V3-0324
                        |
                        v
              Generated Quiz JSON
                        |
                        v
              Python Validation
                        |
                        v
              Shuffle Answer Options
                        |
                        v
                  Go LMS
```

The AI service **does not directly save quizzes to the database**.

Instead:

```text
Teacher
   ↓
Generate with AI
   ↓
Go LMS
   ↓
Python AI Service
   ↓
Generated Questions
   ↓
Go LMS
   ↓
Teacher Reviews Questions
   ↓
Teacher Edits/Adds/Removes Questions
   ↓
Create Quiz
   ↓
PostgreSQL
```

This ensures that teachers remain in control of the final quiz.

---

# Architecture

SABIFY currently uses a service-oriented architecture for AI functionality.

## Main LMS

The main LMS is responsible for:

* Authentication
* Authorization
* Courses
* Course materials
* Quizzes
* Questions
* Student submissions
* Automatic grading
* Teacher dashboards
* Student dashboards
* Database operations

Technology:

```text
Go
Chi Router
PostgreSQL
Go Templates
```

## AI Service

The AI service is responsible for:

* AI quiz generation
* Prompt construction
* Communication with Hugging Face
* LLM response processing
* JSON extraction
* Response validation
* Answer-option randomization
* Returning structured quiz data to the LMS

Technology:

```text
Python
FastAPI
Pydantic
HTTPX
Hugging Face Router
DeepSeek-V3-0324
```

---

# Technology Stack

| Component       | Technology                     |
| --------------- | ------------------------------ |
| Language        | Python                         |
| API Framework   | FastAPI                        |
| Data Validation | Pydantic                       |
| HTTP Client     | HTTPX                          |
| AI Provider     | Hugging Face Router            |
| AI Model        | `deepseek-ai/DeepSeek-V3-0324` |
| API Format      | JSON                           |
| Main LMS        | Go                             |
| Database        | PostgreSQL                     |

---

# Project Structure

A simplified version of the AI service structure is:

```text
ai-service/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── quiz.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── services/
│   │   └── quiz_generator.py
│   │
│   └── main.py
│
├── .env
├── requirements.txt
└── README.md
```

---

# Configuration

The AI service requires a Hugging Face API token.

Example `.env`:

```env
HF_TOKEN=your_huggingface_token
```

The Go LMS also needs to know where the AI service is running.

Example Go `.env`:

```env
AI_SERVICE_URL=http://localhost:8082
```

The AI service and Go LMS are therefore connected through HTTP.

---

# Running the Service

Install dependencies:

```bash
pip install -r requirements.txt
```

Run FastAPI:

```bash
uvicorn app.main:app --reload --port 8082
```

The AI service will then be available at:

```text
http://localhost:8082
```

The quiz generation endpoint is:

```text
POST http://localhost:8082/api/v1/quiz/generate
```

---

# API Endpoint

## Generate Quiz

```http
POST /api/v1/quiz/generate
```

The endpoint generates multiple-choice questions based on either:

1. A topic
2. Uploaded course material

At least one of these must contain usable content.

---

# Quiz Generation

## Request Fields

The request follows this schema:

```python
class QuizGenerationRequest(BaseModel):
    course_id: Optional[str] = None
    material_id: Optional[str] = None
    material_text: Optional[str] = None
    topic: Optional[str] = None
    number_of_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="basic")
    question_type: str = Field(default="multiple_choice")
```

## Field Description

| Field                 | Type    | Required | Description                         |
| --------------------- | ------- | -------- | ----------------------------------- |
| `course_id`           | string  | No       | ID of the SABIFY course             |
| `material_id`         | string  | No       | ID of course material               |
| `material_text`       | string  | No       | Text extracted from course material |
| `topic`               | string  | No*      | Topic to generate questions about   |
| `number_of_questions` | integer | No       | Number of questions                 |
| `difficulty`          | string  | No       | Question difficulty                 |
| `question_type`       | string  | No       | Type of questions                   |

`topic` is required when `material_text` is not supplied.

---

# Request Example

A simple topic-based request:

```json
{
  "course_id": "e3cbe98b-3f17-4664-bc59-70129f037e09",
  "topic": "Biology",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

---

# Real SABIFY Request Example

The Go LMS currently sends the quiz title and description as the topic.

For example, the teacher entered:

```text
Quiz title:
digestive system

Description:
About digestive system
```

The Go application combines these into:

```text
digestive system: About digestive system
```

and sends the request to the AI service.

The browser payload was:

```json
{
  "course_id": "e3cbe98b-3f17-4664-bc59-70129f037e09",
  "title": "digestive system",
  "description": "About digestive system",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

The Go service converts this into the AI service request.

---

# Response Fields

The AI service returns:

```python
class GeneratedQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: str


class QuizGenerationResponse(BaseModel):
    questions: List[GeneratedQuestion]
```

Each question contains:

| Field            | Type    | Description                            |
| ---------------- | ------- | -------------------------------------- |
| `question`       | string  | The question                           |
| `options`        | array   | Exactly four answer options            |
| `correct_answer` | integer | Zero-based index of the correct option |
| `explanation`    | string  | Explanation of the correct answer      |

---

# Correct Answer Index

The `correct_answer` field uses a zero-based index.

```text
0 = Option A
1 = Option B
2 = Option C
3 = Option D
```

Example:

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

The correct answer is:

```text
Option A - Epidermis
```

---

# Real Response Example

One successful response from the AI service generated Biology questions about the skin:

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
    },
    {
      "question": "Which layer of the skin contains blood vessels and nerve endings?",
      "options": [
        "Epidermis",
        "Dermis",
        "Hypodermis",
        "Subcutaneous layer"
      ],
      "correct_answer": 1,
      "explanation": "The dermis is the middle layer of the skin, containing tough connective tissue, hair follicles, sweat glands, blood vessels, and nerve endings."
    },
    {
      "question": "What is the primary function of the hypodermis?",
      "options": [
        "Protection from UV radiation",
        "Temperature regulation",
        "Fat storage and insulation",
        "Sensation of touch"
      ],
      "correct_answer": 2,
      "explanation": "The hypodermis, also called the subcutaneous layer, is primarily responsible for fat storage and insulation, helping to regulate body temperature."
    },
    {
      "question": "Which of the following is NOT a function of the skin?",
      "options": [
        "Protection from pathogens",
        "Vitamin D synthesis",
        "Production of red blood cells",
        "Regulation of body temperature"
      ],
      "correct_answer": 2,
      "explanation": "While the skin performs many functions, red blood cells are produced in the bone marrow, not the skin."
    },
    {
      "question": "What gives skin its color?",
      "options": [
        "Keratin",
        "Melanin",
        "Collagen",
        "Elastin"
      ],
      "correct_answer": 1,
      "explanation": "Melanin is the pigment produced by melanocytes in the epidermis that gives skin its color and provides protection from UV radiation."
    }
  ]
}
```

---

# Another Real Response Example

The service was also tested with English/Literature content about figures of speech.

The model initially returned:

```json
{
  "questions": [
    {
      "question": "Which figure of speech involves the repetition of the same sound at the beginning of words in a sentence?",
      "options": [
        "Alliteration",
        "Metaphor",
        "Simile",
        "Hyperbole"
      ],
      "correct_answer": 0
    },
    {
      "question": "What figure of speech directly compares two unlike things using 'like' or 'as'?",
      "options": [
        "Simile",
        "Metaphor",
        "Personification",
        "Onomatopoeia"
      ],
      "correct_answer": 0
    },
    {
      "question": "Which figure of speech gives human characteristics to non-human objects or animals?",
      "options": [
        "Personification",
        "Alliteration",
        "Irony",
        "Oxymoron"
      ],
      "correct_answer": 0
    },
    {
      "question": "What figure of speech involves an exaggerated statement not meant to be taken literally?",
      "options": [
        "Hyperbole",
        "Metonymy",
        "Synecdoche",
        "Euphemism"
      ],
      "correct_answer": 0
    },
    {
      "question": "Which figure of speech involves a contradiction in terms, often for emphasis or humor?",
      "options": [
        "Oxymoron",
        "Paradox",
        "Allusion",
        "Apostrophe"
      ],
      "correct_answer": 0
    }
  ]
}
```

Although these questions were correct, every correct answer was placed at index `0`.

This created an undesirable pattern:

```text
Question 1 → A
Question 2 → A
Question 3 → A
Question 4 → A
Question 5 → A
```

The service therefore performs answer-option shuffling before returning the response.

---

# How Quiz Generation Works

The generation process is:

```text
1. Receive request
        ↓
2. Determine whether material or topic is provided
        ↓
3. Build context
        ↓
4. Build system prompt
        ↓
5. Build user prompt
        ↓
6. Send request to Hugging Face
        ↓
7. Receive LLM response
        ↓
8. Clean response
        ↓
9. Parse JSON
        ↓
10. Validate questions
        ↓
11. Shuffle answer options
        ↓
12. Update correct_answer
        ↓
13. Return QuizGenerationResponse
```

---

# Topic-Based Generation

When no course material is provided, the service uses the topic.

Example:

```json
{
  "topic": "Newton's Laws of Motion",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

The AI should generate questions specifically about Newton's Laws of Motion.

For example:

```text
Which law states that an object remains at rest or in uniform motion unless acted upon by an external force?
```

The AI must not generate unrelated questions about programming, databases, or other subjects.

---

# Material-Based Generation

The service also supports generating questions from uploaded material.

When `material_text` is supplied:

```json
{
  "material_text": "Photosynthesis is the process by which green plants convert light energy into chemical energy...",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

The service uses:

```text
Material Text:
"""
Photosynthesis is the process by which green plants...
"""
```

as the context for the AI.

Material-based generation is intended to allow questions to be generated from actual course content.

---

# Topic Priority

The service currently uses the following logic:

```python
if request.material_text and request.material_text.strip():
    context_prompt = f"Material Text:\n\"\"\"\n{request.material_text}\n\"\"\""
else:
    context_prompt = f"Topic: {request.topic}"
```

Therefore:

```text
material_text exists
        ↓
use material_text
```

Otherwise:

```text
topic
 ↓
use topic
```

---

# Topic Relevance

The system prompt explicitly instructs the model to stay within the requested subject.

Important requirements include:

```text
Every question MUST be directly related to the provided topic.

Every answer option MUST be relevant to that question and topic.

Every explanation MUST explain the answer using knowledge relevant to that topic.

Never substitute your own topic for the user's topic.

Never introduce an unrelated subject.
```

For example:

```text
Topic: Biology
```

must produce Biology questions.

It should not produce:

```text
Programming
Databases
Software Engineering
Computer Networks
```

unless those subjects are explicitly requested.

---

# Correct Answer Handling

The LLM provides the initial correct answer index.

For example:

```json
{
  "options": [
    "Alliteration",
    "Metaphor",
    "Simile",
    "Hyperbole"
  ],
  "correct_answer": 0
}
```

The Python service then shuffles the options.

Before:

```text
A → Alliteration ← Correct
B → Metaphor
C → Simile
D → Hyperbole
```

After shuffling:

```text
A → Simile
B → Hyperbole
C → Alliteration ← Correct
D → Metaphor
```

The service updates:

```json
"correct_answer": 2
```

The correct answer therefore remains correct even though its position changes.

This is important because the AI may repeatedly place the correct answer at position `0`.

---

# Option Shuffling Implementation

The service uses:

```python
@staticmethod
def _shuffle_question_options(question: dict) -> None:
    """
    Shuffle the answer options while keeping correct_answer
    pointing to the correct option.
    """
    options = question["options"]
    correct_index = question["correct_answer"]

    correct_option = options[correct_index]

    random.shuffle(options)

    question["correct_answer"] = options.index(correct_option)
```

This ensures that:

```text
Correct option before shuffle
        ↓
Option is saved
        ↓
Options are shuffled
        ↓
Correct option is located again
        ↓
correct_answer is updated
```

---

# Validation

The service validates the LLM output before returning it.

## Question Count

The number of returned questions must equal the requested number.

For example:

```text
Requested: 5
Returned: 5
```

is valid.

But:

```text
Requested: 5
Returned: 4
```

causes an error.

---

# Four Options

Every question must contain exactly four options.

Valid:

```json
"options": [
  "A",
  "B",
  "C",
  "D"
]
```

Invalid:

```json
"options": [
  "A",
  "B"
]
```

Invalid:

```json
"options": [
  "A",
  "B",
  "C",
  "D",
  "E"
]
```

---

# Placeholder Detection

The service rejects placeholder answers such as:

```text
Option 0
Option 1
Option 2
Option 3
string
```

This protects the LMS from receiving unusable generated questions.

---

# Explanation Validation

Each question must contain a meaningful explanation.

The service rejects:

```text
"explanation": "string"
```

because this is usually an LLM/schema placeholder rather than an educational explanation.

---

# JSON Cleaning

LLMs can sometimes return JSON surrounded by additional content.

The service contains:

```python
_clean_llm_json()
```

which handles:

* DeepSeek reasoning tokens
* Markdown code fences
* Extra text surrounding JSON
* Extracting the outer JSON object

For example, if the model returns:

````text
```json
{
  "questions": [...]
}
````

````

the service extracts:

```json
{
  "questions": [...]
}
````

before parsing it.

---

# Error Handling

The service uses FastAPI `HTTPException` for expected API errors.

General errors are converted into HTTP 500 responses.

Possible errors include:

```text
400 Bad Request
500 Internal Server Error
503 Service Unavailable
```

---

# Common Errors

## Missing Topic or Material

If both are empty:

```json
{
  "topic": "",
  "material_text": ""
}
```

the endpoint returns:

```text
400 Bad Request
```

with:

```text
Either 'material_text' or 'topic' must be provided.
```

---

# Incorrect Number of Questions

If the application requests:

```json
{
  "number_of_questions": 5
}
```

but the AI returns four questions, the service rejects the response.

Error:

```text
AI returned an incorrect number of questions.
```

---

# Incorrect Number of Options

If an AI response contains fewer or more than four options:

```text
AI returned a question without exactly four options.
```

the response is rejected.

---

# Placeholder Options

If the AI returns:

```json
{
  "options": [
    "Option 0",
    "Option 1",
    "Option 2",
    "Option 3"
  ]
}
```

the service rejects it.

Error:

```text
AI returned placeholder answer options.
```

---

# Hugging Face Errors

If the Hugging Face API does not return HTTP 200, the service raises an HTTP error containing the Hugging Face response.

This helps identify provider-side problems such as:

* Invalid API token
* Rate limits
* Model availability
* Provider errors
* Network failures

---

# JSON Parsing Errors

If the LLM returns invalid JSON, the service raises:

```text
Failed to parse LLM JSON output
```

The raw LLM response is included in the server-side error for debugging.

---

# Known Problems and Solutions

## Problem 1: Browser `Failed to fetch`

### Symptom

The browser showed:

```text
TypeError: Failed to fetch
```

and Firefox showed:

```text
TypeError: NetworkError
```

The Go server, however, showed that the request successfully generated a response.

Example:

```text
POST /teacher/quizzes/generate HTTP/1.1 200
```

with a response time of approximately:

```text
23.994483026s
```

### Cause

The Go HTTP server originally had:

```go
WriteTimeout: 10 * time.Second,
```

while AI generation could take approximately 24 seconds.

Therefore:

```text
AI generation
≈ 24 seconds

Go WriteTimeout
= 10 seconds
```

The server's write timeout was too short for the AI operation.

### Solution

The timeout was increased to:

```go
WriteTimeout: 60 * time.Second,
```

The Go server must be restarted after changing this value.

The final configuration is:

```go
srv := &http.Server{
    Addr:         cfg.addr,
    Handler:      app.routes(),
    IdleTimeout:  time.Minute,
    ReadTimeout:  5 * time.Second,
    WriteTimeout: 60 * time.Second,
}
```

---

# Problem 2: Curl Redirected to `/login`

### Symptom

A direct curl request returned:

```text
HTTP/1.1 303 See Other
Location: /login
```

### Cause

The Go LMS protects the quiz generation endpoint with authentication.

The curl request did not contain the authenticated SABIFY session cookie.

Therefore the LMS correctly redirected the request to:

```text
/login
```

### Important

This does **not** indicate that the AI service is broken.

The browser request works because the teacher is already authenticated in SABIFY.

---

# Problem 3: Correct Answer Always Appeared as Option A

### Symptom

The AI generated questions such as:

```text
Question 1 → A
Question 2 → A
Question 3 → A
Question 4 → A
Question 5 → A
```

The questions themselves were correct, but the quiz became predictable.

### Cause

The LLM frequently placed the correct answer at index `0`.

### Solution

Python now randomly shuffles the four options and updates `correct_answer`.

This makes the final quiz less predictable.

---

# Problem 4: AI Generated Questions About the Wrong Subject

### Symptom

A Biology request could occasionally result in unrelated questions such as programming questions.

### Cause

LLMs are probabilistic and can sometimes drift from the requested subject if the prompt does not enforce topic relevance strongly enough.

### Solution

The system prompt was strengthened with explicit topic-relevance rules.

The model is instructed:

```text
The target topic is the ONLY subject you are allowed to generate questions about.

Do not change the subject.

Do not introduce another subject.

Do not generate generic questions.

Do not generate programming questions unless programming is the target topic.
```

Topic adherence is therefore explicitly enforced at the prompt level.

---

# Testing

## Test the AI Service Directly

The service can be tested independently of the Go LMS.

Example:

```bash
curl -X POST http://localhost:8082/api/v1/quiz/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_HF_TOKEN" \
  -d '{
    "topic": "Biology",
    "number_of_questions": 5,
    "difficulty": "basic",
    "question_type": "multiple_choice"
  }'
```

The service should return:

```json
{
  "questions": [...]
}
```

with exactly five questions.

---

# Testing With the Go LMS

The normal production-like flow is:

```text
1. Start PostgreSQL
2. Start Python AI service
3. Start Go LMS
4. Login as teacher
5. Open Create Quiz
6. Select course
7. Enter quiz title
8. Enter description
9. Click Generate Quiz with AI
10. Review generated questions
11. Edit questions if necessary
12. Add/remove questions if necessary
13. Click Create Quiz
```

---

# Expected Frontend Behavior

When generation succeeds:

```text
Generate with AI
        ↓
Generating...
        ↓
AI response received
        ↓
Question builder populated
        ↓
AI Generated badge displayed
```

The teacher should then be able to modify the generated questions before saving.

---

# Integration With the Go LMS

The Go LMS calls:

```text
POST /api/v1/quiz/generate
```

on the Python service.

The Go client sends:

```json
{
  "course_id": "...",
  "topic": "...",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

The Python service returns:

```json
{
  "questions": [
    {
      "question": "...",
      "options": [
        "...",
        "...",
        "...",
        "..."
      ],
      "correct_answer": 1,
      "explanation": "..."
    }
  ]
}
```

The Go LMS converts the response into the existing quiz-question builder.

---

# Important Security Design

The Python service does not decide whether a teacher owns a course.

The Go LMS performs this validation before calling the AI service.

The Go application verifies:

```text
Current user
      ↓
Authenticated?
      ↓
Teacher?
      ↓
Course exists?
      ↓
Course belongs to teacher?
      ↓
Call AI service
```

This prevents a teacher from using the endpoint to generate content for another teacher's course.

---

# Database Responsibility

The AI service does **not** directly access the SABIFY PostgreSQL database.

It only generates content.

The database flow is:

```text
AI Service
    ↓
Generated JSON
    ↓
Go LMS
    ↓
Teacher Review
    ↓
Existing Create Quiz Handler
    ↓
PostgreSQL
```

This separation keeps the AI service independent from the LMS database layer.

---

# Current API Contract

## Request

```json
{
  "course_id": "string",
  "material_id": "string",
  "material_text": "string",
  "topic": "string",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

All fields except `number_of_questions`, `difficulty`, and `question_type` are optional at the API schema level.

However, either:

```text
material_text
```

or:

```text
topic
```

must contain usable content.

---

# Response

```json
{
  "questions": [
    {
      "question": "string",
      "options": [
        "string",
        "string",
        "string",
        "string"
      ],
      "correct_answer": 0,
      "explanation": "string"
    }
  ]
}
```

The actual service enforces:

```text
questions = requested number
options = exactly 4
correct_answer = 0-3
explanation = meaningful
```

---

# Example: Biology

Request:

```json
{
  "topic": "Biology - Human Digestive System",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

Expected content:

```text
What is the primary function of the small intestine?

A. Absorb nutrients
B. Store bile
C. Produce red blood cells
D. Pump blood
```

The service should not generate:

```text
What is a variable in Python?
```

because that is unrelated to the requested topic.

---

# Example: Physics

Request:

```json
{
  "topic": "Newton's Laws of Motion",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

Expected content should focus on:

* Newton's First Law
* Newton's Second Law
* Newton's Third Law
* Force
* Mass
* Acceleration
* Inertia

---

# Example: English

Request:

```json
{
  "topic": "Figures of Speech",
  "number_of_questions": 5,
  "difficulty": "basic",
  "question_type": "multiple_choice"
}
```

Questions may cover:

* Simile
* Metaphor
* Alliteration
* Hyperbole
* Personification
* Oxymoron
* Onomatopoeia

---

# Performance

AI generation is currently performed synchronously.

A typical request can take several seconds because the Go application must:

```text
Browser
 ↓
Go
 ↓
Python
 ↓
Hugging Face
 ↓
DeepSeek
 ↓
Python
 ↓
Go
 ↓
Browser
```

AI generation has previously taken approximately 24 seconds for a five-question request.

The Go server therefore uses:

```go
WriteTimeout: 60 * time.Second
```

The Python HTTP client also uses:

```python
httpx.Client(timeout=60.0)
```

---

# Current Limitations

The current MVP does not yet automatically:

* Read all course materials
* Retrieve relevant sections from PDFs
* Perform RAG
* Use previous examination questions
* Automatically determine the teacher's preferred question distribution
* Automatically detect every possible hallucination
* Automatically fact-check every generated question
* Save generated quizzes directly to the database
* Generate all possible question types

The teacher remains responsible for reviewing AI-generated questions before publishing.

---

# Future Improvements

Possible future improvements include:

## Course Material Integration

Instead of only using the quiz title and description:

```text
Course
 ↓
Course Materials
 ↓
Relevant Material
 ↓
AI Quiz Generation
```

---

## RAG

A future version can use:

```text
Course Materials
      ↓
Chunking
      ↓
Embeddings
      ↓
Vector Database
      ↓
Relevant Context
      ↓
LLM
      ↓
Quiz
```

Possible vector databases include:

```text
pgvector
Qdrant
FAISS
```

---

## Question Difficulty

Support:

```text
Basic
Intermediate
Advanced
```

or:

```text
Easy
Medium
Hard
```

---

## Question Types

Future versions can support:

```text
Multiple Choice
True / False
Short Answer
Fill in the Blank
Essay
Matching
```

---

## AI Teacher Assistant

The same AI service can eventually support:

```text
Teacher
 ↓
AI Teacher Assistant
 ↓
Lesson planning
Question generation
Explanations
Student performance analysis
Teaching recommendations
```

---

## AI Learning Coach

Students could interact with:

```text
Student
 ↓
AI Learning Coach
 ↓
Study recommendations
Weak-topic detection
Personalized explanations
Revision plans
```

---

## AI Analytics

Future AI analytics could use:

```text
Quiz Results
Course Activity
Submission History
Learning Progress
        ↓
      AI/ML
        ↓
Learning Insights
        ↓
Teacher Dashboard
```

---

# Design Principle

The SABIFY AI service follows an important principle:

> **AI generates; the teacher decides.**

The AI is an assistant rather than the final authority.

The workflow is intentionally:

```text
AI Generation
      ↓
Validation
      ↓
Teacher Review
      ↓
Teacher Editing
      ↓
Publication
```

This makes the system safer and more useful for real educational environments.

---

# Summary

The SABIFY AI Service provides an independent AI layer for the SABIFY LMS.

Current functionality:

```text
✓ FastAPI API
✓ Hugging Face integration
✓ DeepSeek-V3-0324
✓ Topic-based quiz generation
✓ Material-based quiz generation
✓ Structured JSON responses
✓ Four-option MCQs
✓ Correct-answer indexing
✓ Response validation
✓ Placeholder detection
✓ JSON cleaning
✓ Answer-option shuffling
✓ Go LMS integration
✓ Teacher review workflow
```

Current primary endpoint:

```text
POST /api/v1/quiz/generate
```

The service is designed to expand beyond quiz generation into a broader AI education platform supporting intelligent teaching, learning, analytics, personalization, and educational assistance.
