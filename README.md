# DebateMate 🗣️🤖

DebateMate is an AI-powered platform for **structured argumentation**, **pitch testing**, **critical feedback**, **expected objections**.

Our vision is to create a tool where students, founders, and professionals can stress-test their reasoning against a powerful AI partner.

In the future, DebateMate could grow into a pitch simulator for **startups**, **sales reps**, and a critical-thinking assistant for **anyone** who wants to refine their arguments before stepping into the real world.

At its core, DebateMate uses GPT-5, which can write complex, nuanced texts, analyze reasoning, and surface weaknesses that humans might overlook. This makes debates not just automatic, but genuinely intelligent.

## 🌟 What It Does

The app has two main modes:

### Debate Counterattacks

User posts an argument.

The model summarizes it under the FOR column.

User can choose to:

- Evaluate Argument → critique the logic, detect fallacies.

- Give Objections → generate counterarguments.

- Find Sources → fetch neutral references (Wiki for now)

### Pitch Objections

User posts a startup pitch idea.

The model can:

- Object → raise possible concerns.

- Give Ruthless Impression → critique the pitch as an investor.

- Research → fetch neutral references to test the idea.

The pitch is re-evaluated with a score, showing how convincing it remains after objections.

## 🧠 Why GPT-5?

We believe debates and arguments should be intelligent, nuanced, and constructive.
GPT-5 is not just a chatbot — it can write complex, structured texts, analyze reasoning, and surface hidden weaknesses in arguments.

By leveraging its advanced reasoning, we can:

Turn casual opinions into professional debates.

Stress-test startup ideas with ruthless investor-style objections.

Help users improve critical thinking and sharpen persuasion skills.

## ⚙️ How to Run

Clone the repository:

```
git clone https://github.com/TapkiGroup/debate-coach.git
cd debate-coach
```

Copy .env.example to .env and fill in API keys:

```
cp .env.example .env
```

Build and run with Docker Compose:

```
docker compose up -d --build
```

Access the app at:

👉 http://localhost:8080

## 🛠️ Tech Stack

Backend: FastAPI (Python)

Frontend: Next.js (React)

Gateway: Nginx

Containerization: Docker Compose

## 💡 Vision

Debate Coach is just a beginning.
We want to explore AI-assisted debates, objection handling, and critical feedback systems.
Imagine classrooms, hackathons, or boardrooms where AI challenges ideas — sharpening them instead of replacing them.

GPT-5 makes it possible.
Now let’s start generating smart debates together. 🧠🔥
