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
        base = 2 + index % 9
        first_power = 2 + index // 9
        second_power = 3 + index % 5
        exponent = first_power + second_power
        answer = f"{base}^{exponent}"
        prompt = f"Simplify {base}^{first_power} × {base}^{second_power}."
        solution = (
            "Step 1: The bases are the same. When multiplying powers with the same base, "
            "keep the base and add the exponents.\n"
            f"Step 2: Add the exponents: {first_power} + {second_power} = {exponent}.\n"
            f"Step 3: Keep the base {base} and write the new exponent.\n"
            f"Answer: {answer}."
        )
        distractors = [
            f"{base}^{first_power * second_power}",
            f"{base + 1}^{exponent}",
            f"{base}^{exponent - 1}",
        ]
    elif "angle" in title or "polygon" in title or "straight line" in title:
        first_coefficient = 1 + index % 4
        second_coefficient = 2 + index // 4
        x_value = 10 + index % 12
        constant = 180 - (first_coefficient + second_coefficient) * x_value
        answer = x_value
        prompt = (
            f"Two angles on a straight line are {first_coefficient}x° and "
            f"({second_coefficient}x + {constant})°. Find x."
        )
        solution = (
            "Step 1: Angles on a straight line add up to 180°.\n"
            f"Step 2: Add the expressions: {first_coefficient}x + {second_coefficient}x + "
            f"{constant} = 180, so {first_coefficient + second_coefficient}x + "
            f"{constant} = 180.\n"
            f"Step 3: Subtract {constant}: {first_coefficient + second_coefficient}x = "
            f"{180 - constant}.\n"
            f"Step 4: Divide by {first_coefficient + second_coefficient}: x = {x_value}.\n"
            f"Check: the two angles add up to 180°. Answer: x = {x_value}."
        )
        distractors = [x_value + 2, x_value - 2, 180 - x_value]
    else:
        return None

    options, correct_answer = generator.build_options(answer, distractors, index)
    return {
        "kind": "mcq",
        "prompt": prompt,
        "options": options,
        "correct_answer": correct_answer,
        "explanation": solution,
        "difficulty": objective_difficulty(index),
        "is_published": True,
    }


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
        candidate_index = 20
        while len(existing_prompts) < 40:
            data = additional_objective(generator, topic, added)
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
