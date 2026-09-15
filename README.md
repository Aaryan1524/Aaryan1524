<!-- HERO:START -->

<img src="assets/sphere.svg" width="100%" alt="Aaryan Gajula. I build the whole thing, interface to infrastructure. A rotating sphere of dots labelled with the tools I work in: Python, FastAPI, TypeScript, React, Next.js, Neo4j, PostgreSQL, Docker, Java, C# / .NET, spaCy, Claude API.">

<img src="assets/card.svg" width="100%" alt="A card cycling through three answers, one per audience. if you are hiring, &quot;Can you ship a feature end to end?&quot; — Yes. Interface, API, data, deploy. (Python, FastAPI, React, PostgreSQL, C# / .NET, Docker) if you are investing, &quot;What are you building?&quot; — Te Vārtā — news that finds you. (Te Vārtā, Knowledge graph, iOS app, tevarta.com) if you build things, &quot;What is under the hood?&quot; — A deterministic core, with the LLM at the edge. (Neo4j, RAG pipelines, spaCy, Claude API, Docker)">

<!-- HERO:END -->

Founder of Te Vārtā · CS at FIU '27 · SWE intern at CoOrdio Health, summer 2026.

### Flagships

<!-- FLAGSHIPS:START -->

<p align="center">
  <a href="https://www.tevarta.com"><img src="assets/flagship-te-varta.svg" width="49%" alt="Te Vārtā: News that finds you. core Neo4j knowledge graph, model LLM at the surface only, client iOS app."></a>
  <img src="assets/flagship-ember.svg" width="49%" alt="Ember: Memory recall for dementia care. with Dr. Chen Chen, venue UIST poster, status in progress.">
</p>

<!-- FLAGSHIPS:END -->

### Selected work

<!-- SELECTED:START -->

<a href="https://github.com/Aaryan1524/ClaudeSentinel"><img src="assets/rows/claude-sentinel.svg" width="100%" alt="Claude Sentinel — knows the instant your Claude usage window resets, even with the laptop closed. Python."></a><br>
<a href="https://github.com/Aaryan1524/ReccursiveCommits"><img src="assets/rows/recursive-commits.svg" width="100%" alt="Recursive Commits — an offline-first CLI for safely scheduling verified software changes across Git repositories. Rust."></a><br>
<a href="https://github.com/Aaryan1524/RepoParser"><img src="assets/rows/repoparser.svg" width="100%" alt="RepoParser — chat with any GitHub repo; RAG over an ingested codebase. Python."></a><br>
<a href="https://github.com/Aaryan1524/Personal_trading"><img src="assets/rows/personal-trading.svg" width="100%" alt="Personal trading — scenario modeling over hype. Python."></a><br>
<a href="https://github.com/Aaryan1524/Shadow-PrincetonHacks-Education-Track-"><img src="assets/rows/shadow.svg" width="100%" alt="Shadow — a Meta smart-glasses coach that watches a physical skill and gives live feedback. Python."></a><br>
<a href="https://github.com/Aaryan1524/event_finder"><img src="assets/rows/event-finder.svg" width="100%" alt="event_finder — hyper-local event discovery, from house parties and pickup games to academic workshops. TypeScript."></a><br>

<!-- SELECTED:END -->

<!-- REPOS:START -->

<details>
<summary>Everything else (16)</summary>

##### Tools and agents

- **[Prompt Perfector](https://github.com/Aaryan1524/Prompt-Perfector-AI-)** — turns vague prompts into precise, optimized ones · HTML · ★ 1 · updated 11 months ago
- **[Agent Sentinel](https://github.com/Aaryan1524/AgentSentinel)** — Python · updated today
- **[Codex Skills](https://github.com/Aaryan1524/Codex_Skills)** — Python · ★ 1 · updated 3 days ago

##### Markets

- **[NSE sentiment analysis](https://github.com/Aaryan1524/NSE_sentiment_analysis)** — market sentiment from NSE data · JavaScript · ★ 1 · updated 7 months ago
- **[AI loan repayment](https://github.com/Aaryan1524/AI-loan-Repayment-)** — repayment modeling · TypeScript · ★ 1 · updated 6 months ago

##### Systems

- **[Concurrent Job Scheduler](https://github.com/Aaryan1524/Concurrent-Job-Scheduler)** — a multithreaded scheduler in Java · Java · ★ 1 · updated 5 months ago
- **[Chess server](https://github.com/Aaryan1524/Chess_server)** — a game server in Python · Python · ★ 1 · updated 10 months ago
- **[Te Vārtā architecture](https://github.com/Aaryan1524/TeVarta-architecture)** — the system design behind the engine · ★ 1 · updated 2 months ago

##### Products and hackathons

- **[Bosnai](https://github.com/Aaryan1524/Bosnai)** — TypeScript · ★ 1 · updated today
- **[StackMap](https://github.com/Aaryan1524/StackMap)** — Python · ★ 1 · updated 6 months ago
- **[cruisefrnds](https://github.com/Aaryan1524/cruisefrnds)** — TypeScript · ★ 1 · updated 6 months ago
- **[Desktop Pet](https://github.com/Aaryan1524/Desktop-Pet)** — TypeScript · updated 2 months ago
- **[305 Gemma efficiency](https://github.com/Aaryan1524/305Gemma-efficiencyproj)** — Python · ★ 1 · updated 7 weeks ago
- **[Craigslist redesign](https://github.com/Aaryan1524/Craigslist_redesign)** — reimagining a classic · HTML · ★ 1 · updated 5 months ago

</details>

<!-- REPOS:END -->

<details>
<summary>Evidence: where each layer was detected</summary>

### Shipped, end to end

Each cell was read from source and links to the file that proves it.

<!-- MATRIX:START -->

| Project | Interface | API | Data | AI | Deploy | Idea → shipped |
|---|---|---|---|---|---|---|
| Te Vārtā | iOS | FastAPI | Postgres | — | Actions | 1 day |
| [Claude Sentinel](https://github.com/Aaryan1524/ClaudeSentinel) | [CLI](https://github.com/Aaryan1524/ClaudeSentinel/blob/main/claude_usage_watcher.py) | — | [JSON state](https://github.com/Aaryan1524/ClaudeSentinel/blob/main/claude_usage_watcher.py) | — | [launchd](https://github.com/Aaryan1524/ClaudeSentinel/blob/main/launchd/com.claude-usage-watcher.plist) | 0 days |
| [event_finder](https://github.com/Aaryan1524/event_finder) | [Next.js](https://github.com/Aaryan1524/event_finder/blob/main/package.json) | [Next API](https://github.com/Aaryan1524/event_finder/blob/main/src/app/api/auth/%5B...nextauth%5D/route.ts) | [Supabase](https://github.com/Aaryan1524/event_finder/blob/main/package.json) | — | [Docker](https://github.com/Aaryan1524/event_finder/blob/main/websocket-server/docker-compose.yml) | 42 days |

*Cells detected from source on 2026-09-15.*

<!-- MATRIX:END -->

</details>

<!-- FOOTER:START -->

### Set in

Python · FastAPI · TypeScript · React · Next.js · Java · C# / .NET · Neo4j · PostgreSQL · Supabase · pgvector · spaCy · Claude API · Docker · AWS

### Correspondence

[www.tevarta.com](https://www.tevarta.com) · [X](https://x.com/aaryangajulaa) · [LinkedIn](https://www.linkedin.com/in/aaryangajula) · [aaryangajula17@gmail.com](mailto:aaryangajula17@gmail.com)

### Colophon

*Plates are SVG, rebuilt nightly by GitHub Actions.*

<!-- FOOTER:END -->
