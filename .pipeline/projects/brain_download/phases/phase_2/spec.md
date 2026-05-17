## Phase 2 — Resource Engine & Multi-Format Export

### Description
Expand the tool to recommend immersive learning resources (books, movies, podcasts, fiction) alongside the core curriculum, and export everything in multiple formats (PDF, workbook, quiz, Udemy-ready package).

### Deliverables
1. **Resource Recommendation Engine**
   - **Non-fiction**: Books, papers, articles with key insight extraction
   - **Entertainment mapping**: Fictional works, movies, shows that immerse learners in the topic's world
   - **Podcast/audio**: Supplementary audio resources for osmosis learning
   - Cross-referenced knowledge graph linking resources to course modules

2. **Entertainment Immersion Mapper**
   - Maps topics to fictional works that create emotional/contextual familiarity
   - Examples: Learning about medieval history → Game of Thrones + historical novels
   - Examples: Learning about AI → Ex Machina + I, Robot + non-fiction
   - Provides "watch/read before" and "watch/read after" recommendations per module

3. **Multi-Format Export System**
   - **PDF Course Book**: Complete course with all scripts, resources, and exercises
   - **Student Workbook**: Fill-in exercises, reflection prompts, practice tasks
   - **Quiz Generator**: Multiple-choice and short-answer assessments per module
   - **Udemy Package**: Properly structured folder for Udemy upload
   - **Audio Script Pack**: Readable scripts formatted for voiceover recording

4. **Knowledge Graph**
   - Visual map of how all recommended resources connect to course objectives
   - Prerequisite chains and dependency tracking
   - "Deep dive" paths for advanced learners

### Dependencies
- Phase 1 complete (course outline + scripts as foundation)
- Resource database/APIs (Book API, IMDB/TMDb API, podcast APIs)
- PDF generation library (ReportLab or WeasyPrint)
- Knowledge graph library (NetworkX)

### Success Criteria
- [ ] Recommends at least 3 non-fiction resources per course topic with key insights
- [ ] Maps at least 2 entertainment/fictional works per topic for immersion
- [ ] Entertainment recommendations are contextually relevant (not generic)
- [ ] PDF export produces a professionally formatted course book
- [ ] Student workbook includes exercises tied to each module
- [ ] Quiz generator produces valid assessments per module
- [ ] Udemy package has correct folder/file structure
- [ ] Knowledge graph visualizes resource-to-objective relationships

### Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| Resource recommendations are inaccurate | Use curated seed lists + LLM refinement; allow user corrections |
| Entertainment mapping feels forced | Build on real "thematic similarity" algorithms; use human-curated examples |
| PDF export formatting is inconsistent | Use proven template approach; test with real PDF readers |
| Knowledge graph complexity | Start with linear graph; add complexity iteratively |

---

