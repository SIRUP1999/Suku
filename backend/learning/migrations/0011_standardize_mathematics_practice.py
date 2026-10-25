from importlib import import_module

from django.db import migrations


def objective_difficulty(index):
    if index < 4:
        return "easy"
    if index < 15:
        return "medium"
    return "hard"


def additional_objective(generator, topic, index):
    title = topic.title.lower()
    if "exponent" in title or "power" in title or "square" in title or "cube" in title:
        data = generator.question_for(topic, "mcq", index + 20)
    elif "angle" in title or "polygon" in title or "straight line" in title:
        data = generator.question_for(topic, "mcq", index + 20)
    else:
        return None

    data["difficulty"] = objective_difficulty(index)
    return data


def expand_and_standardize(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    Topic = apps.get_model("learning", "Topic")
    Question = apps.get_model("learning", "Question")
    generator = import_module(
        "learning.migrations.0009_expand_mathematics_topic_practice"
    )
    mathematics = Subject.objects.get(slug="mathematics")
    topics = Topic.objects.filter(subject=mathematics, is_published=True).exclude(
        slug="g9-paper-2-written-practice"
    )

    for topic in topics:
        existing_prompts = set(
            Question.objects.filter(
                topic=topic,
                kind="mcq",
                is_published=True,
            ).values_list("prompt", flat=True)
        )
        new_questions = []
        added = 0
        objective_index = 0
        candidate_index = 20
        while len(existing_prompts) < 40:
            data = additional_objective(generator, topic, objective_index)
            objective_index += 1
            if data is None:
                data = generator.question_for(topic, "mcq", candidate_index)
                data["difficulty"] = objective_difficulty(added)
                candidate_index += 1
            if data["prompt"] in existing_prompts:
                continue
            new_questions.append(Question(topic=topic, **data))
            existing_prompts.add(data["prompt"])
            added += 1
        if new_questions:
            Question.objects.bulk_create(new_questions, batch_size=500)

        objective_questions = list(
            Question.objects.filter(
                topic=topic,
                kind="mcq",
                is_published=True,
            ).order_by("id")
        )
        for index, question in enumerate(objective_questions):
            if index < 20:
                question.difficulty = (
                    "easy" if index < 6 else "medium" if index < 15 else "hard"
                )
            else:
                question.difficulty = objective_difficulty(index - 20)
        if objective_questions:
            Question.objects.bulk_update(
                objective_questions,
                fields=("difficulty",),
                batch_size=500,
            )

        theory_questions = list(
            Question.objects.filter(
                topic=topic,
                kind="theory",
                is_published=True,
            ).order_by("id"),
        )
        for question in theory_questions:
            original_prompt = question.prompt
            instruction = "Show your working step by step on paper before choosing an answer.\n\n"
            if original_prompt.startswith(instruction):
                original_prompt = original_prompt[len(instruction):]
            question.prompt = (
                "BECE-style structured practice\n"
                "(a) State the rule, formula or method you will use. [1 mark]\n"
                "(b) Solve the problem below. Show each step of your working. [2 marks]\n"
                f"{original_prompt}\n"
                "(c) Choose the option that gives your final answer to part (b). [1 mark]"
            )
            question.expected_answer = question.correct_answer
            question.rubric = (
                "Total: 4 marks. (a) 1 mark for identifying the suitable rule, formula "
                "or method. (b) 2 marks for correct substitution and clear working. "
                "(c) 1 mark for the correct final answer, including units or simplest "
                "form where needed."
            )
        if theory_questions:
            Question.objects.bulk_update(
                theory_questions,
                fields=("prompt", "expected_answer", "rubric"),
                batch_size=500,
            )


class Migration(migrations.Migration):
    dependencies = [("learning", "0010_remove_theory_prompt_repetition")]

    operations = [
        migrations.RunPython(
            expand_and_standardize,
            migrations.RunPython.noop,
        ),
    ]
