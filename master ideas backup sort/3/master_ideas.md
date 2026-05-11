# Master Ideas List

Ideas are processed top-to-bottom. The pipeline picks the first unchecked `[ ]` item.

## Format
`- [ ] **Title** — Description of what to build`

## Ideas
- [ ] **[Movie/Series auto-tracker]** — [ [lock] Tool with multiple features. 1) enables you to "continue" watching and load whatever streaming service. 2)Enables you to search across all streaming platforms. 3)Enables a centralized platform for viewing titles. 4)Affiliate link cookie and link to sign up. 5)Searches free options also.]
- [ ] **[AI movie generation suite]** — [[lock] suite that enables save the cat style screenplay writing, prompts for generating images/storyboard, prompts for describing characters, enable import of character into UE5 (or others) and integration with UE5 (or whichever is best) characters for developing movies. Possibly use GOogle Geenie or develop consistent 3d worlds and enable the development of movies from a combination of tools. At minimum should construct the beatsheet, the script, the detailed description of the scene itself, and the dialogue while leaving it open for future development of actual movie development from that set of data.]
- [ ] **[AI movie generation suite 2]** — [[lock] core suite. API surface, data models, file formats for movie generation.]
- [ ] **[Movie idea generator]** — [generate simple movie ideas. requires: ai_movie_generation_suite]
- [ ] **[beatsheet generator]** — [Save the cat beatsheet from movie idea. requires: ai_movie_generation_suite, movie_idea_generator]
- [ ] **[consistent character developer]** — [[lock] consistent characters using Kling AI or similar. requires: ai_movie_generation_suite]
- [ ] **[consistent scene developer]** — [[lock] scene describer integrating characters. requires: ai_movie_generation_suite, consistent_character_developer]
- [ ] **[dialog generator]** — [[lock] generate dialogue between characters. requires: ai_movie_generation_suite]
- [ ] **[director/editor]** — [[lock] direct and cut using RL. requires: ai_movie_generation_suite]
- [ ] **[movie player]** — [[lock] front end player to play the AI movies. requires: ai_movie_generation_suite]
