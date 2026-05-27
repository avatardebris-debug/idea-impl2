# Master Ideas List

Ideas are processed top-to-bottom. The pipeline picks the first unchecked `[ ]` item.

## Format
`- [ ] **Title** — Description of what to build`

## Ideas
[ ] [movie player] — [[lock] front end player to play the AI movies. requires: ai_movie_generation_suite]
[ ] [dialog generator] — [[lock] generate dialogue between characters. requires: ai_movie_generation_suite]
[ ] [director/editor] — [[lock] direct and cut using RL. requires: ai_movie_generation_suite]

## Robotics & Physical Agency

- [ ] **[tetra meta learn harness]** — [tetra] Validate Throng6 tetra_meta_learn toolcall from pipeline; phase 3 checks grounding_score and promotes capability in registry. requires: throng6

- [ ] **[Bootstrap Robot Training]** — Design the full robot primitive vocabulary and skill acquisition pipeline, from atomic motion primitives through sim-to-real gap measurement. --goal


- [ ] **[MuJoCo URDF Research]** — Research and compare 3 MuJoCo-compatible robot URDFs (Franka, UR5, Unitree H1). Write a ranked comparison to .pipeline/goals/urdf_research.md covering DOF, contact complexity, and sim stability. goal_check: Has a ranked comparison of ≥3 URDFs been written to .pipeline/goals/urdf_research.md? --hermes



- [ ] **[robo primitive mapper]** — [[lock] Maps video_recipe action descriptions to the canonical robot primitive vocabulary. Handles unit conversion, reference frame normalization (world/object/gripper), validates each action maps to a known primitive. Output: robot_program.json ready for mujoco_codegen. requires: video_recipe, robot_primitive_vocabulary]

- [ ] **[mujoco codegen]** — [[lock] Generates runnable MuJoCo XML scene files and Python control scripts from robo_primitive_mapper output. Handles object placement, trajectory planning, contact and grasp primitives. Executes simulation and records render video. Output: scene.xml, control.py, render.mp4. requires: robo_primitive_mapper]

- [ ] **[sim real comparator]** — [[lock] Given a real video clip and a MuJoCo simulation render of the same task, computes multi-metric similarity: SSIM, perceptual hash, CLIP embedding cosine similarity. Outputs per-frame heatmap + global score in [0,1]. Core evaluation tool for sim-to-real gap measurement. requires: video_ingestor_summary]

- [ ] **[sim real discriminator]** — [[lock] GAN-style critic trained to distinguish real robot/human footage from MuJoCo renders. Discriminator score is the RL reward signal driving adversarial sim improvement. Extends video_GAN architecture. Once gap closes past threshold, additional criteria push performance beyond the original demonstration. requires: sim_real_comparator, video_gan]

- [ ] **[pufferlib rl harness]** — [[lock] Wraps MuJoCo robot skill environments with PufferLib (github.com/PufferAI/PufferLib) for vectorized high-throughput RL training. Achieves 10-100x sample efficiency vs naive implementations. Enables training primitive skills on a consumer RTX 4090 instead of A100 cluster. Exposes: train_skill(skill_name, reward_fn, n_envs=512, max_steps=1M). Plugs sim_real_discriminator score in as reward. requires: mujoco_codegen]

- [ ] **[robot skill library]** — [[lock] SQLite + FAISS vector database of verified robot skill programs. Schema: {skill_id, name, description_embedding, video_example_path, robo_program_path, sim_score, real_score, primitive_tags}. Query by semantic similarity. Reviewer promotes successful skills here after validation. Shared library acts as reviewer: all new skills checked for redundancy and interface consistency before promotion. requires: robo_primitive_mapper]

- [ ] **[goal decomposer]** — [[lock] LLM agent that takes any high-level goal and recursively decomposes it into a dependency tree of skills using subgoal_generator. Checks robot_skill_library for each node — found skills reused, gap skills queued as video_recipe jobs. Robot can invoke any software pipeline tool (web scraping, SEO, legal, payments, Airbnb) as subgoals alongside physical skills — unified goal graph across physical and digital domains. requires: robot_skill_library, subgoal_generator]

- [ ] **[robot pipeline fork]** — [[lock] Fork of the autonomous pipeline with agents retuned for robot skill development: skill_planner, robo_codegen, sim_runner, sim_critic, skill_reviewer. Same runner/message bus/budget management — ~30% new code, ~70% reused. Robot has full LLM access and the current agent harness to develop its own software in addition to robot skill programs. Can spawn any software pipeline tool: websites, SEO, legal, finance, delegate to other robots. shared_libs/RobotPrimitives is the canonical reviewer for all generated robot code. requires: goal_decomposer, pufferlib_rl_harness, sim_real_discriminator, robot_skill_library]

## Goal Decompositions
<!-- goal:bootstrap_robot_training decomposed 2026-05-21 -->
- [ ] **[Sim-to-real gap measurement tool]** — [[goal:bootstrap_robot_training:b002] Build a Python tool to quantify sim-to-real transfer gap. Input: simulation trajectories (JSON/CSV) and real-world trajectories (JSON/CSV). Output: gap metrics including position error (RMSE), velocity error, force profile divergence, success rate delta. Key class: SimRealComparator with methods compute_position_error(), compute_success_delta(), generate_gap_report(). Write results to .pipeline/reports/sim_real_gap.md with markdown tables and matplotlib plots saved to .pipeline/figures/.]
- [ ] **[Skill acquisition pipeline orchestrator]** — [[goal:bootstrap_robot_training:b003] Create an orchestrator that chains primitive execution with skill learning. Input: skill definition JSON (sequence of primitives with parameters). Output: executable skill script in .pipeline/skills/ with logging to .pipeline/logs/skill_execution.log. Key classes: SkillOrchestrator, SkillExecutor, SkillLogger. Supports: replay, parameter tuning, failure recovery. I/O: JSON skill specs, CSV execution logs.]
- [ ] **[MuJoCo URDF compatibility layer]** — [[goal:bootstrap_robot_training:b004] Build a converter that transforms URDF robot models to MuJoCo-compatible MJCF format. Input: URDF file path. Output: .pipeline/models/converted_robot.xml with validated joint limits, collision geometries, and actuator definitions. Key function: convert_urdf_to_mjcf(urdf_path, output_path) using mujoco-py or mujoco libraries. Include validation: check joint counts, verify collision meshes, test simulation stability.]
- [ ] **[Robot skill library builder]** — [[goal:bootstrap_robot_training:b005] Build a repository of pre-trained robot skills with standardized interfaces. Requires decomposition into: (1) skill storage format, (2) skill loading/execution API, (3) skill evaluation harness.] --goal
- [ ] **[Hermes: evaluate sim-to-real transfer methods]** — [[goal:bootstrap_robot_training:b006] Research and benchmark sim-to-real transfer techniques for robot learning. Evaluate domain randomization, system identification, and adversarial domain adaptation.] --hermes


