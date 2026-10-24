from fractions import Fraction

from django.db import migrations


def format_fraction(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def format_money(cents):
    return f"GH₵{cents // 100}.{cents % 100:02d}"


def build_options(answer, distractors, variant):
    values = [str(answer)]
    for distractor in distractors:
        text = str(distractor)
        if text not in values:
            values.append(text)
        if len(values) == 4:
            break
    fallback = 1
    while len(values) < 4:
        text = str(answer + fallback) if isinstance(answer, int) else f"{answer} ({fallback})"
        if text not in values:
            values.append(text)
        fallback += 1
    answer_index = variant % 4
    options = values[1:answer_index + 1] + values[:1] + values[answer_index + 1:]
    return options, str(answer)


def make_question(kind, prompt, answer, distractors, solution, difficulty, variant):
    options, correct_answer = build_options(answer, distractors, variant)
    if kind == "theory":
        prompt = (
            "Show your working step by step on paper before choosing an answer.\n\n"
            f"{prompt}"
        )
    data = {
        "kind": kind,
        "prompt": prompt,
        "options": options,
        "correct_answer": correct_answer,
        "explanation": solution,
        "difficulty": difficulty,
        "is_published": True,
    }
    if kind == "theory":
        data["expected_answer"] = correct_answer
        data["rubric"] = "Award marks for the correct method and final answer."
    return data


def difficulty_for(kind, index):
    if kind == "mcq":
        return "easy" if index < 6 else "medium" if index < 15 else "hard"
    return "easy" if index < 3 else "medium" if index < 7 else "hard"


def question_for(topic, kind, index):
    grade = topic.grade or 7
    title = topic.title.lower()
    variant = index + (20 if kind == "theory" else 0)
    round_number = variant // 2 + 1
    form = variant % 2
    difficulty = difficulty_for(kind, index)

    if "factor" in title or "multiple" in title:
        if form == 0:
            common = 3 + round_number
            first, second = 2 + round_number * 2, 3 + round_number * 2
            left, right = common * first, common * second
            answer = common
            prompt = f"Find the highest common factor (HCF) of {left} and {right}."
            solution = (
                f"Step 1: The HCF is the largest number that divides both numbers exactly.\n"
                f"Step 2: {left} = {common} × {first}, and {right} = {common} × {second}.\n"
                f"Step 3: The greatest shared factor is {common}.\n"
                f"Answer: HCF = {answer}."
            )
        else:
            unit = 5 + round_number
            left, right = unit * 2, unit * 3
            answer = unit * 6
            prompt = f"Two bells ring every {left} minutes and {right} minutes. If they ring together now, after how many minutes will they next ring together?"
            solution = (
                f"Step 1: We need the first time that is a multiple of both intervals, so find their LCM.\n"
                f"Step 2: The intervals are {unit} × 2 and {unit} × 3. Their lowest common multiple is {unit} × 2 × 3 = {answer}.\n"
                f"Step 3: Check that {answer} ÷ {left} and {answer} ÷ {right} are whole numbers.\n"
                f"Answer: The bells ring together again after {answer} minutes."
            )
        return make_question(kind, prompt, answer, [answer * 2, answer + 1, answer * 3], solution, difficulty, variant)

    if "ratio" in title or "rate" in title or "consumer" in title or "financial" in title:
        parts_a, parts_b = 2 + round_number % 4, 3 + (round_number + 1) % 4
        unit = 8 + grade + round_number
        total = unit * (parts_a + parts_b)
        answer = unit * parts_b
        prompt = (
            f"A school club shares GH₵{total} between two teams in the ratio "
            f"{parts_a}:{parts_b}. How much does the team with {parts_b} parts receive?"
        )
        solution = (
            f"Step 1: Add the ratio parts: {parts_a} + {parts_b} = {parts_a + parts_b} parts.\n"
            f"Step 2: Find one part: GH₵{total} ÷ {parts_a + parts_b} = GH₵{unit}.\n"
            f"Step 3: The team receives {parts_b} parts, so multiply {parts_b} × GH₵{unit} = GH₵{answer}.\n"
            f"Check: the other team receives GH₵{unit * parts_a}, and the two shares add to GH₵{total}."
        )
        return make_question(kind, prompt, f"GH₵{answer}", [f"GH₵{unit * parts_a}", f"GH₵{total - unit}", f"GH₵{total}"], solution, difficulty, variant)

    if ("fraction" in title and "decimal" not in title) or "percentage" in title or "percent" in title:
        denominator_a = 3 + round_number % 5
        denominator_b = denominator_a + 1
        numerator_a = denominator_a - 1
        numerator_b = 1 + round_number % (denominator_b - 1)
        first = Fraction(numerator_a, denominator_a)
        second = Fraction(numerator_b, denominator_b)
        answer = first + second if form == 0 else first - second
        operator = "+" if form == 0 else "−"
        prompt = f"Calculate {format_fraction(first)} {operator} {format_fraction(second)}. Give your answer in its simplest form."
        solution = (
            f"Step 1: Use a common denominator. The denominators {denominator_a} and {denominator_b} have common denominator {denominator_a * denominator_b}.\n"
            f"Step 2: {format_fraction(first)} = {numerator_a * denominator_b}/{denominator_a * denominator_b} and {format_fraction(second)} = {numerator_b * denominator_a}/{denominator_a * denominator_b}.\n"
            f"Step 3: {format_fraction(first)} {operator} {format_fraction(second)} = {format_fraction(answer)}.\n"
            f"Step 4: The fraction {format_fraction(answer)} is already in its simplest form.\n"
            f"Answer: {format_fraction(answer)}."
        )
        alternatives = [first, second, first * second, answer + Fraction(1, denominator_a * denominator_b)]
        return make_question(kind, prompt, format_fraction(answer), [format_fraction(value) for value in alternatives], solution, difficulty, variant)

    if "decimal" in title:
        quantity = 2 + round_number % 7
        price = 125 + round_number * 17
        if form == 0:
            answer = quantity * price
            prompt = f"A learner buys {quantity} exercise books at GH₵{format_money(price)} each. How much do the books cost altogether?"
            solution = (
                f"Step 1: There are {quantity} books, each costing GH₵{format_money(price)}. Multiply the price by the number of books.\n"
                f"Step 2: {quantity} × {format_money(price)} cents = {answer} cents.\n"
                f"Step 3: {answer} cents is GH₵{format_money(answer)}.\n"
                f"Answer: The learner pays GH₵{format_money(answer)}."
            )
        else:
            first, second = price + 48, quantity * 13 + 27
            answer = first + second
            prompt = f"Add GH₵{format_money(first)} and GH₵{format_money(second)}."
            solution = (
                f"Step 1: Write the amounts with the decimal points lined up: {format_money(first)} + {format_money(second)}.\n"
                f"Step 2: Add the amounts: {first} cents + {second} cents = {answer} cents.\n"
                f"Step 3: Change {answer} cents to cedi and pesewa: GH₵{format_money(answer)}.\n"
                f"Answer: GH₵{format_money(answer)}."
            )
        answer_text = format_money(answer)
        return make_question(kind, prompt, f"GH₵{answer_text}", [f"GH₵{format_money(answer + 100)}", f"GH₵{format_money(answer - 100)}", f"GH₵{format_money(answer + 10)}"], solution, difficulty, variant)

    if "exponent" in title or "power" in title or "square" in title or "cube" in title:
        base = 2 + round_number % 4
        if form == 0:
            first_power, second_power = 2 + round_number % 3, 1 + round_number % 3
            exponent = first_power + second_power
            answer = f"{base}^{exponent}"
            prompt = f"Simplify {base}^{first_power} × {base}^{second_power}."
            solution = (
                f"Step 1: The bases are the same, so when powers are multiplied we add the exponents.\n"
                f"Step 2: {base}^{first_power} × {base}^{second_power} = {base}^({first_power}+{second_power}).\n"
                f"Step 3: Add the exponents: {first_power} + {second_power} = {exponent}.\n"
                f"Answer: {base}^{exponent}."
            )
            wrong = [f"{base}^{first_power * second_power}", f"{base + 1}^{exponent}", f"{base}^{exponent - 1}"]
        else:
            power = 2 + round_number % 3
            answer = base ** power
            prompt = f"Find the value of {base}^{power}."
            solution = (
                f"Step 1: An exponent tells us how many times to multiply the base by itself.\n"
                f"Step 2: {base}^{power} means " + " × ".join([str(base)] * power) + ".\n"
                f"Step 3: Multiply to get {answer}.\n"
                f"Answer: {base}^{power} = {answer}."
            )
            wrong = [answer + base, answer - base, base * power]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

    if "integer" in title and "real number" not in title:
        start, rise, fall = -2 - round_number, 8 + round_number, 3 + round_number % 5
        answer = start + rise - fall
        prompt = f"At dawn the temperature is {start}°C. It rises by {rise}°C and then falls by {fall}°C. What is the final temperature?"
        solution = (
            f"Step 1: Start at {start}°C. A rise means add, so calculate {start} + {rise} = {start + rise}.\n"
            f"Step 2: A fall means subtract: {start + rise} − {fall} = {answer}.\n"
            f"Step 3: Check the changes together: +{rise} − {fall} = {rise - fall}; then {start} + ({rise - fall}) = {answer}.\n"
            f"Answer: The final temperature is {answer}°C."
        )
        return make_question(kind, prompt, f"{answer}°C", [f"{answer + 2}°C", f"{answer - 2}°C", f"{-answer}°C"], solution, difficulty, variant)

    if "pattern" in title or "relationship" in title or "general rule" in title:
        first, difference, position = 3 + round_number, 2 + round_number % 6, 8 + round_number
        answer = first + (position - 1) * difference
        prompt = f"A number pattern starts {first}, {first + difference}, {first + difference * 2}, … . What is its {position}th term?"
        solution = (
            f"Step 1: Find the amount added each time: {first + difference} − {first} = {difference}.\n"
            f"Step 2: From term 1 to term {position}, there are {position - 1} jumps.\n"
            f"Step 3: Total increase = {position - 1} × {difference} = {(position - 1) * difference}.\n"
            f"Step 4: Add this to the first term: {first} + {(position - 1) * difference} = {answer}.\n"
            f"Answer: The {position}th term is {answer}."
        )
        return make_question(kind, prompt, answer, [answer - difference, answer + difference, first + position * difference], solution, difficulty, variant)

    if "construction" in title:
        length = 10 + 2 * round_number
        if form == 0:
            answer = length // 2
            prompt = f"A learner constructs the perpendicular bisector of a {length} cm line segment. How far is the midpoint from either endpoint?"
            solution = (
                "Step 1: A perpendicular bisector crosses a line segment at its midpoint and makes a right angle.\n"
                "Step 2: The midpoint divides the segment into two equal lengths.\n"
                f"Step 3: Divide the full length by 2: {length} ÷ 2 = {answer}.\n"
                f"Answer: The midpoint is {answer} cm from either endpoint."
            )
            wrong = [length, answer + 1, length * 2]
        else:
            answer = "a ruler and compass"
            prompt = f"Which pair of instruments is used to construct the perpendicular bisector of a {length} cm line segment accurately?"
            solution = (
                "Step 1: A ruler is used to draw the straight line and join marked points.\n"
                "Step 2: A compass draws equal arcs from both endpoints of the segment.\n"
                "Step 3: Joining the arc intersections creates a line that crosses the segment at 90° and at its midpoint.\n"
                "Answer: Use a ruler and a compass."
            )
            wrong = ["a protractor and calculator", "a tape measure and set square", "a ruler and calculator"]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

    if "angle" in title or "polygon" in title or "straight line" in title:
        angle = 35 + (round_number % 5) * 10
        if form == 0:
            other = 55 + (round_number % 4) * 10
            answer = 180 - angle - other
            prompt = f"Two angles in a triangle are {angle}° and {other}°. Find the third angle."
            solution = (
                "Step 1: The three interior angles of every triangle add up to 180°.\n"
                f"Step 2: Add the known angles: {angle}° + {other}° = {angle + other}°.\n"
                f"Step 3: Subtract from 180°: 180° − {angle + other}° = {answer}°.\n"
                f"Answer: The third angle is {answer}°."
            )
        else:
            sides = [5, 6, 8, 9, 10, 12, 15, 18][(round_number - 1) % 8]
            answer = 360 // sides
            prompt = f"A regular polygon has {sides} sides. Find the size of one exterior angle."
            solution = (
                "Step 1: The exterior angles of any polygon, one at each corner, add up to 360°.\n"
                f"Step 2: A regular polygon has equal exterior angles, so divide 360° by its {sides} sides.\n"
                f"Step 3: 360° ÷ {sides} = {answer}°.\n"
                f"Answer: One exterior angle is {answer}°."
            )
        return make_question(kind, prompt, f"{answer}°", [f"{answer + 10}°", f"{answer - 10}°", f"{180 - answer}°"], solution, difficulty, variant)

    if "surface area" in title or "volume" in title:
        length, width, height = 3 + round_number, 2 + round_number % 4, 4 + round_number % 5
        if form == 0:
            answer = length * width * height
            prompt = f"A cuboid is {length} cm long, {width} cm wide and {height} cm high. Find its volume."
            solution = (
                "Step 1: The volume of a cuboid is length × width × height.\n"
                f"Step 2: Substitute the measurements: {length} × {width} × {height}.\n"
                f"Step 3: Multiply: {length} × {width} = {length * width}, then {length * width} × {height} = {answer}.\n"
                f"Answer: The volume is {answer} cm³."
            )
            correct = f"{answer} cm³"
            wrong = [f"{length * width} cm³", f"{2 * (length + width + height)} cm³", f"{answer + length} cm³"]
        else:
            answer = 2 * (length * width + length * height + width * height)
            prompt = f"A closed cuboid measures {length} cm by {width} cm by {height} cm. Find its total surface area."
            solution = (
                "Step 1: A cuboid has two faces of each size: length × width, length × height and width × height.\n"
                f"Step 2: Add one of each: {length * width} + {length * height} + {width * height} = {length * width + length * height + width * height}.\n"
                f"Step 3: Double this total because each face size appears twice: 2 × {length * width + length * height + width * height} = {answer}.\n"
                f"Answer: The surface area is {answer} cm²."
            )
            correct = f"{answer} cm²"
            wrong = [f"{length * width + length * height + width * height} cm²", f"{answer + length} cm²", f"{2 * (length + width + height)} cm²"]
        return make_question(kind, prompt, correct, wrong, solution, difficulty, variant)

    if "measurement" in title or "area" in title or "perimeter" in title:
        length, width = 6 + round_number, 3 + round_number % 5
        if form == 0:
            answer = length * width
            prompt = f"A rectangular classroom is {length} m long and {width} m wide. What is its area?"
            solution = (
                "Step 1: Area measures the space covered inside a flat shape.\n"
                "Step 2: A rectangle's area is length × width.\n"
                f"Step 3: {length} m × {width} m = {answer} m².\n"
                f"Answer: The area is {answer} m²."
            )
            correct = f"{answer} m²"
            wrong = [f"{length + width} m²", f"{2 * (length + width)} m²", f"{answer + length} m²"]
        else:
            answer = 2 * (length + width)
            prompt = f"A rectangular garden is {length} m long and {width} m wide. How much fencing is needed to go once around it?"
            solution = (
                "Step 1: Fencing goes around the outside, so find the perimeter.\n"
                f"Step 2: A rectangle has two lengths and two widths: {length} + {width} + {length} + {width}.\n"
                f"Step 3: Perimeter = 2 × ({length} + {width}) = 2 × {length + width} = {answer} m.\n"
                f"Answer: {answer} m of fencing is needed."
            )
            correct = f"{answer} m"
            wrong = [f"{length + width} m", f"{length * width} m", f"{answer + width} m"]
        return make_question(kind, prompt, correct, wrong, solution, difficulty, variant)

    if "data" in title or "chart" in title or "probability" in title:
        if form == 0:
            values = [4 + round_number, 6 + round_number, 7 + round_number, 8 + round_number, 10 + round_number]
            answer = sum(values) // len(values)
            prompt = f"The scores are {', '.join(map(str, values))}. Find their mean."
            solution = (
                "Step 1: The mean is the total of the values divided by how many values there are.\n"
                f"Step 2: Add the scores: {' + '.join(map(str, values))} = {sum(values)}.\n"
                f"Step 3: There are {len(values)} scores, so divide: {sum(values)} ÷ {len(values)} = {answer}.\n"
                f"Answer: The mean is {answer}."
            )
        else:
            red, blue, green = 3 + round_number, 2 + round_number % 4, 1 + round_number % 3
            total = red + blue + green
            answer = Fraction(red, total)
            prompt = f"A bag contains {red} red, {blue} blue and {green} green counters. One counter is picked without looking. What is the probability it is red?"
            solution = (
                f"Step 1: Count all the counters: {red} + {blue} + {green} = {total}.\n"
                f"Step 2: The wanted outcome is picking red. There are {red} red counters.\n"
                f"Step 3: Probability = wanted outcomes ÷ all outcomes = {red}/{total}.\n"
                f"Answer: {format_fraction(answer)}."
            )
        if isinstance(answer, Fraction):
            correct = format_fraction(answer)
            wrong = [format_fraction(1 - answer), format_fraction(Fraction(1, answer.denominator)), format_fraction(answer + Fraction(1, 10))]
        else:
            correct = answer
            wrong = [answer + 1, answer - 1, sum(values)]
        return make_question(kind, prompt, correct, wrong, solution, difficulty, variant)

    if "transformation" in title or "position" in title:
        x, y = 2 + round_number, 3 + round_number % 5
        if form == 0:
            answer = f"({x}, {-y})"
            prompt = f"Point P({x}, {y}) is reflected in the x-axis. What are the coordinates of its image?"
            solution = (
                "Step 1: A reflection in the x-axis keeps the x-coordinate the same.\n"
                "Step 2: It changes the sign of the y-coordinate.\n"
                f"Step 3: ({x}, {y}) becomes ({x}, {-y}).\n"
                f"Answer: The image is {answer}."
            )
            wrong = [f"({-x}, {y})", f"({-x}, {-y})", f"({y}, {x})"]
        else:
            dx, dy = round_number + 1, 2
            answer = f"({x + dx}, {y + dy})"
            prompt = f"Point Q({x}, {y}) is translated {dx} units right and {dy} units up. Find its new coordinates."
            solution = (
                f"Step 1: Moving right adds {dx} to the x-coordinate: {x} + {dx} = {x + dx}.\n"
                f"Step 2: Moving up adds {dy} to the y-coordinate: {y} + {dy} = {y + dy}.\n"
                f"Step 3: Write the new x- and y-coordinates in order.\n"
                f"Answer: ({x + dx}, {y + dy})."
            )
            wrong = [f"({x - dx}, {y + dy})", f"({x + dx}, {y - dy})", f"({y + dy}, {x + dx})"]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

    if "formula" in title or "variable" in title:
        x = 3 + round_number
        answer = 3 * x + 5
        prompt = f"Use the formula y = 3x + 5 to find y when x = {x}."
        solution = (
            f"Step 1: Replace x in the formula with {x}: y = 3 × {x} + 5.\n"
            f"Step 2: Multiply first: 3 × {x} = {3 * x}.\n"
            f"Step 3: Add 5: {3 * x} + 5 = {answer}.\n"
            f"Answer: y = {answer}."
        )
        return make_question(kind, prompt, answer, [answer + 3, answer - 3, 3 * (x + 5)], solution, difficulty, variant)

    if ("algebra" in title or "equation" in title) and "simultaneous" not in title:
        value = 2 + round_number
        coefficient = 2 + round_number % 4
        constant = 3 + round_number
        total = coefficient * value + constant
        prompt = f"Solve {coefficient}x + {constant} = {total}. Find x."
        solution = (
            f"Step 1: We want x by itself. Subtract {constant} from both sides: {coefficient}x = {total} − {constant} = {coefficient * value}.\n"
            f"Step 2: Divide both sides by {coefficient}: x = {coefficient * value} ÷ {coefficient}.\n"
            f"Step 3: Calculate the division: x = {value}.\n"
            f"Check: {coefficient} × {value} + {constant} = {total}.\n"
            f"Answer: x = {value}."
        )
        return make_question(kind, prompt, value, [value + 1, value - 1, total], solution, difficulty, variant)

    if "real number" in title:
        value = round_number + 2
        if form == 0:
            answer = value * value - (value - 1) * (value - 1)
            prompt = f"Calculate {value}² − {value - 1}²."
            solution = (
                f"Step 1: Work out each square: {value}² = {value * value} and {value - 1}² = {(value - 1) * (value - 1)}.\n"
                f"Step 2: Subtract the second square from the first: {value * value} − {(value - 1) * (value - 1)} = {answer}.\n"
                f"Answer: {answer}."
            )
            wrong = [answer + 1, answer - 1, value * 2]
        else:
            answer = "√50"
            prompt = "Which of these numbers is irrational?"
            solution = (
                "Step 1: A rational number can be written as a fraction of two whole numbers.\n"
                "Step 2: √36 = 6 and √49 = 7, so those square roots are rational. Also, 0.5 = 1/2 is rational.\n"
                "Step 3: 50 is not a perfect square, so √50 cannot be written as a whole number or a simple fraction.\n"
                "Answer: √50 is irrational."
            )
            wrong = ["√36", "√49", "0.5"]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

    if "simultaneous" in title:
        x, y = 3 + round_number, 2 + round_number % 5
        total, difference = x + y, x - y
        answer = y if form == 0 else x
        requested = "y" if form == 0 else "x"
        prompt = f"Solve the simultaneous equations x + y = {total} and x − y = {difference}. Find {requested}."
        solution = (
            f"Step 1: Add the two equations to eliminate y: 2x = {total + difference}.\n"
            f"Step 2: Divide by 2: x = {x}.\n"
            f"Step 3: Substitute into x + y = {total}: {x} + y = {total}, so y = {y}.\n"
            f"Answer: {requested} = {answer}."
        )
        return make_question(kind, prompt, answer, [answer + 1, answer - 1, total], solution, difficulty, variant)

    answer = 2 + round_number
    prompt = f"Calculate {answer} + {round_number}."
    solution = f"Step 1: Start with {answer}.\nStep 2: Add {round_number}.\nAnswer: {answer + round_number}."
    return make_question(kind, prompt, answer + round_number, [answer, answer + round_number + 1, answer - 1], solution, difficulty, variant)


def expand_banks(apps, schema_editor):
    Topic = apps.get_model("learning", "Topic")
    Question = apps.get_model("learning", "Question")
    mathematics = apps.get_model("learning", "Subject").objects.get(slug="mathematics")
    topics = Topic.objects.filter(subject=mathematics, is_published=True).exclude(
        slug="g9-paper-2-written-practice"
    )

    for topic in topics:
        for kind, target in (("mcq", 20), ("theory", 10)):
            existing = set(
                Question.objects.filter(topic=topic, kind=kind).values_list("prompt", flat=True)
            )
            variant = 0
            while len(existing) < target:
                data = question_for(topic, kind, variant)
                if data["prompt"] in existing:
                    variant += 1
                    continue
                Question.objects.create(topic=topic, **data)
                existing.add(data["prompt"])
                variant += 1


class Migration(migrations.Migration):
    dependencies = [("learning", "0008_paper_two_choose_answers")]

    operations = [
        migrations.RunPython(expand_banks, migrations.RunPython.noop),
    ]
