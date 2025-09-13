{
  "menus": {
    {% for name, items in menus.items() %}
    "{{ name }}": [{% for i in items %}"{{ i }}"{% if not loop.last %}, {% endif %}{% endfor %}]{% if not loop.last %}, {% endif %}
    {% endfor %}
  },
  "last_updated": "{{ timestamp }}"
}
