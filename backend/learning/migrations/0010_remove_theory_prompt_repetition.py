from django.db import migrations


INSTRUCTION = "Show your working step by step on paper before choosing an answer.\n\n"


def remove_repeated_instruction(apps, schema_editor):
    Question = apps.get_model("learning", "Question")
    prompts = Question.objects.filter(
        kind="theory",
        topic__subject__slug="mathematics",
        topic__is_published=True,
    )
    for question in prompts.iterator():
        if question.prompt.startswith(INSTRUCTION):
            question.prompt = question.prompt[len(INSTRUCTION):]
            question.save(update_fields=("prompt",))


class Migration(migrations.Migration):
    dependencies = [("learning", "0009_expand_mathematics_topic_practice")]

    operations = [
        migrations.RunPython(remove_repeated_instruction, migrations.RunPython.noop),
    ]
