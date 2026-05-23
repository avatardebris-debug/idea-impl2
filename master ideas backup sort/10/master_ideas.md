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


- [ ] **[Chronovision autoresearch adapter]** — [ [lock] adaptor for chronovision. tracks research papers across arxiv, openreview, bioRxiv, NASA ADS, NBER,FRED,OECD, predicts paper and impact it will have. Also tracks crunchbase, pitchbook, cb insights, y combinator, a16z research to monitor and predict funding spikes to anticipate industry booms and changes and new transformations and growth. requires:osint_corp, forensic, sec_importer, chronovision]

- [ ] **[brain download]** — [Tim Ferriss Meta Learning accelerated Learning inspired "coursera/udemy course builder" that formats the course using deconstruction, selection, sequencing, stakes and compression, encoding, and frequency to optimize the learning experience while also providing quality scripts for video creation for Udemy, with PDF and other tools. The tool is for course designers to make quality courses but it doesn't need to build out the full video training itself. Also should reccomend other resources including entertainment for total immersion and osmosis like fictional enjoyment movies and books as well as the actual non fiction resources f extraction of information.]

- [ ] **[Ranker architecture]** — [Every tool run through this wrapper enables you to choose weight/preferences or rank or score. The idea is the ranker architecture can accumulate value to determine tastes. This could be provided and integrated with machine learning for various purposes.]
- [ ] **[VASTAI instance initializer]** — [User sets up preset commands for a vast AI terminal, time between commands, number of instances into a database, selects all the settings and so on and clicks run and it initializes according to the user selections]
- [ ] **[pairenv]** — [environment enabling the pairing of real world hardware to then assign it to software and send and receive commands and translate English to the necessary format to access the tool]
- [ ] **[agentic mirroring game]** — [game where you input data and with that can build an empire. When agentic mirroring is turned on and everything is paired, your actions are mirrored in real life and integrated with agentic commerce, robots, etc so that the empire you build in the gaming environment happens in real life. requires:pairenv]
- [ ] **[AgentFlow Drophip]** — [Autonomous drop shipping orchestration platform that lets you describe your entire operation and it builds, runs and scales workflows for you using agentic AI.]
- [ ] **[dropsearch]** — [dropship researcher. spy on competitors and come up with a business gameplan in full English describing the entire operation.]
- [ ] **[droppain]** — [dropship marketing campaign. plan and implement a marketing campaign for dropship products integrate with shopify and others]
- [ ] **[Drop=Gentic]** — [Dropshipping and agentic commerce planner]
- [ ] **[RL for dropshipping]** — [train on cloning successful dropshipping first and then running RL. source deep rl zoo or others from github. use profit, traffic, revenue per cost and autoresearch solutions in simulated market place using MiroFish and then roll out and calibrate to real. Assess risk and manage using 10% kelly criterion strategy based on budget.]
- [ ] **[dropstore]** — [dropshipping niche or superstore builder and website integration. choose to make compatible with shopify or others if you want.]
- [ ] **[dropify]** — [dropshipping shopify clone]
- [x] **[Summarizer tool]** — [[lock]from a dashboard use an llm to summarize uploaded pdfs, youtube links, websites, blogs. user share links or download files and click summarize, or prompt agent what is needed from source material. Then agent uses tools/functions to access the sources, extracts, summaries, and presents.]
- [ ] **[extraction]** — [turn source material from summarizer tool into a "recipe" or specific step by step sequences and for potential specific skill extraction. Enable button that save's skill.  requires:summarizer_tool]
- [ ] **[skillify]** — [turn recipe from extraction into claude skill. Also ability to convert claude skill to JSON file for other LLM. "system_prompt": "..." "functions": [ ... ] "examples": [ ... ]. Also, ability to export JSON file or claude skill. requires:summarizer_tool, extraction]
- [ ] **[skill ninja]** — [container and public facing tool for skillify, extraction, summarizer tool. requires:summarizer_tool, extraction, skillify]
- [ ] **[JSON skill]** — [This tool is for enabling local AI to run claude skills as JSON files in the format "system_prompt": "..." "functions": [ ... ] "examples": [ ... ]. Any claude code skill converted into a JSON file should be able to run. Should contain a loader, dispatcher and a runtime that injects it into the model]

- [ ] **[idea]** — [amazon audiobook to pdf converter]
- [ ] **[research1]** — [user provides a topic, then this tool goes through highly credible sources to create a well sourced report User can select "informational" or "recipe" if it's a reciepe it's structured as how to do a particular thing. Ability to choose LLM for response. sources like ARXIV, pub med, wikipedia,crossref, semantic scholar, web of science, scopus, jstor,ssrn,dot gov government domains, biorxiv,medrxiv,openreview,papers with code,nber,fred,data.gov,nist,iso,acm digital library, ieee xplore, rand corporation, bookings institution,,]

- [ ] **[unweb]** — [This tool should unmask the connections of any news story. loosely based on the "mike benz filter" on the world, "if you know what is reported you know anything, but if you know who is reporting, you know everything. This connects people to organizations they work with, the think tanks they or their organization is a part of, who finances them, how NGOs and other entities connect together. This should also look for political biases and follow the money. It should scan for similar agenda based talking point phrasing going on around the same time within the article and strike through the text and on hover over says why this word or phrase is likely propaganda. ]
- [ ] **[See BS]** — [news BS filter based on several scott adams techniques. for example the "Scott Alexander rule", the Gellman Amnesia, the suggestion that "who" reports is just as important as what.]

- [ ] **[book researcher]** — [find the book people aren't writing but that people want. scan reviews, quora, etc from top selling information books, pdfs, video courses, etc for reviews that are like "this book was good but I wish it also did X, it didn't explain Y" and combine for the niche and then LLM deconstructs into a table of contents]

- [ ] **[podcast]** — [extract lessons from podcast.  Tool identifies from a podcast title or link to the overall page. fast whisper transcript->podcast->LLM process. prompt to find the lessons->repeat for the next podct in sequence, etc. Options for number extracted per run, custom instructions about anything you want, etc. insert API or pull ollama model and run with prompt that descibes which LLM you plan to use.]


[ ] [movie player] — [[lock] front end player to play the AI movies. requires: ai_movie_generation_suite]

[ ] [dialog generator] — [[lock] generate dialogue between characters. requires: ai_movie_generation_suite]
[ ] [director/editor] — [[lock] direct and cut using RL. requires: ai_movie_generation_suite]
[ ] [DocsAI Code Execution Engine] — Add interactive code snippet execution and automatic API reference mapping.
[ ] [Drop=Gentic] — [Dropshipping and agentic commerce planner]
[ ] [dropify] — [dropshipping shopify clone]
[ ] [droppain] — [dropship marketing campaign. plan and implement a marketing campaign for dropship products integrate with shopify and others]
[ ] [dropsearch] — [dropship researcher. spy on competitors and come up with a business gameplan in full English describing the entire operation.]
[ ] [dropshipping suite builder] — [description]
[ ] [dropstore] — [dropshipping niche or superstore builder and website integration. choose to make compatible with shopify or others if you want.]

[ ] [pairenv] — [environment enabling the pairing of real world hardware to then assign it to software and send and receive commands and translate English to the necessary format to access the tool]
[ ] [extraction] — [turn source material from summarizer tool into a "recipe" or specific step by step sequences and for potential specific skill extraction. Enable button that save's skill.  requires:summarizer_tool]
[ ] [quant developing program for prediction markets, sports, events, weather markets,etc ] — [[lock]Using high level mathematics like Hawkes Process and understanding  market maker spread costs and order flow intensity and branching for market making strategy. Adjusting spread based on VPIN and latency arbitrage. create a suite to run simulations and calculate sharpe ratio of prediction markets based on quant math. Expected value, bayes theorem, kelly criterion, base rate (true positive vs false positive), KL divergence, LMSR. Betting using oversold RSI and other TA like MACD for line changes. Make it possible to plug in LLM or API key or local AI and ask the AI about the setup and give it the harness/ tools it needs to interact with the tool and explain everything. Understand the formulas used by vegas and others to make markets and balance books and offer action to do so. Understand greeks, etc. ]
[ ] [Ranker architecture] — [Every tool run through this wrapper enables you to choose weight/preferences or rank or score. The idea is the ranker architecture can accumulate value to determine tastes. This could be provided and integrated with machine learning for various purposes.]

[ ] [brain download] — [Tim Ferriss Meta Learning accelerated Learning inspired "coursera/udemy course builder" that formats the course using deconstruction, selection, sequencing, stakes and compression, encoding, and frequency to optimize the learning experience while also providing quality scripts for video creation for Udemy, with PDF and other tools. The tool is for course designers to make quality courses but it doesn't need to build out the full video training itself. Also should reccomend other resources including entertainment for total immersion and osmosis like fictional enjoyment movies and books as well as the actual non fiction resources f extraction of information.]
[ ] [skillify] — [turn recipe from extraction into claude skill. Also ability to convert claude skill to JSON file for other LLM. "system_prompt": "..." "functions": [ ... ] "examples": [ ... ]. Also, ability to export JSON file or claude skill. requires:summarizer_tool, extraction]
[ ] [skill ninja] — [container and public facing tool for skillify, extraction, summarizer tool. requires:summarizer_tool, extraction, skillify]

[ ] [AgentFlow Dropship] — [Autonomous drop shipping orchestration platform that lets you describe your entire operation and it builds, runs and scales workflows for you using agentic AI.]
[ ] [agentic mirroring game] — [game where you input data and with that can build an empire. When agentic mirroring is turned on and everything is paired, your actions are mirrored in real life and integrated with agentic commerce, robots, etc so that the epire you build in the gaming environment happens in real life. requires:pairenv]

[ ] Agent observability dashboard — Build a real-time dashboard that tracks agent execution metrics (steps taken, LLM calls, costs, errors, duration) across all running pipeline projects with alerting on anomalies.

[ ] Automated SEO content factory — Combines ai_author_suite with dropship/service/ecommerce autoSEO autometa to generate SEO-optimized product descriptions and blog content at scale for ecommerce stores. requires: ai_author_suite, 
[ ] [babble] — [[lock] Duolingo style language learning. Find the most common phrases the uses the most common words across multiple language swiping across to understand. Learn in order of usage to learn in order of value that the sentence and question has. jam pack the top 2000 words and before that the top 1500 and top 1000 and top 500 and so on but also the common formats and questions and answers in every day language. use accelerating learning techniques to teach it best. use memory palace tricks]
[ ] Book content repurposer — Add a module to the AI author suite that takes a completed book and auto-generates blog posts, social media threads, newsletter articles, and course outlines from chapters. requires: ai_author_suite
[ ] [unweb] — [This tool should unmask the connections of any news story. loosely based on the "mike benz filter" on the world, "if you know what is reported you know anything, but if you know who is reporting, you know everything. This connects people to organizations they work with, the think tanks they or their organization is a part of, who finances them, how NGOs and other entities connect together. This should also look for political biases and follow the money. It should scan for similar agenda based talking point phrasing going on around the same time within the article and strike through the text and on hover over says why this word or phrase is likely propaganda. ]
[ ] [VASTAI instance initializer] — [User sets up preset commands for a vast AI terminal, time between commands, number of instances into a database, selects all the settings and so on and clicks run and it initializes according to the user selections]
[ ] Video content SEO engine — Combines dropship/service/ecommerce autoSEO autometa with youtube workflow tool to generate SEO titles, descriptions, tags, and transcripts for YouTube video catalogs at scale. requires: dropship/service/ecommerce. autoSEO autometa, youtube workflow tool
[ ] [video GAN] — [[lock] GAN and RL training. one determines if the video is real or fake, the other adapts video pow to generate fake from a real video and presents one or the other and both sides improve. requires:video_pow]
[ ] [video pow] — [[lock] convert description of video to video from the video alone. can use or modify existing tools on github.]
[ ] [video recipe] — [[lock] deconstructs video action to a "recipe" in the sense of describing how to perform a task. For example of the video shows a man lumberjacking and chopping a tree it will contained detailed description that an LLM agent could hopefully train on and learn from or convert the dscription as needed]


[ ] [AI Author Audiobook Integration] — Add automated narration synthesis and dynamic cover art animation to the suite. requires:ai_author_suite
[ ] [AI Author Docs Platform] — Merge ai_author_suite and docsai_documentation_generator to publish technical books automatically. requires:ai_author_suite, docsai_documentation_generator
[ ] [AI Screenplay Writer] — Automated scriptwriting assistant that handles plot structure, dialogue generation, and formatting. requires:ai_author_suite

[ ] API mock server generator — Tool that reads an OpenAPI/Swagger spec and generates a fully functional mock API server with configurable response delays, random data generation, and request logging. ai_author_suite
[ ] [Automated Dependency Resolver] — Tool that tracks cross-project requirements and automatically syncs version constraints.
dropship/service/ecommerce. autoSEO autometa
[ ] [Autonomous Web Vulnerability Scanner] — Continuous security tool that automatically probes and patches public web assets.


[ ] [Data Docs Generator] — Merge docsai_documentation_generator and csv_analyzer to auto-generate schema and API documentation.
[ ] [DFS arb] — [[lock] daily fantasy sports formula for arbitrage and mispriced lines, bonus and promo hunting and algorithmic entering if there is value added proposition. Across book arbitrage.]

[ ] Email attachment to CSV pipeline — Connector that extracts CSV attachments from emails processed by the email tool, runs them through the CSV analyzer, and routes results to a configured folder or webhook. requires: email_tool, csv_analyzer

[ ] [Figma to Mobile App Generator] — AI pipeline that converts design mockups into production-ready cross-platform code.
[ ] [Interactive Fiction Engine] — Combine ai_author_suite and advantage_player_cardgame_simulator_training for branching narrative games.
[ ] [JSON skill] — [This tool is for enabling local AI to run claude skills as JSON files in the format "system_prompt": "..." "functions": [ ... ] "examples": [ ... ]. Any claude code skill converted into a JSON file should be able to run. Should contain a loader, dispatcher and a runtime that injects it into the model]
[ ] LLMClient bridge for AI Author — Adapter that plugs the LLMClient protocol from drop_servicing_tool into the AI author suite so all modules share the same LLM interface and caching layer. requires: drop_servicing_tool, ai_author_suite
[ ] [Local Knowledge Graph Builder] — Privacy-focused desktop app that connects personal notes, files, and bookmarks.
[ ] Local weather dashboard CLI — Python CLI that fetches local weather data from OpenWeatherMap, displays current conditions and 7-day forecast in terminal with color-coded alerts for severe weather.
[ ] [Manuscript to Docs Bridge] — Formatter that transforms ai_author_suite output into docsai_documentation_generator compatible specs.
[ ] Meeting notes auto-summarizer — Tool that takes raw meeting transcripts or audio recordings, identifies action items, decisions, and key topics, and outputs a structured summary with assignees and deadlines.
[ ] [newsletter /online profit environment for LLM RL training and sims.] — []

[ ] [PDF Schema Analyzer] — CLI tool that extracts and validates complex structures from unstructured PDF documents.
[ ] Personal finance tracker CLI — Python CLI that imports bank CSV transactions, categorizes them by merchant patterns, generates monthly budget reports, and alerts on spending anomalies.
[ ] [Pipeline Observability Dashboard] — Real-time visualization of agent execution, costs, and failure rates across all projects.
[ ] Project dependency graph visualizer — Tool that reads all project workspace files and MANIFEST.json to generate a visual dependency graph showing which projects depend on which shared tools and ideas.


[ ] [Real-Time Market Predictor] — Prediction engine that tracks financial sentiment and forecasts asset price movements.
[ ] Real estate listing analyzer — CLI tool that pulls property data from public APIs, analyzes price trends, neighborhood metrics, and generates comparative market reports in CSV or PDF. requires: Zillow
[ ] [research1] — [user provides a topic, then this tool goes through highly credible sources to create a well sourced report User can select "informational" or "recipe" if it's a reciepe it's structured as how to do a particular thing. Ability to choose LLM for response. sources like ARXIV, pub med, wikipedia,crossref, semantic scholar, web of science, scopus, jstor,ssrn,dot gov government domains, biorxiv,medrxiv,openreview,papers with code,nber,fred,data.gov,nist,iso,acm digital library, ieee xplore, rand corporation, bookings institution,,]
[ ] [research2] — [user provides a topic, then ]
[ ] [research3] — [description]
[ ] Resume-to-job-applicant automator — Combines drop_servicing_tool with fiverr job automation tool to analyze job listings, auto-generate tailored applications, and manage bulk outreach campaigns. requires: drop_servicing_tool, fiverr job automation tool
[ ] Resume and cover letter builder — Python tool that takes a job description and candidate profile, then generates tailored resumes and cover letters using templating and LLM-assisted rewriting. requires: drop_servicing_tool
[ ] [RL for dropshipping] — [train on cloning successful dropshipping first and then running RL. source deep rl zoo or others from github. use profit, traffic, revenue per cost and autoresearch solutions in simulated market place using MiroFish and then roll out and calibrate to real. Assess risk and manage using 10% kelly criterion strategy based on budget.]
[ ] [SaaS Pricing Optimizer] — Automated tool that analyzes competitor pricing and recommends optimal subscription tiers.
[ ] [SEC to CSV Bridge] — Pipeline that converts raw SEC filing XML into standardized CSVs for csv_analyzer ingestion.
[ ] [See BS] — [news BS filter based on several scott adams techniques. for example the "Scott Alexander rule", the Gellman Amnesia, the suggestion that "who" reports is just as important as what.]
[ ] Shared LLM cost tracker — Add a cost-tracking middleware to the LLMClient protocol that logs every LLM call's token usage and cost across all projects, with monthly budget alerts and per-project breakdowns.
[ ] [Simulator Result Aggregator] — Pipeline that collects and normalizes monte_carlo training outputs across multiple game simulators.

[ ] Smart email-to-SOP executor — Combines email_tool with drop_servicing_tool to automatically parse incoming emails, extract task requirements, and trigger SOP-based agentic workflows for execution. requires: email_tool, drop_servicing_tool
[ ] [social media management/etc] — [airtable like platform or system for managing social media posts and accounts. AI can help generate content and schedule posts and scale]
[ ] SOP marketplace — Add a marketplace module to the drop servicing tool where users can publish, discover, and license SOPs with version control, ratings, and one-click import. requires: drop_servicing_tool
[ ] SOP output to YouTube content feed — Bridge that takes SOPStep outputs from the drop servicing tool and formats them into YouTube video scripts, titles, and thumbnail text via the youtube workflow tool pipeline. requires: drop_servicing_tool, youtube workflow tool
[ ] [sports/event bet front runner] — [[lock]Use AI technology to front-run polymarket and DFS. read, parse and adjust. Leverage the broadcast delays and parse raw api data from stadiums and more directly. Use RL and train prediction algorithms to predict ahead as well if necessary with high confidence. Additional tools for scalping on news release.]
[ ] [Startup Compliance Scanner] — Automated checklist generator that maps startup data to SOC2 and GDPR requirements.
[ ] [Technical Whitepaper Generator] — AI system that researches, outlines, and drafts professional engineering documentation.
[ ] [Test Coverage Mutator] — Automated suite that generates mutation tests and enforces quality thresholds across the pipeline.
[ ] Test fixture generator — Build a tool that generates realistic test fixtures (CSV files, JSON payloads, mock API responses, sample documents) for any project by reading its existing test patterns and schemas.
[ ] [Universal LLM Router] — Adapter that routes requests across llmclient providers with automatic fallback and load balancing.

[ ] Card composition calculator — Add a deck composition analyzer to the cardgame simulator that calculates card counting advantage, true count, and running count across shuffle patterns. requires: advantage_player_cardgame_simulator_training
[ ] Card game training course platform — Combines advantage_player_cardgame_simulator_training with tim ferriss learning tool to create interactive poker and blackjack training courses with spaced repetition and progress tracking. requires: advantage_player_cardgame_simulator_training, tim ferriss learning tool
[ ] [Card Game Variant Expansion] — Add Texas Hold'em and Omaha variants with AI opponent modeling to the simulator.
[ ] Cardgame simulator output to learning tool — Bridge that exports Monte Carlo training results and strategy metrics from the cardgame simulator into the tim ferriss learning tool format for spaced repetition practice decks. requires: advantage_player_cardgame_simulator_training, tim ferriss learning tool
[ ] Code review diff summarizer — CLI tool that reads git diff output, summarizes changes by file and function, flags potential issues, and generates a human-readable review briefing.
[ ] [Config Schema Validator] — Linter that validates pipeline YAML definitions against typed schemas before execution.
[ ] Contract clause extractor — PDF and DOCX parser that identifies and extracts key contract clauses (termination, liability, NDAs) into a structured searchable database with export options.
[ ] Cross-project code linter — CLI tool that runs consistent linting, type checking, and import analysis across all workspace projects, enforcing a shared style guide and flagging cross-project API mismatches.
[ ] CSV data pipeline builder — Extend CSV analyzer with a visual pipeline builder that chains transformations (filter, join, pivot, aggregate) between multiple CSV files with export to SQL or JSON. requires: csv_analyzer


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

- [ ] **[subgoal generator]** — [General-purpose LLM goal decomposition engine. Takes any high-level goal ("build a house", "make $10k/month", "learn Spanish") and uses an LLM to produce an ordered list of subgoals with dependencies. Each subgoal is formatted as a pipeline idea entry and injected into master_ideas.md for the runner to execute. Operates on any domain: robotics, software, business, learning. The agent's hypothesis and goal-creation layer — enables recursive autonomous expansion of any objective into buildable sub-tasks. The runner processes each subgoal through the normal executor/validator/critic cycle.]

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

