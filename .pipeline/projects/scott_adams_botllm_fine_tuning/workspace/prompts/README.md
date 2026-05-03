# Prompts README

## How to Use the Style Prompt Template

### Quick Start
1. Open `style_prompt_template.md` in any text editor.
2. Copy the full prompt template block (from `You are writing in the style of Scott Adams...` through the end).
3. Paste it into your LLM of choice (ChatGPT, Claude, Gemini, etc.).
4. Replace `{task_description}` with your desired topic or writing prompt.

### Tested LLMs
This template was tested with the following models:
- **GPT-4 / GPT-4o** (OpenAI) — Best overall results for tone and humor
- **Claude 3.5 Sonnet** (Anthropic) — Strong on analytical framing
- **Gemini 1.5 Pro** (Google) — Good on thematic consistency
- **Llama 3 70B** (Meta) — Decent results; may need more few-shot examples

### Tips for Adjusting Tone
- **More humorous**: Add "Include more self-deprecating humor and absurd analogies" to the style guidelines.
- **More serious**: Remove the "slightly irreverent" instruction and add "Maintain a professional, measured tone."
- **More motivational**: Add "Emphasize actionable takeaways and end with an encouraging call to action."
- **More contrarian**: Add "Challenge common wisdom in every paragraph; use 'most people are wrong about X' framing."

### How to Swap Few-Shot Examples
1. Open `corpus/processed/corpus.jsonl` and select 5 diverse samples spanning blog, tweet, and book source types.
2. Replace the existing examples in `style_prompt_template.md` under the `## Few-Shot Examples` section.
3. Ensure each example includes the `source_type` and `date` metadata for traceability.
4. Test the updated template with your target LLM and compare output quality.

### Best Practices
- Use examples from different years to capture style evolution.
- Include at least one example per source type (blog, tweet, book).
- Avoid examples with heavy HTML artifacts or formatting issues.
- Keep examples between 50-200 words for clarity.

### Troubleshooting
- **Output too formal**: Add "Use casual language and contractions (don't, can't, won't)."
- **Output too informal**: Add "Avoid slang; maintain professional credibility."
- **Output lacks humor**: Add "Include at least one humorous analogy or self-deprecating remark per paragraph."
- **Output too long**: Add "Keep responses concise; aim for 300-500 words."
