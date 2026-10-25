from importlib import import_module

from django.db import migrations


THEORY_PROMPT_PREFIX = "Show your working step by step on paper before choosing an answer.\n\n"


def improve_mathematics_solutions(apps, schema_editor):
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
    standardizer = import_module(
        "learning.migrations.0011_standardize_mathematics_practice"
    )

    for topic in topics.iterator():
        explanations_by_prompt = {}
        for kind in ("mcq", "theory"):
            for index in range(100):
                data = generator.question_for(topic, kind, index)
                explanations_by_prompt[data["prompt"]] = data["explanation"]
                if data["prompt"].startswith(THEORY_PROMPT_PREFIX):
                    explanations_by_prompt[
                        data["prompt"][len(THEORY_PROMPT_PREFIX):]
                    ] = data["explanation"]
        for index in range(40):
            data = standardizer.additional_objective(generator, topic, index)
            if data is not None:
                explanations_by_prompt[data["prompt"]] = data["explanation"]

        updated_questions = []
        questions = Question.objects.filter(topic=topic).only(
            "id", "prompt", "explanation"
        )
        for question in questions.iterator():
            explanation = explanations_by_prompt.get(question.prompt)
            if explanation and question.explanation != explanation:
                question.explanation = explanation
                updated_questions.append(question)
        if updated_questions:
            Question.objects.bulk_update(
                updated_questions,
                fields=("explanation",),
                batch_size=500,
            )


class Migration(migrations.Migration):
    dependencies = [("learning", "0012_simplify_theory_question_prompts")]

    operations = [
        migrations.RunPython(
            improve_mathematics_solutions,
            migrations.RunPython.noop,
        ),
    ]
