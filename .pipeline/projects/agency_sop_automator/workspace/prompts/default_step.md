# Default Step Template

## Step: {{step_name}}

**Description:** {{step_description}}

### Input Context
{{input_context}}

{% if previous_output != "N/A" %}
### Previous Step Output
{{previous_output}}
{% endif %}

### Output Format
{{output_format}}

---
Please execute this step and return the result as a JSON object with the following structure:
{
  "result": <your output here>,
  "tokens_used": <number of tokens used>
}
