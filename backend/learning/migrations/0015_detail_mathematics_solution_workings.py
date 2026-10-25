from importlib import import_module

from django.db import migrations


def backfill_detailed_workings(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    Topic = apps.get_model("learning", "Topic")
    Question = apps.get_model("learning", "Question")
    mathematics = Subject.objects.get(slug="mathematics")
    topics = Topic.objects.filter(subject=mathematics, is_published=True)
    generator = import_module(
        "learning.migrations.0009_expand_mathematics_topic_practice"
    )
    standardizer = import_module(
        "learning.migrations.0011_standardize_mathematics_practice"
    )

    for topic in topics.iterator():
        explanations_by_prompt = {}
        if topic.slug != "g9-paper-2-written-practice":
            for kind in ("mcq", "theory"):
                for index in range(160):
                    data = generator.question_for(topic, kind, index)
                    explanations_by_prompt[data["prompt"]] = data["explanation"]
            for index in range(100):
                data = standardizer.additional_objective(generator, topic, index)
                if data is not None:
                    explanations_by_prompt[data["prompt"]] = data["explanation"]

        updated_questions = []
        questions = Question.objects.filter(topic=topic, is_published=True).only(
            "id", "prompt", "explanation"
        )
        for question in questions.iterator():
            explanation = explanations_by_prompt.get(
                question.prompt,
                question.explanation,
            )
            detailed_explanation = generator.expand_solution(explanation)
            if detailed_explanation != question.explanation:
                question.explanation = detailed_explanation
                updated_questions.append(question)
        if updated_questions:
            Question.objects.bulk_update(
                updated_questions,
                fields=("explanation",),
                batch_size=500,
            )


class Migration(migrations.Migration):
    dependencies = [("learning", "0014_add_varied_mathematics_practice")]

    operations = [
        migrations.RunPython(
            backfill_detailed_workings,
            migrations.RunPython.noop,
        ),
    ]