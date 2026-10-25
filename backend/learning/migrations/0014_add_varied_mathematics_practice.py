from importlib import import_module

from django.db import migrations


def add_varied_practice(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    Topic = apps.get_model("learning", "Topic")
    Question = apps.get_model("learning", "Question")
    mathematics = Subject.objects.get(slug="mathematics")
    topics = Topic.objects.filter(subject=mathematics, is_published=True).exclude(
        slug="g9-paper-2-written-practice"
    )
    generator = import_module(
        "learning.migrations.0009_expand_mathematics_topic_practice"
    )

    for topic in topics.iterator():
        existing_prompts = set(
            Question.objects.filter(topic=topic).values_list("prompt", flat=True)
        )
        additions = []
        for kind, indices in (("mcq", range(40, 56)), ("theory", range(10, 18))):
            for index in indices:
                data = generator.question_for(topic, kind, index)
                if data["prompt"] in existing_prompts:
                    continue
                additions.append(Question(topic=topic, **data))
                existing_prompts.add(data["prompt"])
        if additions:
            Question.objects.bulk_create(additions, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("learning", "0013_improve_mathematics_worked_solutions")]

    operations = [
        migrations.RunPython(
            add_varied_practice,
            migrations.RunPython.noop,
        ),
    ]
