# seed_{{ model|lower }}.py — AUTO-GENERATED mock data loader
from django.core.management.base import BaseCommand
from core.models import {{ model }}
import random, datetime
from faker import Faker

faker = Faker()

def mock_row():
    return {
    {% for f in fields if f.name != "id" %}
        "{{ f.name }}": {{ "faker.word()" if f.type == "CharField" else
                           "faker.slug()" if f.type == "SlugField" else
                           "faker.sentence()" if f.type == "TextField" else
                           "faker.email()" if f.type == "EmailField" else
                           "random.randint(1,100)" if f.type in ["IntegerField","FloatField"] else
                           "random.choice([True,False])" if f.type == "BooleanField" else
                           "faker.date_time_this_year()" if f.type == "DateTimeField" else
                           "faker.date()" if f.type == "DateField" else
                           '{"mock":"data"}' if f.type == "JSONField" else
                           "'demo.txt'" }}
        {% if not loop.last %},{% endif %}
    {% endfor %}
    }

class Command(BaseCommand):
    help = "Seed {{ model }} with mock data"

    def handle(self, *args, **kwargs):
        for i in range(5):
            {{ model }}.objects.create(**mock_row())
        self.stdout.write(self.style.SUCCESS("✅ Seeded 5 {{ model }} rows"))
