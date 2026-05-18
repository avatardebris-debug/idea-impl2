# Master Ideas List — Consolidated

Ideas are processed top-to-bottom. The pipeline picks the first unchecked `[ ]` item.
Checked `[x]` = confirmed built by autonomous pipeline in a previous session.
Unchecked `[ ]` = still needs to be built, validated, or tested by the runner.

## Format
`- [ ] **Title** — Description`

---

## Core Utility Tools

- [x] **CSV Analyzer** — Build a Python CLI tool that reads a CSV file and prints summary statistics (row count, column names, min/max/mean for numeric columns, null counts). Include argparse, error handling for missing files and malformed CSVs, and unit tests with sample fixture files.
- [x] **File Deduplicator** — Build a Python script that scans a directory recursively, finds duplicate files by MD5 hash, and prints a report of duplicates grouped by hash. Optionally deletes duplicates with a --delete flag (with dry-run mode). Include unit tests.
- [x] **Markdown to HTML Converter** — Build a Python CLI that converts a markdown file to a standalone HTML file with basic CSS styling. Support headers, bold, italic, code blocks, and links. Include unit tests for each element type.
- [x] **URL Health Checker** — Build a Python CLI that reads a list of URLs from a text file, sends HEAD requests (with timeout), and outputs a report showing status code, response time, and whether each URL is up or down. Include concurrent checking with threading and unit tests with mock HTTP responses.
- [x] **JSON Diff Tool** — Build a Python CLI that compares two JSON files and prints a human-readable diff showing added, removed, and changed keys/values. Handle nested objects and arrays. Include unit tests covering edge cases.

---

## Productivity & Content Tools

- [x] **[ai author suite]** — [niche/topic research, keyword research, book outliner, chapter developer, chapter outliner, detail fill in, deep editor restructure format, cover designer, book cover designer, etc]
- [x] **[summarizer tool]** — [from a dashboard use an llm to summarize uploaded pdfs, youtube links, websites, blogs. user share links or download files and click summarize, or prompt agent what is needed from source material.]
- [x] **[transcript extractor]** — [transcript extractor from video and audio + summary tool. use fast whisper or faster whisper github or something.]
- [x] **[Youtube studio]** — [multistep studio for building youtube videos. story generator or video commercial to video or movie format save cat format video format. Title and thumbnail and keyword generator, transcript builder tool. template developer and implementor]
- [x] **[youtube workflow tool.]** — [youtube workflow tool.]
- [x] **[memory system]** — [moonwalking with Einstein memory system. musical wheel visualizer generator for decks of cards and numbers and others.]
- [x] **[mobile access to pc]** — [Make tool to access pc remotely from apple mobile device or ipad.]
- [x] **[shuffler tracker teacher]** — [visualize how decks are shuffled. Stochastic variation whether it is an even cut 26/26 on each half or another variation like 20/30 or 30/20 statistically distributed around 26/26]
- [x] **[tim ferriss learning tool]** — [Using meta-learning accelerated learning techniques to help deconstruct topic, DISSS. Gather material of various media, summarize sources, outline, provide an LLM/RAG for asking/answering about the details, deep dive and 80/20 extraction of most important parts, lesson plans sequencing of the parts, etc. Compression, Frequency, Encoding for memory tricks.]
- [x] **[udemy training tool]** — [udemy training tool]
- [x] **[newsletter /online profit environment for LLM RL training and sims.]** — [newsletter /online profit environment for LLM RL training and sims.]
- [x] **[pocketknife of the internet]** — [new internet browser. acts like a windows/computer that you can access on a website and user interface where you can move windows within the browser around. Merges the computer's software with internet apps and websites.]

---

## Video Suite (Lock Group — process in order)

- [x] **[video ingestor summary]** — [[lock] upload videos parse dialogue to text recognition, summarize content and answer questions model agnostic LLM harness]
- [x] **[video babbel]** — [[lock] translate video to any language, and then parse dialogue, perform any translation, summarize content and answer questions in any language. requires: video_ingestor_summary]
- [x] **[video langfake]** — [[lock] alter the lips and translate the video to any language. deepfake subtle changes to translate video to any language. requires: video_ingestor_summary]
- [x] **[video scribe]** — [[lock] Extracts frames from video at scene boundaries using OpenCV, then uses a VLM (GPT-4V/LLaVA) to generate structured scene descriptions: visual content, camera techniques, lighting, composition, transitions. Outputs to Markdown/JSON. requires: video_ingestor_summary]
- [x] **[video pow]** — [[lock] convert description of video to video from the video alone. can use or modify existing tools on github.]
- [x] **[video GAN]** — [[lock] GAN and RL training. one determines if the video is real or fake, the other adapts video pow to generate fake from a real video and presents one or the other and both sides improve. requires: video_pow]
- [x] **[video recipe]** — [[lock] Takes video_scribe output (structured scene descriptions) and uses an LLM to extract ordered action steps, building a recipe/SOP. Outputs JSON with: step number, action, objects involved, duration, preconditions. requires: video_scribe]
- [x] **[babble]** — [[lock] Duolingo style language learning. Find the most common phrases across multiple languages. Learn in order of usage value. Use accelerating learning techniques and memory palace tricks.]
- [ ] **[video babbel enhanced]** — [[lock] Combines video_ingestor_summary + video_babbel + babble for Duolingo-style language learning from uploaded videos. Extracts common phrases by frequency, generates bilingual flashcards, lip-sync translation overlays, and spaced-repetition practice. requires: video_babbel, babble, video_ingestor_summary]

---

## E-Commerce & Drop Servicing

- [x] **[drop servicing tool]** — [store SOPs and workflows and enable LLM scaling and agentic scaling for performing bulk tasks.]
- [x] **[dropship/service/ecommerce. autoSEO autometa]** — [dropship/service/ecommerce. autoSEO autometa]
- [x] **[fiverr job automation tool]** — [create automated tasks on fiverr.]
- [x] **[email tool]** — [email processing, rules, systems, agentic instruction, automations. Tool for automating the searching in emails and attachments to follow rules and organize into folders. Ability to export emails or systematize an export/import.]
- [x] **[job automation tool]** — [job automation tool]
- [x] **[SEO tool]** — [SEO tool]

---

## Finance & Prediction Markets

- [x] **[Chronovision]** — [Financial world model pipeline using state space modeling and ensemble prediction for market forecasting. Palantir-style predictive intelligence platform.]
- [x] **[Forensic accounting suite]** — [OSINT for corporate tracking. Tracking shipping manifests, procurement data, government contract databases, corporate registry data. Correlating companies on maps/satellites to SEC filings. Cross correlation engine, anomaly detection.]
- [x] **[quant developing program for prediction markets, sports, events, weather markets]** — [[lock] Using Hawkes Process and market maker spread costs. Sharpe ratio simulations. Expected value, bayes theorem, kelly criterion, KL divergence, LMSR. Betting using RSI, MACD for line changes.]
- [x] **[sports/event bet front runner]** — [[lock] Use AI to frontrun polymarket and DFS. Leverage broadcast delays and parse raw api data from stadiums. RL-trained prediction algorithms.]
- [x] **[DFS arb]** — [[lock] daily fantasy sports formula for arbitrage and mispriced lines, bonus and promo hunting and algorithmic entering if there is value added proposition.]
- [x] **[Zillow]** — [tool using redfin/zillow to trigger criteria alert to phone/email.]

---

## Football / Sports Suite

- [x] **[Football simulator]** — [nfl/highschool/college regulation field size physics engine. reinforcement learning to optimize success rate vs standard NFL play calls and adversarial self play.]
- [x] **[player attribute library]** — [Integration for the Football tool above with ability to match with player attributes. requires: football_simulator]
- [x] **[FFO]** — [Football Financial Optimizer. Integration with financial model for valuing players vs salary cap. requires: football_simulator, player_attribute_library]
- [x] **[Football NFL draft and recruit optimizer]** — [Integration with the above for NFL draft for same purposes. requires: football_simulator, ffo]
- [x] **[advantage player cardgame simulator training]** — [monte carlo simulations and training. blackjack, video poker, tournament poker vs cash game, 7 card stud, limit holdem. progressive jackpot slot calculator]

---

## Social & Media Management

- [x] **[social media management/etc]** — [airtable like platform or system for managing social media posts and accounts. AI can help generate content and schedule posts and scale]
- [x] **[video management]** — [airtable like platform or system for managing video content. AI can help generate content and schedule videos and scale. Integration with youtube suite]
- [x] **[podcastseo metadata optimizer]** — [podcast SEO metadata optimizer]

---

## OSINT & Intelligence

- [x] **[osint corp]** — [OSINT Corporation platform. Comprehensive OSINT data ingestion, entity resolution, and analysis pipeline.]
- [x] **[scott adams bot/llm fine tuning]** — [scott adams bot/llm fine tuning]

---

## Experimental & Gaming

- [x] **[VR practice mode.]** — [VR practice mode.]
- [x] **[VR room for stock ticker scanning.]** — [VR room for stock ticker scanning.]
- [x] **[thronglets as a game]** — [each thronglet is an agent, each agent has a 2d world and you can prompt it and it can visualize interactions with the others. Turn system management into a game.]
- [x] **[VASTAI instance initializer]** — [User sets up preset commands for a vast AI terminal, time between commands, number of instances into a database, selects all the settings and so on and clicks run and it initializes according to the user selections]

---

## Extended Backlog (merged from unstarted_projects_backlog.md)

- [ ] **[unweb]** — [This tool should unmask the connections of any news story. Connects people to organizations, think tanks, financing, NGO networks. Looks for political biases, follows the money. Scans for agenda-based talking-point phrasing and strikes through text with propaganda explanations on hover.]
- [ ] **[See BS]** — [news BS filter based on several scott adams techniques. Scott Alexander rule, Gellman Amnesia, "who reports is as important as what".]
- [ ] **[research1]** — [User provides a topic; tool searches highly credible sources (arXiv, PubMed, Wikipedia, CrossRef, Semantic Scholar, gov domains, bioRxiv, NBER, etc) and creates a well-sourced report. "informational" or "recipe" format. Model-agnostic LLM.]
- [ ] **[extraction]** — [Turn source material from summarizer tool into a recipe or step-by-step sequences for skill extraction. requires: summarizer_tool]
- [ ] **[skillify]** — [Turn recipe from extraction into a Claude skill / JSON skill file. Export-compatible. requires: summarizer_tool, extraction]
- [ ] **[skill ninja]** — [Container and public-facing tool for skillify, extraction, summarizer_tool. requires: summarizer_tool, extraction, skillify]
- [ ] **[JSON skill]** — [Enable local AI to run Claude skills as JSON files. Contains loader, dispatcher, and runtime that injects into the model.]
- [ ] **[pairenv]** — [environment enabling the pairing of real world hardware to then assign it to software and send and receive commands and translate English to the necessary format to access the tool]
- [ ] **[AgentFlow Drophip]** — [Autonomous drop shipping orchestration platform that lets you describe your entire operation and it builds, runs and scales workflows for you using agentic AI.]
- [ ] **[RL for dropshipping]** — [Train on cloning successful dropshipping first then run RL. Source deep RL zoo or others from github. Use profit/traffic/revenue per cost. Simulate in MiroFish marketplace then roll out. 10% kelly criterion risk management.]
- [ ] **[dropstore]** — [dropshipping niche or superstore builder and website integration. Compatible with shopify or others.]
- [ ] **[dropify]** — [dropshipping shopify clone]
- [ ] **[podcast]** — [Extract lessons from podcast. FastWhisper transcript → LLM process → find lessons per episode. Customizable prompt, number of lessons per run, model-agnostic.]
- [ ] **[book researcher]** — [Find books people aren't writing but want. Scan reviews, Quora, etc from top-selling info products for "I wish it also did X" feedback. LLM deconstructs into table of contents for gap-filling book.]
- [ ] **[amazon audiobook to pdf converter]** — [Convert amazon audiobook to pdf]
- [ ] **[AI Author Audiobook Integration]** — Add automated narration synthesis and dynamic cover art animation to the ai_author_suite. requires: ai_author_suite
- [ ] **[AI Author Docs Platform]** — Merge ai_author_suite and docsai_documentation_generator to publish technical books automatically. requires: ai_author_suite, docsai_documentation_generator
- [ ] **[AI Screenplay Writer]** — Automated scriptwriting assistant that handles plot structure, dialogue generation, and formatting. requires: ai_author_suite
- [ ] **Book content repurposer** — Module for ai_author_suite that auto-generates blog posts, social media threads, newsletter articles, and course outlines from chapters. requires: ai_author_suite
- [ ] **Automated SEO content factory** — Combines ai_author_suite with dropship autoSEO autometa to generate SEO-optimized product descriptions and blog content at scale. requires: ai_author_suite, dropshipserviceecommerce_autoseo_autometa
- [ ] **[DocsAI Code Execution Engine]** — Add interactive code snippet execution and automatic API reference mapping to docsai_documentation_generator. requires: docsai_documentation_generator
- [ ] **[Data Docs Generator]** — Merge docsai_documentation_generator and csv_analyzer to auto-generate schema and API documentation. requires: docsai_documentation_generator, csv_analyzer
- [ ] **CSV data pipeline builder** — Extend CSV analyzer with a visual pipeline builder that chains transformations (filter, join, pivot, aggregate) between multiple CSV files with export to SQL or JSON. requires: csv_analyzer
- [ ] **Email attachment to CSV pipeline** — Connector that extracts CSV attachments from emails processed by email_tool, runs them through csv_analyzer, and routes results to a configured folder or webhook. requires: email_tool, csv_analyzer
- [ ] **Smart email-to-SOP executor** — Combines email_tool with drop_servicing_tool to automatically parse incoming emails, extract task requirements, and trigger SOP-based agentic workflows. requires: email_tool, drop_servicing_tool
- [ ] **SOP marketplace** — Add a marketplace module to drop_servicing_tool where users can publish, discover, and license SOPs with version control, ratings, and one-click import. requires: drop_servicing_tool
- [ ] **SOP output to YouTube content feed** — Bridge that takes SOPStep outputs from drop_servicing_tool and formats them into YouTube video scripts, titles, and thumbnail text. requires: drop_servicing_tool, youtube_workflow_tool
- [ ] **Resume-to-job-applicant automator** — Combines drop_servicing_tool with fiverr_job_automation_tool to analyze job listings, auto-generate tailored applications, and manage bulk outreach campaigns. requires: drop_servicing_tool, fiverr_job_automation_tool
- [ ] **Resume and cover letter builder** — Takes a job description and candidate profile, generates tailored resumes and cover letters using LLM-assisted rewriting. requires: drop_servicing_tool
- [ ] **LLMClient bridge for AI Author** — Adapter that plugs the LLMClient protocol from drop_servicing_tool into ai_author_suite so all modules share the same LLM interface. requires: drop_servicing_tool, ai_author_suite
- [ ] **Card composition calculator** — Deck composition analyzer: card counting advantage, true count, running count across shuffle patterns. requires: advantage_player_cardgame_simulator_training
- [ ] **[Card Game Variant Expansion]** — Add Texas Hold'em and Omaha variants with AI opponent modeling to the cardgame simulator. requires: advantage_player_cardgame_simulator_training
- [ ] **Cardgame simulator output to learning tool** — Bridge that exports Monte Carlo training results and strategy metrics from the cardgame simulator into tim_ferriss_learning_tool format for spaced repetition. requires: advantage_player_cardgame_simulator_training, tim_ferriss_learning_tool
- [ ] **Card game training course platform** — Combines cardgame simulator with tim_ferriss_learning_tool to create interactive poker and blackjack training courses. requires: advantage_player_cardgame_simulator_training, tim_ferriss_learning_tool
- [ ] **[Interactive Fiction Engine]** — Combine ai_author_suite and advantage_player_cardgame_simulator_training for branching narrative games. requires: ai_author_suite, advantage_player_cardgame_simulator_training
- [ ] **[movie player]** — [[lock] front end player to play the AI movies. requires: ai_movie_generation_suite]
- [ ] **[dialog generator]** — [[lock] generate dialogue between characters. requires: ai_movie_generation_suite]
- [ ] **[director/editor]** — [[lock] direct and cut using RL. requires: ai_movie_generation_suite]
- [ ] **Real estate listing analyzer** — CLI tool that pulls property data from public APIs, analyzes price trends, neighborhood metrics, and generates comparative market reports. requires: zillow
- [ ] **[SEC to CSV Bridge]** — Pipeline that converts raw SEC filing XML into standardized CSVs for csv_analyzer ingestion.
- [ ] **[Simulator Result Aggregator]** — Pipeline that collects and normalizes monte_carlo training outputs across multiple game simulators. requires: advantage_player_cardgame_simulator_training, football_simulator
- [ ] **[Real-Time Market Predictor]** — Prediction engine that tracks financial sentiment and forecasts asset price movements. requires: chronovision
- [ ] **Video content SEO engine** — Combines dropship autoSEO autometa with youtube_workflow_tool to generate SEO titles, descriptions, tags, and transcripts for YouTube video catalogs at scale. requires: dropshipserviceecommerce_autoseo_autometa, youtube_workflow_tool
- [ ] **Agent observability dashboard** — Real-time dashboard that tracks agent execution metrics (steps taken, LLM calls, costs, errors, duration) across all running pipeline projects with alerting on anomalies.
- [ ] **[Pipeline Observability Dashboard]** — Real-time visualization of agent execution, costs, and failure rates across all projects.
- [ ] **Project dependency graph visualizer** — Reads all project workspace files and MANIFEST.json to generate a visual dependency graph.
- [ ] **[Automated Dependency Resolver]** — Tool that tracks cross-project requirements and automatically syncs version constraints.
- [ ] **Shared LLM cost tracker** — Cost-tracking middleware to the LLMClient protocol that logs every LLM call's token usage and cost across all projects, with monthly budget alerts.
- [x] **[Universal LLM Router]** — Adapter that routes requests across llmclient providers with automatic fallback and load balancing.
- [x] **[Config Schema Validator]** — Linter that validates pipeline YAML definitions against typed schemas before execution.
- [x] **Code review diff summarizer** — CLI tool that reads git diff output, summarizes changes by file and function, flags potential issues, and generates a human-readable review briefing.
- [x] **Test fixture generator** — Build a tool that generates realistic test fixtures (CSV files, JSON payloads, mock API responses, sample documents) for any project by reading its existing test patterns and schemas.
- [x] **[Test Coverage Mutator]** — Automated suite that generates mutation tests and enforces quality thresholds across the pipeline.
- [x] **Cross-project code linter** — CLI tool that runs consistent linting, type checking, and import analysis across all workspace projects, enforcing a shared style guide and flagging cross-project API mismatches.
- [ ] **Contract clause extractor** — PDF and DOCX parser that identifies and extracts key contract clauses (termination, liability, NDAs) into a structured searchable database with export options.
- [ ] **[Startup Compliance Scanner]** — Automated checklist generator that maps startup data to SOC2 and GDPR requirements.
- [ ] **[Technical Whitepaper Generator]** — AI system that researches, outlines, and drafts professional engineering documentation.
- [ ] **API mock server generator** — Tool that reads an OpenAPI/Swagger spec and generates a fully functional mock API server with configurable response delays, random data generation, and request logging.
- [ ] **[PDF Schema Analyzer]** — CLI tool that extracts and validates complex structures from unstructured PDF documents.
- [ ] **Meeting notes auto-summarizer** — Tool that takes raw meeting transcripts or audio recordings, identifies action items, decisions, and key topics, and outputs a structured summary with assignees and deadlines.
- [ ] **Personal finance tracker CLI** — Python CLI that imports bank CSV transactions, categorizes them by merchant patterns, generates monthly budget reports, and alerts on spending anomalies.
- [ ] **Local weather dashboard CLI** — Python CLI that fetches local weather data from OpenWeatherMap, displays current conditions and 7-day forecast in terminal with color-coded alerts for severe weather.
- [ ] **[Local Knowledge Graph Builder]** — Privacy-focused desktop app that connects personal notes, files, and bookmarks.
- [ ] **[Figma to Mobile App Generator]** — AI pipeline that converts design mockups into production-ready cross-platform code.
- [ ] **[Autonomous Web Vulnerability Scanner]** — Continuous security tool that automatically probes and patches public web assets.
- [ ] **[SaaS Pricing Optimizer]** — Automated tool that analyzes competitor pricing and recommends optimal subscription tiers.
- [ ] **[Manuscript to Docs Bridge]** — Formatter that transforms ai_author_suite output into docsai_documentation_generator compatible specs.

---

## Robotics & Physical Agency

- [ ] **[subgoal generator]** — [General-purpose LLM goal decomposition engine. Takes any high-level goal ("build a house", "make $10k/month", "learn Spanish") and uses an LLM to produce an ordered list of subgoals with dependencies. Each subgoal is formatted as a pipeline idea entry and injected into master_ideas.md for the runner to execute. Operates on any domain: robotics, software, business, learning. The agent's hypothesis and goal-creation layer — enables recursive autonomous expansion of any objective into buildable sub-tasks. The runner processes each subgoal through the normal executor/validator/critic cycle.]

- [ ] **[robot primitive vocabulary]** — [[lock] Design document and shared library module defining ~25-30 canonical atomic robot action primitives. Locomotion: move_to, rotate_to, approach, retreat. Manipulation: grasp, release, push, pull, lift, place, insert, rotate_object. Observation: look_at, scan, measure_distance, detect_object. Force: apply_force, apply_torque, maintain_contact. Control flow: sequence, parallel, repeat_until, conditional, wait, signal_done, request_human. Published as shared_libs/RobotPrimitives/ so all robot projects import from one canonical source.]

- [ ] **[robo primitive mapper]** — [[lock] Maps video_recipe action descriptions to the canonical robot primitive vocabulary. Handles unit conversion, reference frame normalization (world/object/gripper), validates each action maps to a known primitive. Output: robot_program.json ready for mujoco_codegen. requires: video_recipe, robot_primitive_vocabulary]

- [ ] **[mujoco codegen]** — [[lock] Generates runnable MuJoCo XML scene files and Python control scripts from robo_primitive_mapper output. Handles object placement, trajectory planning, contact and grasp primitives. Executes simulation and records render video. Output: scene.xml, control.py, render.mp4. requires: robo_primitive_mapper]

- [ ] **[sim real comparator]** — [[lock] Given a real video clip and a MuJoCo simulation render of the same task, computes multi-metric similarity: SSIM, perceptual hash, CLIP embedding cosine similarity. Outputs per-frame heatmap + global score in [0,1]. Core evaluation tool for sim-to-real gap measurement. requires: video_ingestor_summary]

- [ ] **[sim real discriminator]** — [[lock] GAN-style critic trained to distinguish real robot/human footage from MuJoCo renders. Discriminator score is the RL reward signal driving adversarial sim improvement. Extends video_GAN architecture. Once gap closes past threshold, additional criteria push performance beyond the original demonstration. requires: sim_real_comparator, video_gan]

- [ ] **[pufferlib rl harness]** — [[lock] Wraps MuJoCo robot skill environments with PufferLib (github.com/PufferAI/PufferLib) for vectorized high-throughput RL training. Achieves 10-100x sample efficiency vs naive implementations. Enables training primitive skills on a consumer RTX 4090 instead of A100 cluster. Exposes: train_skill(skill_name, reward_fn, n_envs=512, max_steps=1M). Plugs sim_real_discriminator score in as reward. requires: mujoco_codegen]

- [ ] **[robot skill library]** — [[lock] SQLite + FAISS vector database of verified robot skill programs. Schema: {skill_id, name, description_embedding, video_example_path, robo_program_path, sim_score, real_score, primitive_tags}. Query by semantic similarity. Reviewer promotes successful skills here after validation. Shared library acts as reviewer: all new skills checked for redundancy and interface consistency before promotion. requires: robo_primitive_mapper]

- [ ] **[goal decomposer]** — [[lock] LLM agent that takes any high-level goal and recursively decomposes it into a dependency tree of skills using subgoal_generator. Checks robot_skill_library for each node — found skills reused, gap skills queued as video_recipe jobs. Robot can invoke any software pipeline tool (web scraping, SEO, legal, payments, Airbnb) as subgoals alongside physical skills — unified goal graph across physical and digital domains. requires: robot_skill_library, subgoal_generator]

- [ ] **[robot pipeline fork]** — [[lock] Fork of the autonomous pipeline with agents retuned for robot skill development: skill_planner, robo_codegen, sim_runner, sim_critic, skill_reviewer. Same runner/message bus/budget management — ~30% new code, ~70% reused. Robot has full LLM access and the current agent harness to develop its own software in addition to robot skill programs. Can spawn any software pipeline tool: websites, SEO, legal, finance, delegate to other robots. shared_libs/RobotPrimitives is the canonical reviewer for all generated robot code. requires: goal_decomposer, pufferlib_rl_harness, sim_real_discriminator, robot_skill_library]
