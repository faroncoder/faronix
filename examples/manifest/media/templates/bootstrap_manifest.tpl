{
  "version": "{{ version }}",
  "timestamp": "{{ timestamp }}",
  "roles": {{ roles | tojson }},
  "features": {{ features | tojson }},
  "menus": {{ menus | tojson }},
  "snippets": {{ platforms | tojson }}
}
