from django.db import migrations


PREFIX = (
    "BECE-style structured practice\n"
    "(a) State the rule, formula or method you will use. [1 mark]\n"
    "(b) Solve the problem below. Show each step of your working. [2 marks]\n"
)
SUFFIX = "\n(c) Choose the option that gives your final answer to part (b). [1 mark]"


def simplify_theory_prompts(apps, schema_editor):
    Question = apps.get_model("learning", "Question")
    questions = Question.objects.filter(
        kind="theory",
        topic__subject__slug="mathematics",
        topic__is_published=True,
    )
    for question in questions.iterator():
        if question.prompt.startswith(PREFIX) and question.prompt.endswith(SUFFIX):
            question.prompt = question.prompt[len(PREFIX):-len(SUFFIX)]
            question.rubric = (
                "Total: 4 marks. Award 1 mark for choosing a suitable method, "
                "2 marks for clear and correct working, and 1 mark for the "
                "correct final answer with units or simplest form where needed."
            )
            question.save(update_fields=("prompt", "rubric"))


class Migration(migrations.Migration):
    dependencies = [("learning", "0011_standardize_mathematics_practice")]

    operations = [
        migrations.RunPython(
            simplify_theory_prompts,
            migrations.RunPython.noop,
        ),
    ]
