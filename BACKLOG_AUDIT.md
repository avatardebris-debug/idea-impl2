# Backlog audit

Generated: **2026-05-23 19:29 UTC**

Regenerate: `python scripts/gen_backlog_audit.py`

Compares unchecked backlog lines against `.pipeline/projects/*/state/current_idea.json`.

## Summary

| Metric | Count |
|--------|------:|
| Markdown files scanned | 27 |
| Projects complete on disk | 105 |
| Unique unchecked titles | 142 |
| **Not started** | 86 |
| **In progress** | 9 |
| **Stale** (complete on disk, still `[ ]`) | 47 |

**Runner queue:** `master_ideas.md` only.

```bash
python extract.py --rebuild-truth
python extract.py --sync-ideas
```

---

## Active queue: `master_ideas.md`

| # | Title | Slug | Disk status |
|--:|-------|------|-------------|
| 1 | movie player | `movie_player` | none |
| 2 | dialog generator | `dialog_generator` | none |
| 3 | director/editor | `director_editor` | none |
| 4 | [Bootstrap Robot Training] | `bootstrap_robot_training` | none |
| 5 | [MuJoCo URDF Research] | `mujoco_urdf_research` | none |
| 6 | [robo primitive mapper] | `robo_primitive_mapper` | none |
| 7 | [mujoco codegen] | `mujoco_codegen` | none |
| 8 | [sim real comparator] | `sim_real_comparator` | phase_3_validating (phase 3/3) |
| 9 | [sim real discriminator] | `sim_real_discriminator` | none |
| 10 | [pufferlib rl harness] | `pufferlib_rl_harness` | none |
| 11 | [robot skill library] | `robot_skill_library` | none |
| 12 | [goal decomposer] | `goal_decomposer` | none |
| 13 | [robot pipeline fork] | `robot_pipeline_fork` | none |
| 14 | [Sim-to-real gap measurement tool] | `sim_to_real_gap_measurement_tool` | none |
| 15 | [Skill acquisition pipeline orchestrator] | `skill_acquisition_pipeline_orchestrator` | none |
| 16 | [MuJoCo URDF compatibility layer] | `mujoco_urdf_compatibility_layer` | none |
| 17 | [Robot skill library builder] | `robot_skill_library_builder` | none |
| 18 | [Hermes: evaluate sim-to-real transfer methods] | `hermes_evaluate_sim_to_real_transfer_methods` | none |

---

## In progress (9)

- **[advantage player cardgame simulator training]** — `phase_3_reviewed (phase 3/6)` — `master ideas backup sort\0\master_ideas1 done.md` (+4)
- **[podcastseo metadata optimizer]** — `complete (phase 2/3)` — `master ideas backup sort\0\master_ideas_consolidated run this one to confirm everything done.md` (+2)
- **[sim real comparator]** — `phase_3_validating (phase 3/3)` — `master ideas backup sort\10\master_ideas - Copy.md` (+3)
- **[thronglets as a game]** — `complete (phase 1/5)` — `master ideas backup sort\0\master_ideas1 done.md` (+4)
- **[tim ferriss learning tool]** — `phase_4_planning (phase 3/6)` — `master ideas backup sort\0\master_ideas1 done.md` (+4)
- **[transcript extractor]** — `phase_2_planning (phase 1/5)` — `master ideas backup sort\0\master_ideas_consolidated run this one to confirm everything done.md` (+3)
- **[udemy training tool]** — `complete (phase 2/3)` — `master ideas backup sort\0\master_ideas1 done.md` (+4)
- **[video management]** — `phase_2_planning (phase 1/5)` — `master ideas backup sort\0\master_ideas1 done.md` (+4)
- **Financial document analyzer** — `complete (phase 1/3)` — `master ideas backup sort\10\master_ideas autogen1.md`

---

## Not started (86)

- **[AI Author Audiobook Integration]** — `ai_author_audiobook_integration`
- **[AI Author Docs Platform]** — `ai_author_docs_platform`
- **[AI Screenplay Writer]** — `ai_screenplay_writer`
- **[amazon audiobook to pdf converter]** — `amazon_audiobook_to_pdf_converter`
- **[Automated Dependency Resolver]** — `automated_dependency_resolver`
- **[Autonomous Web Vulnerability Scanner]** — `autonomous_web_vulnerability_scanner`
- **[Bootstrap Robot Training]** — `bootstrap_robot_training`
- **[Card Game Variant Expansion]** — `card_game_variant_expansion`
- **[Chronovision Betting Simulator]** — `chronovision_betting_simulator`
- **[Chronovision Multi-Agent Expansion]** — `chronovision_multi_agent_expansion`
- **[Chronovision State Exporter]** — `chronovision_state_exporter`
- **[CSV Analyzer Stream Processing]** — `csv_analyzer_stream_processing`
- **[CSV Chronovision Forecaster]** — `csv_chronovision_forecaster`
- **[Data Docs Generator]** — `data_docs_generator`
- **[DocsAI Code Execution Engine]** — `docsai_code_execution_engine`
- **[Drop=Gentic]** — `drop_gentic`
- **[Figma to Mobile App Generator]** — `figma_to_mobile_app_generator`
- **[Forensic accounting suite for detecting corporate fraud, predicting earnings, understanding capital flows,etc]** — `forensic_accounting_suite_for_detecting_corporate_fraud_pred`
- **[goal decomposer]** — `goal_decomposer`
- **[Hermes: evaluate sim-to-real transfer methods]** — `hermes_evaluate_sim_to_real_transfer_methods`
- **[Interactive Fiction Engine]** — `interactive_fiction_engine`
- **[Local Knowledge Graph Builder]** — `local_knowledge_graph_builder`
- **[Manuscript to Docs Bridge]** — `manuscript_to_docs_bridge`
- **[mujoco codegen]** — `mujoco_codegen`
- **[MuJoCo URDF compatibility layer]** — `mujoco_urdf_compatibility_layer`
- **[MuJoCo URDF Research]** — `mujoco_urdf_research`
- **[Multi-Agent Task Scheduler]** — `multi_agent_task_scheduler`
- **[newsletter /online profit environment for LLM RL training and sims.]** — `newsletter_online_profit_environment_for_llm_rl_training_and`
- **[PDF Schema Analyzer]** — `pdf_schema_analyzer`
- **[Pipeline Observability Dashboard]** — `pipeline_observability_dashboard`
- **[pufferlib rl harness]** — `pufferlib_rl_harness`
- **[quant developing program for prediction markets, sports, events, weather markets]** — `quant_developing_program_for_prediction_markets_sports_event`
- **[Real-Time Market Predictor]** — `real_time_market_predictor`
- **[robo primitive mapper]** — `robo_primitive_mapper`
- **[robot pipeline fork]** — `robot_pipeline_fork`
- **[Robot skill library builder]** — `robot_skill_library_builder`
- **[robot skill library]** — `robot_skill_library`
- **[SaaS Pricing Optimizer]** — `saas_pricing_optimizer`
- **[SEC to CSV Bridge]** — `sec_to_csv_bridge`
- **[sim real discriminator]** — `sim_real_discriminator`
- **[Sim-to-real gap measurement tool]** — `sim_to_real_gap_measurement_tool`
- **[Simulator Result Aggregator]** — `simulator_result_aggregator`
- **[Skill acquisition pipeline orchestrator]** — `skill_acquisition_pipeline_orchestrator`
- **[social media management/etc]** — `social_media_management_etc`
- **[sports/event bet front runner]** — `sports_event_bet_front_runner`
- **[Startup Compliance Scanner]** — `startup_compliance_scanner`
- **[Technical Whitepaper Generator]** — `technical_whitepaper_generator`
- **[udemy training tool researcher]** — `udemy_training_tool_researcher`
- **[udemy training tool2]** — `udemy_training_tool2`
- **[video babble]** — `video_babble`
- **Agent observability dashboard** — `agent_observability_dashboard`
- **AgentFlow Dropship** — `agentflow_dropship`
- **API mock server generator** — `api_mock_server_generator`
- **Automated SEO content factory** — `automated_seo_content_factory`
- **Book content repurposer** — `book_content_repurposer`
- **Card composition calculator** — `card_composition_calculator`
- **Card game training course platform** — `card_game_training_course_platform`
- **Cardgame simulator output to learning tool** — `cardgame_simulator_output_to_learning_tool`
- **Code review diff summarizer** — `code_review_diff_summarizer`
- **Config Schema Validator** — `config_schema_validator`
- **Contract clause extractor** — `contract_clause_extractor`
- **Cross-project code linter** — `cross_project_code_linter`
- **CSV-to-SOP data mapper** — `csv_to_sop_data_mapper`
- **dialog generator** — `dialog_generator`
- **director/editor** — `director_editor`
- **dropshipping suite builder** — `dropshipping_suite_builder`
- **Email attachment to CSV pipeline** — `email_attachment_to_csv_pipeline`
- **LLMClient bridge for AI Author** — `llmclient_bridge_for_ai_author`
- **Local weather dashboard CLI** — `local_weather_dashboard_cli`
- **Meeting notes auto-summarizer** — `meeting_notes_auto_summarizer`
- **movie player** — `movie_player`
- **Multi-table poker trainer** — `multi_table_poker_trainer`
- **Personal finance tracker CLI** — `personal_finance_tracker_cli`
- **Project dependency graph visualizer** — `project_dependency_graph_visualizer`
- **research2** — `research2`
- **research3** — `research3`
- **Resume and cover letter builder** — `resume_and_cover_letter_builder`
- **Resume-to-job-applicant automator** — `resume_to_job_applicant_automator`
- **Shared LLM cost tracker** — `shared_llm_cost_tracker`
- **Smart email-to-SOP executor** — `smart_email_to_sop_executor`
- **SOP marketplace** — `sop_marketplace`
- **SOP output to YouTube content feed** — `sop_output_to_youtube_content_feed`
- **Test Coverage Mutator** — `test_coverage_mutator`
- **Test fixture generator** — `test_fixture_generator`
- **Universal LLM Router** — `universal_llm_router`
- **Video content SEO engine** — `video_content_seo_engine`

---

## Stale checkboxes (47)

- **[AgentFlow Drophip]** — `agentflow_drophip`
- **[agentic mirroring game]** — `agentic_mirroring_game`
- **[AI movie generation suite]** — `ai_movie_generation_suite`
- **[babble]** — `babble`
- **[book researcher]** — `book_researcher`
- **[brain download]** — `brain_download`
- **[Chronovision autoresearch adapter]** — `chronovision_autoresearch_adapter`
- **[Chronovision2]** — `chronovision2`
- **[consistent character developer]** — `consistent_character_developer`
- **[DFS arb]** — `dfs_arb`
- **[dropify]** — `dropify`
- **[droppain]** — `droppain`
- **[dropsearch]** — `dropsearch`
- **[dropstore]** — `dropstore`
- **[email tool]** — `email_tool`
- **[extraction]** — `extraction`
- **[fiverr job automation tool]** — `fiverr_job_automation_tool`
- **[Forensic accounting suite]** — `forensic_accounting_suite`
- **[idea]** — `idea`
- **[JSON skill]** — `json_skill`
- **[osint corp]** — `osint_corp`
- **[pairenv]** — `pairenv`
- **[podcast]** — `podcast`
- **[Ranker architecture]** — `ranker_architecture`
- **[research1]** — `research1`
- **[RL for dropshipping]** — `rl_for_dropshipping`
- **[robot primitive vocabulary]** — `robot_primitive_vocabulary`
- **[See BS]** — `see_bs`
- **[SEO tool]** — `seo_tool`
- **[skill ninja]** — `skill_ninja`
- **[skillify]** — `skillify`
- **[Sports Betting Strategy Simulator]** — `sports_betting_strategy_simulator`
- **[subgoal generator]** — `subgoal_generator`
- **[unweb]** — `unweb`
- **[VASTAI instance initializer]** — `vastai_instance_initializer`
- **[video babbel enhanced]** — `video_babbel_enhanced`
- **[video GAN]** — `video_gan`
- **[video pow]** — `video_pow`
- **[video recipe]** — `video_recipe`
- **[video scribe]** — `video_scribe`
- **[VR room for stock ticker scanning.]** — `vr_room_for_stock_ticker_scanning`
- **[Youtube studio]** — `youtube_studio`
- **[youtube workflow tool.]** — `youtube_workflow_tool`
- **CSV data pipeline builder** — `csv_data_pipeline_builder`
- **Invoice processor** — `invoice_processor`
- **Real estate listing analyzer** — `real_estate_listing_analyzer`
- **URL Health Checker** — `url_health_checker`

---

## Blocked downstream (0)


Unchecked in `master_ideas.md` but `requires:` prerequisites are not verified on disk.

