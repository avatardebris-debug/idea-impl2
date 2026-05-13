# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

{% if current_version %}
## [{{ current_version }}] - {{ current_date }}

{% for category_name, entries in categories.items() %}
### {{ category_name }}
{% for entry in entries %}
- {{ entry }}
{% endfor %}

{% endfor %}
{% endif %}

{% for prev in previous_versions %}
## [{{ prev.version }}] - {{ prev.date }}

{% for category_name, entries in prev.categories.items() %}
### {{ category_name }}
{% for entry in entries %}
- {{ entry }}
{% endfor %}

{% endfor %}
{% endfor %}
