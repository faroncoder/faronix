# model_class.tpl.py
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class {{ view.model }}(models.Model):
    {% if view.user_one_to_one %}
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="{{ view.model|lower }}")
    {% endif %}
    {% for f in fields %}
    {{ f.name }} = models.{{ f.type }}(
        {% if f.max_length %}max_length={{ f.max_length }}, {% endif %}
        {% if f.null %}null=True, {% endif %}
        {% if f.blank %}blank=True, {% endif %}
        {% if f.default is defined %}default={{ f.default|pyrepr }}, {% endif %}
        {% if f.upload_to %}upload_to={{ f.upload_to|pyrepr }}, {% endif %}
    )
    {% endfor %}

    def __str__(self):
        return getattr(self, "title", f"{{ view.model }}({{ '{' }}self.pk{{ '}' }})")
