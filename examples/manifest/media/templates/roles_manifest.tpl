{
  "roles": {
    {% for role, data in roles.items() %}
    "{{ role }}": {
      "rank": {{ data.rank }},
      "can_manage": {{ data.can_manage | lower }},
      "can_edit": {{ data.can_edit | lower }},
      "label": "{{ data.label }}"
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  },
  "last_updated": "{{ timestamp }}"
}
