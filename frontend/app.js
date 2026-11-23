const form = document.querySelector("#quiz-form");
const topicInput = document.querySelector("#topic");
const materialInput = document.querySelector("#material");
const countInput = document.querySelector("#question-count");
const difficultyInput = document.querySelector("#difficulty");
const errorMessage = document.querySelector("#form-error");
const generateButton = document.querySelector("#generate-button");
const emptyState = document.querySelector("#empty-state");
const loadingState = document.querySelector("#loading-state");
const quizResults = document.querySelector("#quiz-results");
const materialCount = document.querySelector("#char-count");

let selectedSource = "topic";

document.querySelectorAll(".source-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    selectedSource = tab.dataset.source;
    document.querySelectorAll(".source-tab").forEach((item) => {
      const selected = item === tab;
      item.classList.toggle("selected", selected);
      item.setAttribute("aria-selected", String(selected));
    });
    document.querySelectorAll(".source-panel").forEach((panel) => {
      panel.hidden = panel.dataset.panel !== selectedSource;
    });
    clearError();
  });
});

document.querySelectorAll(".stepper button").forEach((button) => {
  button.addEventListener("click", () => {
    const next = Number(countInput.value) + Number(button.dataset.step);
    countInput.value = String(Math.max(1, Math.min(20, next || 1)));
  });
});

countInput.addEventListener("change", () => {
  const count = Number(countInput.value);
  countInput.value = String(Math.max(1, Math.min(20, Number.isFinite(count) ? count : 5)));
});

materialInput.addEventListener("input", () => {
  materialCount.textContent = `${materialInput.value.length.toLocaleString()} / 20,000`;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const source = selectedSource === "topic" ? topicInput.value.trim() : materialInput.value.trim();
  if (!source) {
    showError(selectedSource === "topic" ? "Enter a topic to get started." : "Paste some study material to get started.");
    (selectedSource === "topic" ? topicInput : materialInput).focus();
    return;
  }
  const questionCount = Number(countInput.value);
  if (!Number.isInteger(questionCount) || questionCount < 1 || questionCount > 20) {
    showError("Choose between 1 and 20 questions.");
    countInput.focus();
    return;
  }

  const payload = {
    number_of_questions: questionCount,
    difficulty: difficultyInput.value,
    question_type: "multiple_choice",
    ...(selectedSource === "topic" ? { topic: source } : { material_text: source }),
  };
  setLoading(true);
  try {
    const response = await fetch("/api/v1/quiz/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(typeof data.detail === "string" ? data.detail : "Quiz generation failed. Please try again.");
    }
    if (!Array.isArray(data.questions) || data.questions.length === 0) {
      throw new Error("The service returned an empty quiz. Please try again.");
    }
    renderQuestions(data.questions, selectedSource === "topic" ? source : "Your study material");
    emptyState.hidden = true;
    quizResults.hidden = false;
  } catch (error) {
    showError(error instanceof TypeError
      ? "Could not connect to the quiz service. Check that the app is running and try again."
      : error.message);
  } finally {
    setLoading(false);
  }
});

function renderQuestions(questions, title) {
  quizResults.replaceChildren();
  const heading = document.createElement("div");
  heading.className = "results-heading";
  const titleBlock = document.createElement("div");
  const headingTitle = document.createElement("h2");
  headingTitle.textContent = title;
  const subtitle = document.createElement("p");
  subtitle.textContent = `${questions.length} multiple-choice questions`;
  titleBlock.append(headingTitle, subtitle);

  const actions = document.createElement("div");
  actions.className = "results-actions";
  const revealAll = document.createElement("button");
  revealAll.type = "button";
  revealAll.textContent = "Show answers";
  revealAll.addEventListener("click", () => quizResults.querySelectorAll(".question-card").forEach(showAnswer));
  const hideAll = document.createElement("button");
  hideAll.type = "button";
  hideAll.textContent = "Hide answers";
  hideAll.addEventListener("click", () => quizResults.querySelectorAll(".question-card").forEach(hideAnswer));
  actions.append(revealAll, hideAll);
  heading.append(titleBlock, actions);
  quizResults.append(heading);

  questions.forEach((question, index) => {
    const card = document.createElement("article");
    card.className = "question-card";
    const meta = document.createElement("div");
    meta.className = "question-meta";
    const number = document.createElement("span");
    number.textContent = `QUESTION ${String(index + 1).padStart(2, "0")}`;
    const level = document.createElement("span");
    level.className = "question-level";
    level.textContent = difficultyInput.options[difficultyInput.selectedIndex].text;
    meta.append(number, level);

    const prompt = document.createElement("h3");
    prompt.textContent = question.question;
    const options = document.createElement("div");
    options.className = "options-list";
    options.setAttribute("role", "list");
    question.options.forEach((option, optionIndex) => {
      const optionItem = document.createElement("div");
      optionItem.className = "answer-option";
      optionItem.dataset.correct = String(optionIndex === question.correct_answer);
      optionItem.setAttribute("role", "listitem");
      const letter = document.createElement("span");
      letter.className = "option-letter";
      letter.textContent = String.fromCharCode(65 + optionIndex);
      const text = document.createElement("span");
      text.textContent = option;
      optionItem.append(letter, text);
      options.append(optionItem);
    });

    const reveal = document.createElement("button");
    reveal.type = "button";
    reveal.className = "reveal-button";
    reveal.textContent = "Reveal answer";
    reveal.addEventListener("click", () => showAnswer(card));
    const explanation = document.createElement("div");
    explanation.className = "explanation";
    explanation.hidden = true;
    const explanationLabel = document.createElement("strong");
    explanationLabel.textContent = "Why: ";
    explanation.append(explanationLabel, document.createTextNode(question.explanation));
    card.append(meta, prompt, options, reveal, explanation);
    quizResults.append(card);
  });
}

function showAnswer(card) {
  card.querySelectorAll(".answer-option").forEach((option) => {
    if (option.dataset.correct === "true") option.classList.add("correct");
  });
  card.querySelector(".explanation").hidden = false;
  card.querySelector(".reveal-button").hidden = true;
}

function hideAnswer(card) {
  card.querySelectorAll(".answer-option").forEach((option) => option.classList.remove("correct"));
  card.querySelector(".explanation").hidden = true;
  card.querySelector(".reveal-button").hidden = false;
}

function setLoading(loading) {
  generateButton.disabled = loading;
  generateButton.querySelector(".button-label").textContent = loading ? "Generating your quiz…" : "Generate my quiz";
  loadingState.hidden = !loading;
  if (loading) {
    emptyState.hidden = true;
    quizResults.hidden = true;
  } else if (quizResults.childElementCount === 0) {
    emptyState.hidden = false;
  } else {
    quizResults.hidden = false;
  }
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}

function clearError() {
  errorMessage.textContent = "";
  errorMessage.hidden = true;
}
