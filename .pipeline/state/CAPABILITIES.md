# Pipeline capabilities (generated)

Updated: 2026-05-23T19:29:37.117759+00:00

Regenerate: `python scripts/build_capability_registry.py`

Database: `.pipeline/state/capability_registry.sqlite`

Use `--legacy` on the runner to disable capability injection (pre-registry behavior).

---

## pipeline_script

- **extract.py** (`pipeline_extract`) — _verified_
  - Zip pipeline state for cloud transfer
  - run: `python extract.py`
  - example: `python extract.py --help`

- **health_check.py** (`pipeline_health_check`) — _verified_
  - Cross-project health check and --fix
  - run: `python health_check.py`
  - example: `python health_check.py --help`

- **import_zip.py** (`pipeline_import_zip`) — _verified_
  - Import pipeline_extract zip into local state
  - run: `python import_zip.py`
  - example: `python import_zip.py --help`

- **pipeline/grok_sidecar.py** (`pipeline_grok_sidecar`) — _verified_
  - Grok validation sidecar CLI
  - run: `python pipeline/grok_sidecar.py`
  - example: `python pipeline/grok_sidecar.py --help`

- **pipeline/runner.py** (`pipeline_runner`) — _verified_
  - Main multi-agent pipeline orchestrator
  - run: `python pipeline/runner.py`
  - example: `python pipeline/runner.py --help`

- **reset_budget_exceeded.py** (`pipeline_reset_budget`) — _verified_
  - Reset budget_exceeded projects and polish queue
  - run: `python reset_budget_exceeded.py`
  - example: `python reset_budget_exceeded.py --help`

## project

- **AI movie generation suite** (`ai_movie_generation_suite`) — _verified_
  - suite that enables save the cat style screenplay writing, prompts for generating images/storyboard, prompts for describing characters, enable import of character into UE5 (or others) and integration w
  - run: `python -m ai_movie_gen_suite.cli:main`
  - example: `python -m ai_movie_gen_suite.cli:main`

- **AI movie generation suite 2** (`ai_movie_generation_suite_2`) — _verified_
  - core suite. API surface, data models, file formats for movie generation.

- **Academic Thesis Writer** (`academic_thesis_writer`) — _verified_
  - AI-assisted research paper generator with citation management, literature review synthesis, and academic formatting modules.

- **AgentFlow Drophip** (`agentflow_drophip`) — _verified_
  - Autonomous drop shipping orchestration platform that lets you describe your entire operation and it builds, runs and scales workflows for you using agentic AI.
  - run: `python -m agentflow_drophip.cli:main`
  - example: `python -m agentflow_drophip.cli:main`

- **Audiobook Script Pipeline** (`audiobook_script_pipeline`) — _verified_
  - Combine the AI Author Suite with the transcript extractor to automatically convert manuscripts into formatted audio scripts with pacing markers.
  - run: `python .pipeline/projects/audiobook_script_pipeline/workspace/cli.py`
  - example: `python .pipeline/projects/audiobook_script_pipeline/workspace/cli.py --help`

- **AutomatedClientOps Manager** (`automatedclientops_manager`) — _verified_
  - Combine the drop-servicing SOP executor with the email tool to handle client communication, file delivery, and invoice generation autonomously.
  - run: `python -m manager:main`
  - example: `python -m manager:main`

- **BudgetFlow Tracker System** (`budgetflow_tracker_system`) — _verified_
  - Develop a local-first personal finance app that categorizes bank transactions, forecasts cash flow, and alerts on budget deviations.

- **CSV Analyzer** (`csv_analyzer`) — _verified_
  - Build a Python CLI tool that reads a CSV file and prints summary statistics (row count, column names, min/max/mean for numeric columns, null counts). Include argparse, error handling for missing files
  - run: `python -m csv_analyzer.cli.main:cli`
  - example: `python -m csv_analyzer.cli.main:cli`

- **CSV Data Pipeline Builder** (`csv_data_pipeline_builder`) — _verified_
  - run: `python .pipeline/projects/csv_data_pipeline_builder/workspace/cli.py`
  - example: `python .pipeline/projects/csv_data_pipeline_builder/workspace/cli.py --help`

- **Chronovision** (`chronovision`) — _verified_
  - Using software that can create full fidelity 3d worlds like Google Genie and others and use some kind of tracking tech and IOT and RL to produce measurements about the actual world, create worlds seco

- **Chronovision autoresearch adapter** (`chronovision_autoresearch_adapter`) — _verified_
  - adaptor for chronovision. tracks research papers across arxiv, openreview, bioRxiv, NASA ADS, NBER,FRED,OECD, predicts paper and impact it will have. Also tracks crunchbase, pitchbook, cb insights, y 

- **Chronovision2** (`chronovision2`) — _verified_
  - Using software that can create full fidelity 3d worlds like Google Genie and others and use some kind of tracking tech and IOT and RL to produce measurements about the actual world, create worlds seco

- **DFS arb** (`dfs_arb`) — _verified_
  - daily fantasy sports formula for arbitrage and mispriced lines, bonus and promo hunting and algorithmic entering if there is value added proposition.
  - run: `python .pipeline/projects/dfs_arb/workspace/cli.py`
  - example: `python .pipeline/projects/dfs_arb/workspace/cli.py --help`

- **DependencyVuln Code Scanner** (`dependencyvuln_code_scanner`) — _verified_
  - Create a CLI utility that audits project dependency trees, cross-references CVE databases, and outputs prioritized remediation reports.
  - run: `python -m depvuln.cli:cli`
  - example: `python -m depvuln.cli:cli`

- **DocsAI Documentation Generator** (`docsai_documentation_generator`) — _verified_
  - Create an AI-powered technical documentation assistant that structures API specs, generates READMEs, and maintains versioned changelogs.
  - run: `python -m docsai.cli:main`
  - example: `python -m docsai.cli:main`

- **Drop=Gentic** (`dropgentic`) — _verified_
  - Dropshipping and agentic commerce planner
  - run: `python -m dropgentic.cli:main`
  - example: `python -m dropgentic.cli:main`

- **Dynamic Pricing Integrator** (`dynamic_pricing_integrator`) — _verified_
  - Add competitive price tracking and automated discount rule engines to the e-commerce SEO tool for real-time inventory and margin optimization.

- **EcommerceCatalog Metadata Optimizer** (`ecommercecatalog_metadata_optimizer`) — _verified_
  - Merge the autoSEO tool with the CSV Analyzer to automatically audit product catalogs, optimize metadata, and export enriched spreadsheets.

- **FFO** (`ffo`) — _verified_
  - Football Financial Optimizer. Integration with the above with financial model for valuing players vs salary cap including pool of available free agents. Ability to adjust strategy given additions/subt
  - run: `python .pipeline/projects/ffo/workspace/cli.py`
  - example: `python .pipeline/projects/ffo/workspace/cli.py --help`

- **File Deduplicator** (`file_deduplicator`) — _verified_
  - Build a Python script that scans a directory recursively, finds duplicate files by MD5 hash, and prints a report of duplicates grouped by hash. Optionally deletes duplicates with a --delete flag (with

- **Football NFL draft and recruit optimizer** (`football_nfl_draft_and_recruit_optimizer`) — _verified_
  - Integration with the above for NFL draft for same purposes and integration with both free agency and the draft. (or for recruiting) requir

- **Football simulator** (`football_simulator`) — _verified_
  - --nfl/highschool/college regulation field size physics engine. reinforcement learning to optimize success rate vs standard NFL play calls and adversarial self play.

- **Forensic** (`forensic`) — _verified_
  - Forensic accounting suite for detecting corporate fraud, predicting earnings, understanding capital flows,etc. Ability to comb through data imported from SEC importer and run a variety of methods to d
  - run: `python .pipeline/projects/forensic/workspace/cli.py`
  - example: `python .pipeline/projects/forensic/workspace/cli.py --help`

- **Forensic accounting suite** (`forensic_accounting_suite`) — _verified_
  - OSINT for corporate tracking. Tracking shipping manifests, procurement data, government contract databases, corporate registry data. Correlating companies on maps/satellites to SEC filings. Cross corr

- **Forensic2** (`forensic2`) — _verified_
  - Forensic accounting suite for detecting corporate fraud, predicting earnings, understanding capital flows,etc. Ability to comb through data imported from SEC importer and run a variety of methods to d

- **FreelanceTask Manager System** (`freelancetask_manager_system`) — _verified_
  - Merge the drop-servicing SOP engine with the job automation tool to streamline proposal generation, client matching, and contract signing.
  - run: `python .pipeline/projects/freelancetask_manager_system/workspace/cli.py`
  - example: `python .pipeline/projects/freelancetask_manager_system/workspace/cli.py --help`

- **Human-in-the-Loop Reviewer** (`human_in_the_loop_reviewer`) — _verified_
  - Integrate a manual approval checkpoint into the drop-servicing SOP executor, allowing agents to pause execution until a human validates outputs.
  - run: `python .pipeline/projects/human_in_the_loop_reviewer/workspace/cli.py`
  - example: `python .pipeline/projects/human_in_the_loop_reviewer/workspace/cli.py --help`

- **Invoice processor** (`invoice_processor`) — _verified_
  - Tool that scans email attachments for invoices, extracts line items and totals via OCR or text parsing, and organizes them into a searchable ledger with CSV export
  - run: `python .pipeline/projects/invoice_processor/workspace/cli.py`
  - example: `python .pipeline/projects/invoice_processor/workspace/cli.py --help`

- **JSON Diff Tool** (`json_diff_tool`) — _verified_
  - Build a Python CLI that compares two JSON files and prints a human-readable diff showing added, removed, and changed keys/values. Handle nested objects and arrays. Include unit tests covering edge cas
  - run: `python .pipeline/projects/json_diff_tool/workspace/cli.py`
  - example: `python .pipeline/projects/json_diff_tool/workspace/cli.py --help`

- **JSON Schema Profiler** (`json_schema_profiler`) — _verified_
  - Develop a CLI tool that scans JSON or Parquet datasets, infers schemas, detects anomalies, and outputs standardized validation rules.
  - run: `python -m json_schema_profiler.cli:app`
  - example: `python -m json_schema_profiler.cli:app`

- **JSON skill** (`json_skill`) — _verified_
  - This tool is for enabling local AI to run claude skills as JSON files in the format "system_prompt": "..." "functions": [ ... ] "examples": [ ... ]. Any claude code skill converted into a JSON file sh

- **Logistics CSV Optimizer** (`logistics_csv_optimizer`) — _verified_
  - CLI tool for importing shipment manifests, calculating routing costs, and generating optimized delivery schedules
  - run: `python .pipeline/projects/logistics_csv_optimizer/workspace/cli.py`
  - example: `python .pipeline/projects/logistics_csv_optimizer/workspace/cli.py --help`

- **ManuscriptData Analyzer System** (`manuscriptdata_analyzer_system`) — _verified_
  - Merge the AI Author Suite with the CSV Analyzer to track reader demographics, sales metrics, and content performance across published books.
  - run: `python -m manuscriptdata_analyzer.cli:cli`
  - example: `python -m manuscriptdata_analyzer.cli:cli`

- **Markdown to HTML Converter** (`markdown_to_html_converter`) — _verified_
  - Build a Python CLI that converts a markdown file to a standalone HTML file with basic CSS styling. Support headers, bold, italic, code blocks, and links. Include unit tests for each element type.
  - run: `python .pipeline/projects/markdown_to_html_converter/workspace/cli.py`
  - example: `python .pipeline/projects/markdown_to_html_converter/workspace/cli.py --help`

- **Market Strategy Backtester** (`market_strategy_backtester`) — _verified_
  - Build a Monte Carlo backtesting engine for algorithmic trading strategies using historical price data and risk-adjusted metrics.
  - run: `python .pipeline/projects/market_strategy_backtester/workspace/cli.py`
  - example: `python .pipeline/projects/market_strategy_backtester/workspace/cli.py --help`

- **Movie idea generator** (`movie_idea_generator`) — _verified_
  - generate simple movie ideas
  - run: `python .pipeline/projects/movie_idea_generator/workspace/cli.py`
  - example: `python .pipeline/projects/movie_idea_generator/workspace/cli.py --help`

- **Movie/Series auto-tracker** (`movieseries_auto_tracker`) — _verified_
  - Tool with multiple features. 1) enables you to "continue" watching and load whatever streaming service. 2)Enables you to search across all streaming platforms. 3)Enables a centralized platform for vie

- **Multi-Format Export Engine** (`multi_format_export_engine`) — _verified_
  - Expand the AI Author Suite to natively export finished manuscripts to EPUB, MOBI, and print-ready PDF with custom typography and margins.

- **NDA Contract Generator** (`nda_contract_generator`) — _verified_
  - Create a CLI tool that drafts jurisdiction-specific non-disclosure agreements using customizable clauses and AI-assisted legal phrasing.
  - run: `python .pipeline/projects/nda_contract_generator/workspace/cli.py`
  - example: `python .pipeline/projects/nda_contract_generator/workspace/cli.py --help`

- **OSINT corp** (`osint_corp`) — _verified_
  - OSINT for corporate tracking. Uses SEC importer and forensic for data. Thi should also have methods to extract and tracking legal public available shipping manifests, procurement data, government cont
  - run: `python .pipeline/projects/osint_corp/workspace/cli.py`
  - example: `python .pipeline/projects/osint_corp/workspace/cli.py --help`

- **PantryChef Meal Planner** (`pantrychef_meal_planner`) — _verified_
  - Design a meal planning tool that ingests pantry inventory, suggests recipes, generates shopping lists, and tracks nutritional macros.

- **RL for dropshipping** (`rl_for_dropshipping`) — _verified_
  - train on cloning successful dropshipping first and then running RL. source deep rl zoo or others from github. use profit, traffic, revenue per cost and autoresearch solutions in simulated market place

- **Ranker architecture** (`ranker_architecture`) — _verified_
  - Every tool run through this wrapper enables you to choose weight/preferences or rank or score. The idea is the ranker architecture can accumulate value to determine tastes. This could be provided and 

- **Real Estate Listing Analyzer** (`real_estate_listing_analyzer`) — _verified_
  - run: `python .pipeline/projects/real_estate_listing_analyzer/workspace/cli.py`
  - example: `python .pipeline/projects/real_estate_listing_analyzer/workspace/cli.py --help`

- **ReviewPulse Aggregator** (`reviewpulse_aggregator`) — _verified_
  - Build a service that monitors local business reviews across platforms, analyzes sentiment, and auto-generates response drafts for owners.

- **Robot primitive vocabulary schema** (`robot_primitive_vocabulary_schema`) — _verified_
  - [goal:bootstrap_robot_training:b001] Create a JSON schema and Python dataclasses for robot motion primitives. Define atomic primitives (grasp, place, slide, push, lift, rotate) with parameters: positi

- **Rule-Based Triage Engine** (`rule_based_triage_engine`) — _verified_
  - Extend the email tool with a visual rule builder that auto-filters, tags, and routes incoming messages to specific CRM pipelines based on content analysis.

- **SEC importer** (`sec_importer`) — _verified_
  - Ability to import all the latest data of SEC filings for US companies.
  - run: `python -m sec_importer.cli:main`
  - example: `python -m sec_importer.cli:main`

- **SEC importer2** (`sec_importer2`) — _verified_
  - -- Ability to import all the latest data of SEC filings for US companies.
  - run: `python -m sec_importer.cli:cli`
  - example: `python -m sec_importer.cli:cli`

- **SEO tool** (`seo_tool`) — _verified_
  - [SEO tool]
  - run: `python .pipeline/projects/seo_tool/workspace/cli.py`
  - example: `python .pipeline/projects/seo_tool/workspace/cli.py --help`

- **SOPData Ingestion Bridge** (`sopdata_ingestion_bridge`) — _verified_
  - Build a bridge API that converts CSV outputs from the CSV Analyzer into structured SOP inputs for the drop-servicing tool,
  - run: `python -m sopdata_ingestion_bridge.__main__:main`
  - example: `python -m sopdata_ingestion_bridge.__main__:main`

- **See BS** (`see_bs`) — _verified_
  - news BS filter based on several scott adams techniques. for example the "Scott Alexander rule", the Gellman Amnesia, the suggestion that "who" reports is just as important as what.
  - run: `python -m see_bs.__main__:main`
  - example: `python -m see_bs.__main__:main`

- **Sports Betting Strategy Simulator** (`sports_betting_strategy_simulator`) — _verified_
  - Monte Carlo engine for training optimal betting strategies across sports markets.

- **URL Health Checker** (`url_health_checker`) — _verified_
  - Build a Python CLI that reads a list of URLs from a text file, sends HEAD requests (with timeout), and outputs a report showing status code, response time, and whether each URL is up or down. Include 
  - run: `python .pipeline/projects/url_health_checker/workspace/cli.py`
  - example: `python .pipeline/projects/url_health_checker/workspace/cli.py --help`

- **VASTAI instance initializer** (`vastai_instance_initializer`) — _verified_
  - User sets up preset commands for a vast AI terminal, time between commands, number of instances into a database, selects all the settings and so on and clicks run and it initializes according to the u
  - run: `python .pipeline/projects/vastai_instance_initializer/workspace/cli.py`
  - example: `python .pipeline/projects/vastai_instance_initializer/workspace/cli.py --help`

- **VR practice mode.** (`vr_practice_mode`) — _verified_
  - [VR practice mode.]

- **VR room for stock ticker scanning.** (`vr_room_for_stock_ticker_scanning`) — _verified_
  - [VR room for stock ticker scanning.]

- **Youtube studio** (`youtube_studio`) — _verified_
  - [multistep studio for building youtube videos. story generator or video commercial to video or movie format save cat format video format or useful youtube informational format. Title and thumbnail and
  - run: `python .pipeline/projects/youtube_studio/workspace/cli.py`
  - example: `python .pipeline/projects/youtube_studio/workspace/cli.py --help`

- **Zillow** (`zillow`) — _verified_
  - [tool using redfin/zillow to trigger criteria alert to phone/email.]
  - run: `python .pipeline/projects/zillow/workspace/cli.py`
  - example: `python .pipeline/projects/zillow/workspace/cli.py --help`

- **agentic mirroring game** (`agentic_mirroring_game`) — _verified_
  - game where you input data and with that can build an empire. When agentic mirroring is turned on and everything is paired, your actions are mirrored in real life and integrated with agentic commerce, 
  - run: `python .pipeline/projects/agentic_mirroring_game/workspace/cli.py`
  - example: `python .pipeline/projects/agentic_mirroring_game/workspace/cli.py --help`

- **ai author suite** (`ai_author_suite`) — _verified_
  - [niche/topic research, keyword research,book outliner, chapter developer, chapter outliner, detail fill in, deep editor restructure format, cover designer, book cover designer, etc]

- **babble** (`babble`) — _verified_
  - Duolingo style language learning. Find the most common phrases across multiple languages. Learn in order of usage value. Use accelerating learning techniques and memory palace tricks.
  - run: `python .pipeline/projects/babble/workspace/cli.py`
  - example: `python .pipeline/projects/babble/workspace/cli.py --help`

- **beatsheet generator** (`beatsheet_generator`) — _verified_
  - Save the cat beatsheet from movie idea
  - run: `python .pipeline/projects/beatsheet_generator/workspace/cli.py`
  - example: `python .pipeline/projects/beatsheet_generator/workspace/cli.py --help`

- **book researcher** (`book_researcher`) — _verified_
  - find the book people aren't writing but that people want. scan reviews, quora, etc from top selling information books, pdfs, video courses, etc for reviews that are like "this book was good but I wish
  - run: `python .pipeline/projects/book_researcher/workspace/cli.py`
  - example: `python .pipeline/projects/book_researcher/workspace/cli.py --help`

- **brain download** (`brain_download`) — _verified_
  - Tim Ferriss Meta Learning accelerated Learning inspired "coursera/udemy course builder" that formats the course using deconstruction, selection, sequencing, stakes and compression, encoding, and frequ

- **consistent character developer** (`consistent_character_developer`) — _verified_
  - consistent characters using Kling AI or similar. require

- **consistent scene developer** (`consistent_scene_developer`) — _verified_
  - scene describer integrating characters. require

- **drop servicing tool** (`drop_servicing_tool`) — _verified_
  - [store SOPs and workflows and enable LLM scaling and agentic scaling for perfoming bulk tasks.]
  - run: `python .pipeline/projects/drop_servicing_tool/workspace/cli.py`
  - example: `python .pipeline/projects/drop_servicing_tool/workspace/cli.py --help`

- **dropify** (`dropify`) — _verified_
  - dropshipping shopify clone

- **droppain** (`droppain`) — _verified_
  - dropship marketing campaign. plan and implement a marketing campaign for dropship products integrate with shopify and others
  - run: `python .pipeline/projects/droppain/workspace/cli.py`
  - example: `python .pipeline/projects/droppain/workspace/cli.py --help`

- **dropsearch** (`dropsearch`) — _verified_
  - dropship researcher. spy on competitors and come up with a business gameplan in full English describing the entire operation.
  - run: `python -m src.cli:main`
  - example: `python -m src.cli:main`

- **dropship/service/ecommerce. autoSEO autometa** (`dropshipserviceecommerce_autoseo_autometa`) — _verified_
  - [dropship/service/ecommerce. autoSEO autometa]
  - run: `python -m dropship_seo.cli:cli`
  - example: `python -m dropship_seo.cli:cli`

- **dropstore** (`dropstore`) — _verified_
  - dropshipping niche or superstore builder and website integration. choose to make compatible with shopify or others if you want.

- **email tool** (`email_tool`) — _verified_
  - [email processing, rules, systems, agentic instruction, systems, automations. TOol for automating the searching in emails and attachments to follow rules and organize into folders according to these r
  - run: `python .pipeline/projects/email_tool/workspace/cli.py`
  - example: `python .pipeline/projects/email_tool/workspace/cli.py --help`

- **extraction** (`extraction`) — _verified_
  - turn source material from summarizer tool into a "recipe" or specific step by step sequences and for potential specific skill extraction. Enable button that save's skill
  - run: `python .pipeline/projects/extraction/workspace/cli.py`
  - example: `python .pipeline/projects/extraction/workspace/cli.py --help`

- **fiverr job automation tool** (`fiverr_job_automation_tool`) — _verified_
  - [create automated tasks on fiverr.]

- **game/agent** (`gameagent`) — _verified_
  - [game/agent]
  - run: `python .pipeline/projects/gameagent/workspace/cli.py`
  - example: `python .pipeline/projects/gameagent/workspace/cli.py --help`

- **idea** (`idea`) — _verified_
  - amazon audiobook to pdf converter

- **job automation tool** (`job_automation_tool`) — _verified_
  - [job automation tool]
  - run: `python .pipeline/projects/job_automation_tool/workspace/cli.py`
  - example: `python .pipeline/projects/job_automation_tool/workspace/cli.py --help`

- **memory system** (`memory_system`) — _verified_
  - [moonwalking with Einstein memory system. musical wheel visalizer generator for decks of cards and numbers and others.

- **newsletter /online profit environment for LLM RL training and sims.** (`newsletter_online_profit_environment_for_llm_rl_training_and_sims`) — _verified_
  - [newsletter /online profit environment for LLM RL training and sims.]

- **pairenv** (`pairenv`) — _verified_
  - environment enabling the pairing of real world hardware to then assign it to software and send and receive commands and translate English to the necessary format to access the tool

- **player attribute library** (`player_attribute_library`) — _verified_
  - Integration for the Football tool above with ability to match with player attributes. requir
  - run: `python -m player_attribute_library.scripts.cli:main`
  - example: `python -m player_attribute_library.scripts.cli:main`

- **pocketknife of the internet** (`pocketknife_of_the_internet`) — _verified_
  - [new internet browser. acts like a windows/computer that you can access on a website and user interface where you can move windows within the browser around. Merges the computer's software with intern

- **podcast** (`podcast`) — _verified_
  - extract lessons from podcast.  Tool identifies from a podcast title or link to the overall page. fast whisper transcript->podcast->LLM process. prompt to find the lessons->repeat for the next podct in
  - run: `python .pipeline/projects/podcast/workspace/cli.py`
  - example: `python .pipeline/projects/podcast/workspace/cli.py --help`

- **quant developing program for prediction markets, sports, events, weather markets** (`quant_developing_program_for_prediction_markets_sports_events_weather_markets`) — _verified_
  - Using Hawkes Process and market maker spread costs. Sharpe ratio simulations. Expected value, bayes theorem, kelly criterion, KL divergence, LMSR. Betting using RSI, MACD for line changes.

- **research1** (`research1`) — _verified_
  - user provides a topic, then this tool goes through highly credible sources to create a well sourced report User can select "informational" or "recipe" if it's a reciepe it's structured as how to do a 
  - run: `python .pipeline/projects/research1/workspace/cli.py`
  - example: `python .pipeline/projects/research1/workspace/cli.py --help`

- **robot primitive vocabulary** (`robot_primitive_vocabulary`) — _verified_
  - Design document and shared library module defining ~25-30 canonical atomic robot action primitives. Locomotion: move_to, rotate_to, approach, retreat. Manipulation: grasp, release, push, pull, lift, p

- **scott adams bot/llm fine tuning** (`scott_adams_botllm_fine_tuning`) — _verified_
  - [scott adams bot/llm fine tuning]
  - run: `python -m sacbot.cli:main`
  - example: `python -m sacbot.cli:main`

- **skill ninja** (`skill_ninja`) — _verified_
  - container and public facing tool for skillify, extraction, summarizer tool
  - run: `python .pipeline/projects/skill_ninja/workspace/cli.py`
  - example: `python .pipeline/projects/skill_ninja/workspace/cli.py --help`

- **skillify** (`skillify`) — _verified_
  - turn recipe from extraction into claude skill. Also ability to convert claude skill to JSON file for other LLM. "system_prompt": "..." "functions": [ ... ] "examples": [ ... ]. Also, ability to export
  - run: `python .pipeline/projects/skillify/workspace/cli.py`
  - example: `python .pipeline/projects/skillify/workspace/cli.py --help`

- **sports/event bet front runner** (`sportsevent_bet_front_runner`) — _verified_
  - Use AI to frontrun polymarket and DFS. Leverage broadcast delays and parse raw api data from stadiums. RL-trained prediction algorithms.

- **subgoal generator** (`subgoal_generator`) — _verified_
  - General-purpose LLM goal decomposition engine. Takes any high-level goal ("build a house", "make $10k/month", "learn Spanish") and uses an LLM to produce an ordered list of subgoals with dependencies.
  - run: `python -m subgoal_generator.__main__:main`
  - example: `python -m subgoal_generator.__main__:main`

- **summarizer tool** (`summarizer_tool`) — _verified_
  - [from a dashboard use an llm to summarize uploaded pdfs, youtube links, websites, blogs. user share links or download files and click summarize, or prompt agent what is needed from source material. Th

- **unweb** (`unweb`) — _verified_
  - This tool should unmask the connections of any news story. loosely based on the "mike benz filter" on the world, "if you know what is reported you know anything, but if you know who is reporting, you 
  - run: `python .pipeline/projects/unweb/workspace/cli.py`
  - example: `python .pipeline/projects/unweb/workspace/cli.py --help`

- **video GAN** (`video_gan`) — _verified_
  - GAN and RL training. one determines if the video is real or fake, the other adapts video pow to generate fake from a real video and presents one or the other and both sides improve. require
  - run: `python .pipeline/projects/video_gan/workspace/cli.py`
  - example: `python .pipeline/projects/video_gan/workspace/cli.py --help`

- **video babbel** (`video_babbel`) — _verified_
  - translate video to any language, and then parse dialogue, perform any translation, summarize content and answer questions in any language. require
  - run: `python .pipeline/projects/video_babbel/workspace/cli.py`
  - example: `python .pipeline/projects/video_babbel/workspace/cli.py --help`

- **video babbel enhanced** (`video_babbel_enhanced`) — _verified_
  - Language learning platform that ingests any video the user knows in their native language, transcribes it (Whisper), translates every line (LLM), scores each segment by frequency-vocabulary coverage a
  - run: `python .pipeline/projects/video_babbel_enhanced/workspace/cli.py`
  - example: `python .pipeline/projects/video_babbel_enhanced/workspace/cli.py --help`

- **video ingestor summary** (`video_ingestor_summary`) — _verified_
  - upload videos parse dialogue to text recognition, summarize content and answer questions model agnostic LLM harness
  - run: `python -m video_ingestor.cli:main`
  - example: `python -m video_ingestor.cli:main`

- **video langfake** (`video_langfake`) — _verified_
  - alter the lips and translate the video to any language. deepfake subtle changes to translate video to any language
  - run: `python .pipeline/projects/video_langfake/workspace/cli.py`
  - example: `python .pipeline/projects/video_langfake/workspace/cli.py --help`

- **video pow** (`video_pow`) — _verified_
  - convert description of video to video from the video alone. can use or modify existing tools on github.
  - run: `python .pipeline/projects/video_pow/workspace/videopow/cli.py`
  - example: `python .pipeline/projects/video_pow/workspace/videopow/cli.py --help`

- **video recipe** (`video_recipe`) — _verified_
  - deconstructs video action to a recipe in the sense of describing how to perform a task.
  - run: `python .pipeline/projects/video_recipe/workspace/cli.py`
  - example: `python .pipeline/projects/video_recipe/workspace/cli.py --help`

- **video recipe mu** (`video_recipe_mu`) — _verified_
  - Takes video_scribe structured scene descriptions and uses an LLM to extract an ordered sequence of atomic actions as a robot recipe. Output JSON: [{step, action, object, xyz_delta, duration_s, precond

- **video scribe** (`video_scribe`) — _verified_
  - translate a video to scene description, connecting an LLM to describe the details of every scene, camera tricks, transitns, etc.
  - run: `python .pipeline/projects/video_scribe/workspace/cli.py`
  - example: `python .pipeline/projects/video_scribe/workspace/cli.py --help`

- **youtube workflow tool.** (`youtube_workflow_tool`) — _verified_
  - [youtube workflow tool.]
  - run: `python .pipeline/projects/youtube_workflow_tool/workspace/cli.py`
  - example: `python .pipeline/projects/youtube_workflow_tool/workspace/cli.py --help`

## shared_lib

- **shared_lib:AudioScriptFormatter** (`shared_AudioScriptFormatter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/AudioScriptFormatter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/AudioScriptFormatter`

- **shared_lib:BlockingWaitCondition** (`shared_BlockingWaitCondition`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/BlockingWaitCondition/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/BlockingWaitCondition`

- **shared_lib:BlockingWaiter** (`shared_BlockingWaiter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/BlockingWaiter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/BlockingWaiter`

- **shared_lib:CSVParser** (`shared_CSVParser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/CSVParser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/CSVParser`

- **shared_lib:Checkpoint** (`shared_Checkpoint`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/Checkpoint/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/Checkpoint`

- **shared_lib:CheckpointStore** (`shared_CheckpointStore`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/CheckpointStore/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/CheckpointStore`

- **shared_lib:CostCalculator** (`shared_CostCalculator`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/CostCalculator/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/CostCalculator`

- **shared_lib:CveCache** (`shared_CveCache`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/CveCache/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/CveCache`

- **shared_lib:DependencyParser** (`shared_DependencyParser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/DependencyParser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/DependencyParser`

- **shared_lib:DeviceRegistry** (`shared_DeviceRegistry`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/DeviceRegistry/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/DeviceRegistry`

- **shared_lib:DomainExceptions** (`shared_DomainExceptions`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/DomainExceptions/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/DomainExceptions`

- **shared_lib:EnglishParser** (`shared_EnglishParser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/EnglishParser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/EnglishParser`

- **shared_lib:ExceptionHierarchy** (`shared_ExceptionHierarchy`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/ExceptionHierarchy/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/ExceptionHierarchy`

- **shared_lib:Importer** (`shared_Importer`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/Importer/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/Importer`

- **shared_lib:LedgerExporter** (`shared_LedgerExporter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/LedgerExporter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/LedgerExporter`

- **shared_lib:ManuscriptParser** (`shared_ManuscriptParser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/ManuscriptParser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/ManuscriptParser`

- **shared_lib:MessageHandler** (`shared_MessageHandler`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/MessageHandler/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/MessageHandler`

- **shared_lib:MockCSVSource** (`shared_MockCSVSource`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/MockCSVSource/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/MockCSVSource`

- **shared_lib:PDFParser** (`shared_PDFParser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/PDFParser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/PDFParser`

- **shared_lib:PricingConfig** (`shared_PricingConfig`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/PricingConfig/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/PricingConfig`

- **shared_lib:SerialTransport** (`shared_SerialTransport`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/SerialTransport/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/SerialTransport`

- **shared_lib:api_spec_generator** (`shared_api_spec_generator`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/api_spec_generator/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/api_spec_generator`

- **shared_lib:ascii_table_formatter** (`shared_ascii_table_formatter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/ascii_table_formatter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/ascii_table_formatter`

- **shared_lib:column_resolver** (`shared_column_resolver`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/column_resolver/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/column_resolver`

- **shared_lib:concurrent_url_checker** (`shared_concurrent_url_checker`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/concurrent_url_checker/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/concurrent_url_checker`

- **shared_lib:config_loader** (`shared_config_loader`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/config_loader/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/config_loader`

- **shared_lib:core_utils** (`shared_core_utils`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/core_utils/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/core_utils`

- **shared_lib:cost_calculator** (`shared_cost_calculator`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/cost_calculator/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/cost_calculator`

- **shared_lib:csv_auto_parser** (`shared_csv_auto_parser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/csv_auto_parser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/csv_auto_parser`

- **shared_lib:csv_header_mapper** (`shared_csv_header_mapper`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/csv_header_mapper/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/csv_header_mapper`

- **shared_lib:csv_importer** (`shared_csv_importer`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/csv_importer/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/csv_importer`

- **shared_lib:csv_ingester** (`shared_csv_ingester`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/csv_ingester/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/csv_ingester`

- **shared_lib:csv_model** (`shared_csv_model`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/csv_model/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/csv_model`

- **shared_lib:csv_parser** (`shared_csv_parser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/csv_parser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/csv_parser`

- **shared_lib:currency_formatter** (`shared_currency_formatter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/currency_formatter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/currency_formatter`

- **shared_lib:custom_exceptions** (`shared_custom_exceptions`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/custom_exceptions/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/custom_exceptions`

- **shared_lib:data_loader** (`shared_data_loader`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/data_loader/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/data_loader`

- **shared_lib:diff_entry** (`shared_diff_entry`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/diff_entry/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/diff_entry`

- **shared_lib:diff_formatter** (`shared_diff_formatter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/diff_formatter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/diff_formatter`

- **shared_lib:energy_to_viseme** (`shared_energy_to_viseme`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/energy_to_viseme/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/energy_to_viseme`

- **shared_lib:escape_html** (`shared_escape_html`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/escape_html/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/escape_html`

- **shared_lib:exception_hierarchy** (`shared_exception_hierarchy`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/exception_hierarchy/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/exception_hierarchy`

- **shared_lib:export_engine** (`shared_export_engine`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/export_engine/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/export_engine`

- **shared_lib:fill_prompt** (`shared_fill_prompt`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/fill_prompt/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/fill_prompt`

- **shared_lib:financial_column_mapper** (`shared_financial_column_mapper`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/financial_column_mapper/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/financial_column_mapper`

- **shared_lib:generator_base** (`shared_generator_base`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/generator_base/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/generator_base`

- **shared_lib:html_escape** (`shared_html_escape`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/html_escape/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/html_escape`

- **shared_lib:http_client_wrapper** (`shared_http_client_wrapper`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/http_client_wrapper/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/http_client_wrapper`

- **shared_lib:http_health_checker** (`shared_http_health_checker`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/http_health_checker/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/http_health_checker`

- **shared_lib:ingestor** (`shared_ingestor`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/ingestor/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/ingestor`

- **shared_lib:job_description_parser** (`shared_job_description_parser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/job_description_parser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/job_description_parser`

- **shared_lib:json_comparator** (`shared_json_comparator`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/json_comparator/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/json_comparator`

- **shared_lib:json_diff_core** (`shared_json_diff_core`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/json_diff_core/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/json_diff_core`

- **shared_lib:json_formatter** (`shared_json_formatter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/json_formatter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/json_formatter`

- **shared_lib:json_loader** (`shared_json_loader`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/json_loader/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/json_loader`

- **shared_lib:json_response_parser** (`shared_json_response_parser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/json_response_parser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/json_response_parser`

- **shared_lib:ledger_exporter** (`shared_ledger_exporter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/ledger_exporter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/ledger_exporter`

- **shared_lib:llmclient** (`shared_llmclient`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/llmclient/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/llmclient`

- **shared_lib:logging_utils** (`shared_logging_utils`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/logging_utils/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/logging_utils`

- **shared_lib:manuscript_model** (`shared_manuscript_model`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/manuscript_model/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/manuscript_model`

- **shared_lib:margin_parser** (`shared_margin_parser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/margin_parser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/margin_parser`

- **shared_lib:matcher** (`shared_matcher`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/matcher/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/matcher`

- **shared_lib:mock_transcriber** (`shared_mock_transcriber`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/mock_transcriber/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/mock_transcriber`

- **shared_lib:monte_carlo_engine** (`shared_monte_carlo_engine`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/monte_carlo_engine/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/monte_carlo_engine`

- **shared_lib:numeric_parser** (`shared_numeric_parser`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/numeric_parser/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/numeric_parser`

- **shared_lib:output_formatter** (`shared_output_formatter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/output_formatter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/output_formatter`

- **shared_lib:parse_margins** (`shared_parse_margins`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/parse_margins/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/parse_margins`

- **shared_lib:parser_base** (`shared_parser_base`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/parser_base/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/parser_base`

- **shared_lib:parser_factory** (`shared_parser_factory`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/parser_factory/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/parser_factory`

- **shared_lib:product_record** (`shared_product_record`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/product_record/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/product_record`

- **shared_lib:profile_data_model** (`shared_profile_data_model`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/profile_data_model/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/profile_data_model`

- **shared_lib:profile_matcher** (`shared_profile_matcher`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/profile_matcher/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/profile_matcher`

- **shared_lib:profile_model** (`shared_profile_model`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/profile_model/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/profile_model`

- **shared_lib:pytest_workspace_injector** (`shared_pytest_workspace_injector`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/pytest_workspace_injector/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/pytest_workspace_injector`

- **shared_lib:reporting_utils** (`shared_reporting_utils`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/reporting_utils/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/reporting_utils`

- **shared_lib:result_formatter** (`shared_result_formatter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/result_formatter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/result_formatter`

- **shared_lib:risk_metrics** (`shared_risk_metrics`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/risk_metrics/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/risk_metrics`

- **shared_lib:rule_engine_operators** (`shared_rule_engine_operators`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/rule_engine_operators/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/rule_engine_operators`

- **shared_lib:rule_engine_store** (`shared_rule_engine_store`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/rule_engine_store/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/rule_engine_store`

- **shared_lib:salary_cap_engine** (`shared_salary_cap_engine`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/salary_cap_engine/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/salary_cap_engine`

- **shared_lib:sample_ohlcv_generator** (`shared_sample_ohlcv_generator`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/sample_ohlcv_generator/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/sample_ohlcv_generator`

- **shared_lib:schedule_generator** (`shared_schedule_generator`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/schedule_generator/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/schedule_generator`

- **shared_lib:sec_accession_utils** (`shared_sec_accession_utils`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/sec_accession_utils/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/sec_accession_utils`

- **shared_lib:sec_fetcher** (`shared_sec_fetcher`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/sec_fetcher/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/sec_fetcher`

- **shared_lib:sec_filing_types** (`shared_sec_filing_types`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/sec_filing_types/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/sec_filing_types`

- **shared_lib:sopinput** (`shared_sopinput`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/sopinput/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/sopinput`

- **shared_lib:sops_dir** (`shared_sops_dir`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/sops_dir/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/sops_dir`

- **shared_lib:sqlite_analytics_db** (`shared_sqlite_analytics_db`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/sqlite_analytics_db/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/sqlite_analytics_db`

- **shared_lib:steplog** (`shared_steplog`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/steplog/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/steplog`

- **shared_lib:stop_words** (`shared_stop_words`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/stop_words/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/stop_words`

- **shared_lib:strategy_base** (`shared_strategy_base`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/strategy_base/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/strategy_base`

- **shared_lib:text_classifier** (`shared_text_classifier`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/text_classifier/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/text_classifier`

- **shared_lib:text_table_formatter** (`shared_text_table_formatter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/text_table_formatter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/text_table_formatter`

- **shared_lib:ticket_models** (`shared_ticket_models`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/ticket_models/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/ticket_models`

- **shared_lib:trend_indicator** (`shared_trend_indicator`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/trend_indicator/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/trend_indicator`

- **shared_lib:url_checker** (`shared_url_checker`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/url_checker/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/url_checker`

- **shared_lib:url_checker_util** (`shared_url_checker_util`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/url_checker_util/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/url_checker_util`

- **shared_lib:url_health_checker** (`shared_url_health_checker`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/url_health_checker/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/url_health_checker`

- **shared_lib:url_health_checker_formatter** (`shared_url_health_checker_formatter`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/url_health_checker_formatter/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/url_health_checker_formatter`

- **shared_lib:url_health_checker_loader** (`shared_url_health_checker_loader`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/url_health_checker_loader/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/url_health_checker_loader`

- **shared_lib:url_loader** (`shared_url_loader`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/url_loader/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/url_loader`

- **shared_lib:validate_input** (`shared_validate_input`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/validate_input/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/validate_input`

- **shared_lib:value_scoring** (`shared_value_scoring`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/value_scoring/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/value_scoring`

- **shared_lib:wav_writer** (`shared_wav_writer`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/wav_writer/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/wav_writer`

- **shared_lib:word_safe_truncator** (`shared_word_safe_truncator`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/word_safe_truncator/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/word_safe_truncator`

- **shared_lib:youtube_url_detector** (`shared_youtube_url_detector`) — _verified_
  - Promoted shared library at .pipeline/shared_libs/youtube_url_detector/
  - example: `# import from C:/Users/avata/aicompete/idea impl/.pipeline/shared_libs/youtube_url_detector`

## workflow

- **Refresh capability registry and backlog audit** (`registry_refresh`) — _verified_
  - Rebuild capability registry then regenerate backlog audit (no new code).
  - run: `python scripts/run_workflow.py registry_refresh`
  - example: `python scripts/run_workflow.py registry_refresh --help`

## connector

- **Movie chain (n8n hybrid template)** (`movie_chain_n8n`) — _draft_
  - Template connector chaining movie generation to downstream steps.
Native steps run locally; optional n8n webhook notifies self-hosted n8n.
Set status verified and fill requires when ai_movie_generatio
  - run: `python scripts/run_workflow.py movie_chain_n8n`
  - example: `python scripts/run_workflow.py movie_chain_n8n --help`

- **[Movie plus player]** (`bridge_ai_movie_generation_suite_ai_movie_generation_suite`) — _draft_
  - Unified viewer kind:connector requires: ai_movie_generation_suite, movie_player

Auto-generated from ideator (combination product scaffold). Source: - [ ] **[Movie plus player]** — Unified viewer kind
  - run: `python scripts/run_workflow.py bridge_ai_movie_generation_suite_ai_movie_generation_suite`
  - example: `python scripts/run_workflow.py bridge_ai_movie_generation_suite_ai_movie_generation_suite --help`

- **[Similar niche tool]** (`bridge_similar_niche_tool`) — _draft_
  - Another bridge requires: pipeline_health_check, pipeline_extract

Auto-generated from ideator (integration bridge). Source: - [ ] **[Similar niche tool]** — Another bridge requires: pipeline_health_ch
  - run: `python scripts/run_workflow.py bridge_similar_niche_tool`
  - example: `python scripts/run_workflow.py bridge_similar_niche_tool --help`

- **[TTS to video]** (`bridge_audiobook_script_pipeline_ai_movie_generation_suite`) — _draft_
  - Pipe audiobook output into movie suite kind:connector requires: audiobook_script_pipeline, ai_movie_generation_suite

Auto-generated from ideator (integration bridge). Source: - [ ] **[TTS to video]**
  - run: `python scripts/run_workflow.py bridge_audiobook_script_pipeline_ai_movie_generation_suite`
  - example: `python scripts/run_workflow.py bridge_audiobook_script_pipeline_ai_movie_generation_suite --help`

## project

- **Agency SOP Automator** (`agency_sop_automator`) — _draft_

- **Financial Portfolio Simulator** (`financial_portfolio_simulator`) — _draft_
  - Monte Carlo risk analysis and strategy training for stock and crypto portfolios using proven simulation math

- **Financial document analyzer** (`financial_document_analyzer`) — _draft_
  - Build a Python CLI that reads financial PDFs and CSVs, extracts key metrics (revenue, margins, ratios), and prints structured summary reports with trend analysis
  - run: `python .pipeline/projects/financial_document_analyzer/workspace/cli.py`
  - example: `python .pipeline/projects/financial_document_analyzer/workspace/cli.py --help`

- **OSINT corp2** (`osint_corp2`) — _draft_
  - OSINT for corporate tracking. Uses SEC importer and forensic for data. Thi should also have methods to extract and tracking legal public available shipping manifests, procurement data, government cont

- **PodcastSEO Metadata Optimizer** (`podcastseo_metadata_optimizer`) — _draft_
  - Build an automation tool that extracts keywords from transcripts, generates show notes, and produces platform-specific metadata for podcasts.
  - run: `python -m podcastseo.cli:app`
  - example: `python -m podcastseo.cli:app`

- **SupportAgent Workflow Builder** (`supportagent_workflow_builder`) — _draft_
  - Design an agentic SOP execution system for automated customer support ticket routing, triage, and draft response generation.
  - run: `python -m supportagent.cli:main`
  - example: `python -m supportagent.cli:main`

- **Tableau Integration Module** (`tableau_integration_module`) — _draft_
  - Add real-time data visualization dashboards to the card game simulator for tracking win rates, bankroll curves, and Nash equilibrium shifts.

- **advantage player cardgame simulator training** (`advantage_player_cardgame_simulator_training`) — _draft_
  - [monte carlo simulations and training, solve nash distance leveage pokerkit and poker-mtt-icm-master on github if necessary for making it easier to develop poker aspect to the suite. blackjack, video 
  - run: `python -m advantage_cardgames.cli.main:main`
  - example: `python -m advantage_cardgames.cli.main:main`

- **mobile access to pc** (`mobile_access_to_pc`) — _draft_
  - [Make tool to access pc remotely from apple mobile device or ipad.]

- **shuffler tracker teacher** (`shuffler_tracker_teacher`) — _draft_
  - [visualize how decks are shuffled. Stochastaic variation whether it is an even cut 26/26 on each halff or another variation like 20/30 or 30/20 statistically distributed around 26/26]

- **sim real comparator** (`sim_real_comparator`) — _draft_
  - Given a real video clip and a MuJoCo simulation render of the same task, computes multi-metric similarity: SSIM, perceptual hash, CLIP embedding cosine similarity. Outputs per-frame heatmap + global s
  - run: `python -m sim_real_comparator.cli:cli`
  - example: `python -m sim_real_comparator.cli:cli`

- **social media management/etc** (`social_media_managementetc`) — _draft_
  - [airtable like platform or system for managing social media posts and accounts. AI can help generate content and schedule posts and scale]

- **thronglets as a game** (`thronglets_as_a_game`) — _draft_
  - [each thronglet is an agent, each agent has a 2d world and you can prompt it and it can visualize interactions with the others. Turn system management into a game where the interactions of the game ma

- **tim ferriss learning tool** (`tim_ferriss_learning_tool`) — _draft_
  - [Using meta-learning accelerated learning techniques to help deconstruct topic, DISSS. (decnstruction, selection, sequencing, stakes) Gather material of various media, summarize sources, outline, prov
  - run: `python .pipeline/projects/tim_ferriss_learning_tool/workspace/cli.py`
  - example: `python .pipeline/projects/tim_ferriss_learning_tool/workspace/cli.py --help`

- **transcript extractor** (`transcript_extractor`) — _draft_
  - [transcript extractor from video and audio + summary tool. use fast whisperer or faster whisperer github or something.]
  - run: `python .pipeline/projects/transcript_extractor/workspace/cli.py`
  - example: `python .pipeline/projects/transcript_extractor/workspace/cli.py --help`

- **udemy training tool** (`udemy_training_tool`) — _draft_
  - [udemy training tool]
  - run: `python .pipeline/projects/udemy_training_tool/workspace/cli.py`
  - example: `python .pipeline/projects/udemy_training_tool/workspace/cli.py --help`

- **video management** (`video_management`) — _draft_
  - [airtable like platform or system for managing video content. AI can help generate content and schedule videos and scale. Integration with youtube suite]

## workflow

- **Registry refresh via n8n (replacement mode template)** (`registry_refresh_n8n`) — _draft_
  - Delegates execution to self-hosted n8n. Import registry_refresh_n8n.json
into n8n, activate, then set n8n.webhook_path below to match your webhook URL path.

  - run: `python scripts/run_workflow.py registry_refresh_n8n`
  - example: `python scripts/run_workflow.py registry_refresh_n8n --help`
