{
  "features": {
    {% for entitlement, features in features.items() %}
    "{{ entitlement }}": [
      {% for feature in features %}"{{ feature }}"{% if not loop.last %}, {% endif %}{% endfor %}
    ]{% if not loop.last %}, {% endif %}
    {% endfor %}
  },
  "last_updated": "{{ timestamp }}"
}
