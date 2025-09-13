{
  "version": "{{ version }}",
  "last_updated": "{{ timestamp }}",
  "platforms": {
    {% for platform, entitlements in platforms.items() %}
    "{{ platform }}": [{% for e in entitlements %}"{{ e }}"{% if not loop.last %}, {% endif %}{% endfor %}]{% if not loop.last %}, {% endif %}
    {% endfor %}
  }
}
