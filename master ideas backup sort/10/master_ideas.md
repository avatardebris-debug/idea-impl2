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
- [ ] **URL Health Checker** — Build a Python CLI that reads a list of URLs from a text file, sends HEAD requests (with timeout), and outputs a report showing status code, response time, and whether each URL is up or down. Include concurrent checking with threading and unit tests with mock HTTP responses.
- [x] **JSON Diff Tool** — Build a Python CLI that compares two JSON files and prints a human-readable diff showing added, removed, and changed keys/values. Handle nested objects and arrays. Include unit tests covering edge cases.

---

## Productivity & Content Tools

- [x] **[ai author suite]** — [niche/topic research, keyword research, book outliner, chapter developer, chapter outliner, detail fill in, deep editor restructure format, cover designer, book cover designer, etc]
- [x] **[summarizer tool]** — [from a dashboard use an llm to summarize uploaded pdfs, youtube links, websites, blogs. user share links or download files and click summarize, or prompt agent what is needed from source material.]
- [x] **[memory system]** — [moonwalking with Einstein memory system. musical wheel visualizer generator for decks of cards and numbers and others.]
- [x] **[mobile access to pc]** — [Make tool to access pc remotely from apple mobile device or ipad.]
- [x] **[shuffler tracker teacher]** — [visualize how decks are shuffled. Stochastic variation whether it is an even cut 26/26 on each half or another variation like 20/30 or 30/20 statistically distributed around 26/26]
- [x] **[pocketknife of the internet]** — [new internet browser. acts like a windows/computer that you can access on a website and user interface where you can move windows within the browser around. Merges the computer's software with internet apps and websites.]
- [ ] **[transcript extractor]** — [transcript extractor from video and audio + summary tool. use fast whisper or faster whisper github or something.]
- [ ] **[Youtube studio]** — [multistep studio for building youtube videos. story generator or video commercial to video or movie format save cat format video format. Title and thumbnail and keyword generator, transcript builder tool. template developer and implementor]
- [ ] **[youtube workflow tool.]** — [youtube workflow tool.]
- [ ] **[tim ferriss learning tool]** — [Using meta-learning accelerated learning techniques to help deconstruct topic, DISSS. Gather material of various media, summarize sources, outline, provide an LLM/RAG for asking/answering about the details, deep dive and 80/20 extraction of most important parts, lesson plans sequencing of the parts, etc. Compression, Frequency, Encoding for memory tricks.]
- [ ] **[udemy training tool]** — [udemy training tool]
- [ ] **[newsletter /online profit environment for LLM RL training and sims.]** — [newsletter /online profit environment for LLM RL training and sims.]

---

## Video Suite (Lock Group — process in order)

- [x] **[video ingestor summary]** — [[lock] upload videos parse dialogue to text recognition, summarize content and answer questions model agnostic LLM harness]
- [x] **[video babbel]** — [[lock] translate video to any language, and then parse dialogue, perform any translation, summarize content and answer questions in any language. requires: video_ingestor_summary]
- [x] **[video langfake]** — [[lock] alter the lips and translate the video to any language. deepfake subtle changes to translate video to any language. requires: video_ingestor_summary]
- [ ] **[video scribe]** — [[lock] translate a video to scene description, connecting an LLM to describe the details of every scene, camera tricks, transitions, etc.]
- [ ] **[video pow]** — [[lock] convert description of video to video from the video alone. can use or modify existing tools on github.]
- [ ] **[video GAN]** — [[lock] GAN and RL training. one determines if the video is real or fake, the other adapts video pow to generate fake from a real video and presents one or the other and both sides improve. requires: video_pow]
- [ ] **[video scribe]** — [[lock] Extracts frames from video at scene boundaries using OpenCV, then uses a VLM (GPT-4V/LLaVA) to generate structured scene descriptions: visual content, camera techniques, lighting, composition, transitions. Outputs to Markdown/JSON. Acts as the foundation for video_recipe. requires: video_ingestor_summary ]
- [ ] **[video recipe]** — [[lock] Takes video_scribe output (structured scene descriptions) and uses an LLM to extract ordered action steps, building a recipe/SOP. Outputs JSON with: step number, action, objects involved, duration, preconditions. Suitable for agent training data generation or instructional content. requires: video_scribe ]
- [ ] **[babble]** — [[lock] Duolingo style language learning. Find the most common phrases across multiple languages. Learn in order of usage value. Use accelerating learning techniques and memory palace tricks.]
- [ ] **[video babble]** — [[lock] Combines babble Duolingo style language learning. Find the most common phrases across multiple languages. Learn in order of usage value. Use accelerating learning techniques and memory palace tricks.]

---

## E-Commerce & Drop Servicing

- [x] **[drop servicing tool]** — [store SOPs and workflows and enable LLM scaling and agentic scaling for performing bulk tasks.]
- [x] **[dropship/service/ecommerce. autoSEO autometa]** — [dropship/service/ecommerce. autoSEO autometa]
- [ ] **[fiverr job automation tool]** — [create automated tasks on fiverr.]
- [ ] **[email tool]** — [email processing, rules, systems, agentic instruction, automations. Tool for automating the searching in emails and attachments to follow rules and organize into folders. Ability to export emails or systematize an export/import.]
- [x] **[job automation tool]** — [job automation tool]
- [ ] **[SEO tool]** — [SEO tool]

---

## Finance & Prediction Markets

- [x] **[Chronovision]** — [Financial world model pipeline using state space modeling and ensemble prediction for market forecasting. Palantir-style predictive intelligence platform.]
- [ ] **[Forensic accounting suite]** — [OSINT for corporate tracking. Tracking shipping manifests, procurement data, government contract databases, corporate registry data. Correlating companies on maps/satellites to SEC filings. Cross correlation engine, anomaly detection.]
- [ ] **[quant developing program for prediction markets, sports, events, weather markets]** — [[lock] Using Hawkes Process and market maker spread costs. Sharpe ratio simulations. Expected value, bayes theorem, kelly criterion, KL divergence, LMSR. Betting using RSI, MACD for line changes.]
- [ ] **[sports/event bet front runner]** — [[lock] Use AI to frontrun polymarket and DFS. Leverage broadcast delays and parse raw api data from stadiums. RL-trained prediction algorithms.]
- [ ] **[DFS arb]** — [[lock] daily fantasy sports formula for arbitrage and mispriced lines, bonus and promo hunting and algorithmic entering if there is value added proposition.]
- [x] **[Zillow]** — [tool using redfin/zillow to trigger criteria alert to phone/email.]

---

## Football / Sports Suite

- [x] **[Football simulator]** — [nfl/highschool/college regulation field size physics engine. reinforcement learning to optimize success rate vs standard NFL play calls and adversarial self play.]
- [x] **[player attribute library]** — [Integration for the Football tool above with ability to match with player attributes. requires: football_simulator]
- [x] **[FFO]** — [Football Financial Optimizer. Integration with financial model for valuing players vs salary cap. requires: football_simulator, player_attribute_library]
- [x] **[Football NFL draft and recruit optimizer]** — [Integration with the above for NFL draft for same purposes. requires: football_simulator, ffo]
- [ ] **[advantage player cardgame simulator training]** — [monte carlo simulations and training. blackjack, video poker, tournament poker vs cash game, 7 card stud, limit holdem. progressive jackpot slot calculator]

---

## Social & Media Management

- [ ] **[social media management/etc]** — [airtable like platform or system for managing social media posts and accounts. AI can help generate content and schedule posts and scale]
- [ ] **[video management]** — [airtable like platform or system for managing video content. AI can help generate content and schedule videos and scale. Integration with youtube suite]
- [ ] **[podcastseo metadata optimizer]** — [podcast SEO metadata optimizer]

---

## OSINT & Intelligence

- [ ] **[osint corp]** — [OSINT Corporation platform. Comprehensive OSINT data ingestion, entity resolution, and analysis pipeline.]
- [x] **[scott adams bot/llm fine tuning]** — [scott adams bot/llm fine tuning]

---

## Experimental & Gaming

- [x] **[VR practice mode.]** — [VR practice mode.]
- [ ] **[VR room for stock ticker scanning.]** — [VR room for stock ticker scanning.]
- [ ] **[thronglets as a game]** — [each thronglet is an agent, each agent has a 2d world and you can prompt it and it can visualize interactions with the others. Turn system management into a game.]
- [ ] **[VASTAI instance initializer]** — [User sets up preset commands for a vast AI terminal, time between commands, number of instances into a database, selects all the settings and so on and clicks run and it initializes according to the user selections]



## Robotics & Physical Agency

- [ ] **[Bootstrap Robot Training]** — Design the full robot primitive vocabulary and skill acquisition pipeline, from atomic motion primitives through sim-to-real gap measurement. --goal

- [ ] **[subgoal generator]** — [General-purpose LLM goal decomposition engine. Takes any high-level goal ("build a house", "make $10k/month", "learn Spanish") and uses an LLM to produce an ordered list of subgoals with dependencies. Each subgoal is formatted as a pipeline idea entry and injected into master_ideas.md for the runner to execute. Operates on any domain: robotics, software, business, learning. The agent's hypothesis and goal-creation layer — enables recursive autonomous expansion of any objective into buildable sub-tasks. The runner processes each subgoal through the normal executor/validator/critic cycle.]

- [ ] **[MuJoCo URDF Research]** — Research and compare 3 MuJoCo-compatible robot URDFs (Franka, UR5, Unitree H1). Write a ranked comparison to .pipeline/goals/urdf_research.md covering DOF, contact complexity, and sim stability. goal_check: Has a ranked comparison of ≥3 URDFs been written to .pipeline/goals/urdf_research.md? --hermes

- [ ] **[robot primitive vocabulary]** — [[lock] Design document and shared library module defining ~25-30 canonical atomic robot action primitives. Locomotion: move_to, rotate_to, approach, retreat. Manipulation: grasp, release, push, pull, lift, place, insert, rotate_object. Observation: look_at, scan, measure_distance, detect_object. Force: apply_force, apply_torque, maintain_contact. Control flow: sequence, parallel, repeat_until, conditional, wait, signal_done, request_human. Published as shared_libs/RobotPrimitives/ so all robot projects import from one canonical source.]

- [ ] **[video recipe]** — [[lock] Takes video_scribe structured scene descriptions and uses an LLM to extract an ordered sequence of atomic actions as a robot recipe. Output JSON: [{step, action, object, xyz_delta, duration_s, preconditions, success_state}]. Any video of a real task becomes a structured skill recipe. requires: video_scribe]

- [ ] **[robo primitive mapper]** — [[lock] Maps video_recipe action descriptions to the canonical robot primitive vocabulary. Handles unit conversion, reference frame normalization (world/object/gripper), validates each action maps to a known primitive. Output: robot_program.json ready for mujoco_codegen. requires: video_recipe, robot_primitive_vocabulary]

- [ ] **[mujoco codegen]** — [[lock] Generates runnable MuJoCo XML scene files and Python control scripts from robo_primitive_mapper output. Handles object placement, trajectory planning, contact and grasp primitives. Executes simulation and records render video. Output: scene.xml, control.py, render.mp4. requires: robo_primitive_mapper]

- [ ] **[sim real comparator]** — [[lock] Given a real video clip and a MuJoCo simulation render of the same task, computes multi-metric similarity: SSIM, perceptual hash, CLIP embedding cosine similarity. Outputs per-frame heatmap + global score in [0,1]. Core evaluation tool for sim-to-real gap measurement. requires: video_ingestor_summary]

- [ ] **[sim real discriminator]** — [[lock] GAN-style critic trained to distinguish real robot/human footage from MuJoCo renders. Discriminator score is the RL reward signal driving adversarial sim improvement. Extends video_GAN architecture. Once gap closes past threshold, additional criteria push performance beyond the original demonstration. requires: sim_real_comparator, video_gan]

- [ ] **[pufferlib rl harness]** — [[lock] Wraps MuJoCo robot skill environments with PufferLib (github.com/PufferAI/PufferLib) for vectorized high-throughput RL training. Achieves 10-100x sample efficiency vs naive implementations. Enables training primitive skills on a consumer RTX 4090 instead of A100 cluster. Exposes: train_skill(skill_name, reward_fn, n_envs=512, max_steps=1M). Plugs sim_real_discriminator score in as reward. requires: mujoco_codegen]

- [ ] **[robot skill library]** — [[lock] SQLite + FAISS vector database of verified robot skill programs. Schema: {skill_id, name, description_embedding, video_example_path, robo_program_path, sim_score, real_score, primitive_tags}. Query by semantic similarity. Reviewer promotes successful skills here after validation. Shared library acts as reviewer: all new skills checked for redundancy and interface consistency before promotion. requires: robo_primitive_mapper]

- [ ] **[goal decomposer]** — [[lock] LLM agent that takes any high-level goal and recursively decomposes it into a dependency tree of skills using subgoal_generator. Checks robot_skill_library for each node — found skills reused, gap skills queued as video_recipe jobs. Robot can invoke any software pipeline tool (web scraping, SEO, legal, payments, Airbnb) as subgoals alongside physical skills — unified goal graph across physical and digital domains. requires: robot_skill_library, subgoal_generator]

- [ ] **[robot pipeline fork]** — [[lock] Fork of the autonomous pipeline with agents retuned for robot skill development: skill_planner, robo_codegen, sim_runner, sim_critic, skill_reviewer. Same runner/message bus/budget management — ~30% new code, ~70% reused. Robot has full LLM access and the current agent harness to develop its own software in addition to robot skill programs. Can spawn any software pipeline tool: websites, SEO, legal, finance, delegate to other robots. shared_libs/RobotPrimitives is the canonical reviewer for all generated robot code. requires: goal_decomposer, pufferlib_rl_harness, sim_real_discriminator, robot_skill_library]

