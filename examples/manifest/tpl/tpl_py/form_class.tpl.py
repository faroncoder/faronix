# form_class.tpl.py
from django import forms
{% if view.model %}from core.models import {{ view.model }}{% endif %}

class {{ tab.slug|camel }}Form(forms.{{ "ModelForm" if view.model else "Form" }}):
    {% if view.model %}
    class Meta:
        model = {{ view.model }}
        fields = [{% for field in tab.fields %}{{ field.name|pyrepr }}{% if not loop.last %}, {% endif %}{% endfor %}]
    {% else %}
    # Plain Form fields (no model backing)
    {% for field in tab.fields %}
    {{ field.name }} = forms.{{ FORM_TYPE_MAP.get(field.type, field.type or "CharField") }}(
        {% if field.label %}label={{ field.label|pyrepr }}, {% endif %}
        required={{ (field.required is not defined) or field.required }}
        {% if field.type in ["password"] %}, widget=forms.PasswordInput(){% endif %}
        {% if field.choices %}, choices={{ field.choices|pyrepr }}{% endif %}
        {% if field.initial is defined %}, initial={{ field.initial|pyrepr }}{% endif %}
        {% if field.help %}, help_text={{ field.help|pyrepr }}{% endif %}
    )
    {% endfor %}

    {% endif %}
