# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

{% if current_version %}
## [{{ current_version }}] - {{ current_date }}

{% for category_name, items in categories.items() %}
### {{ category_name }}

{% for item in items %}
- {{ item }}
{% endfor %}

{% endfor %}
{% else %}
## Unreleased

{% for category_name, items in categories.items() %}
### {{ category_name }}

{% for item in items %}
- {{ item }}
{% endfor %}

{% endfor %}
{% endif %}

{% if previous_versions %}
## Older Versions

{% for version_info in previous_versions %}
### [{{ version_info.version }}] - {{ version_info.date }}

{% for category_name, items in version_info.categories.items() %}
#### {{ category_name }}

{% for item in items %}
- {{ item }}
{% endfor %}

{% endfor %}
{% endfor %}
{% endif %}
