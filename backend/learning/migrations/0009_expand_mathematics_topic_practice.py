from fractions import Fraction
from math import gcd

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
    variant = index + (2 if kind == "theory" else 0)
    round_number = variant // 4 + 1
    form = variant % 4
    difficulty = difficulty_for(kind, index)

    if "factor" in title or "multiple" in title:
        if form in (0, 2):
            common = 3 + round_number
            first, second = 2 + round_number * 2, 3 + round_number * 2
            left, right = common * first, common * second
            answer = common
            if form == 0:
                prompt = f"Find the highest common factor (HCF) of {left} and {right}."
                solution = (
                    "HCF is the biggest whole number that divides both numbers exactly.\n"
                    f"{left} = {common} × {first}; {right} = {common} × {second}.\n"
                    f"The remaining factors {first} and {second} are consecutive, "
                    f"so they share no factor greater than 1. The shared factor is {common}.\n"
                    f"Check: {left} ÷ {common} = {first} and {right} ÷ {common} = {second}.\n"
                    f"Answer: HCF = {answer}."
                )
            else:
                prompt = (
                    f"There are {left} pencils and {right} rulers. Make the greatest "
                    "number of identical prize bags with none left over. How many bags?"
                )
                solution = (
                    "Each bag must receive the same whole number of pencils and rulers, "
                    "so the number of bags must divide both totals.\n"
                    f"Find the HCF: {left} = {common} × {first}, and "
                    f"{right} = {common} × {second}.\n"
                    f"{first} and {second} are consecutive, so no larger shared "
                    f"factor is possible. Make {common} bags.\n"
                    f"Check: each bag gets {first} pencils and {second} rulers."
                )
        else:
            unit = 5 + round_number
            left, right = unit * 2, unit * 3
            answer = unit * 6
            if form == 1:
                prompt = f"Two bells ring every {left} minutes and {right} minutes. When will they next ring together?"
                solution = (
                    "Find the least common multiple (LCM), the first time that is "
                    "a multiple of both intervals.\n"
                    f"{left} = {unit} × 2 and {right} = {unit} × 3.\n"
                    f"Use both remaining factors: LCM = {unit} × 2 × 3 = {answer}.\n"
                    f"Check: {answer} ÷ {left} = {answer // left}, and "
                    f"{answer} ÷ {right} = {answer // right}.\n"
                    f"Answer: {answer} minutes."
                )
            else:
                prompt = (
                    f"A red light flashes every {left} seconds and a blue light "
                    f"every {right} seconds. They flash together now. After how "
                    "many seconds will they next flash together?"
                )
                solution = (
                    f"List some multiples of each interval:\n"
                    f"{left}: {left}, {left * 2}, {left * 3}, …\n"
                    f"{right}: {right}, {right * 2}, …\n"
                    f"The first shared time is {answer} seconds "
                    f"({left * 3} = {right * 2}).\n"
                    "Answer: They flash together again after "
                    f"{answer} seconds."
                )
        return make_question(kind, prompt, answer, [answer * 2, answer + 1, answer * 3], solution, difficulty, variant)

    if "ratio" in title or "rate" in title or "consumer" in title or "financial" in title:
        parts_a, parts_b = 2 + round_number % 4, 3 + (round_number + 1) % 4
        unit = 8 + grade + round_number
        total = unit * (parts_a + parts_b)
        if form in (0, 1):
            wanted_parts = parts_b if form == 0 else parts_a
            other_parts = parts_a if form == 0 else parts_b
            group_name = "second" if form == 0 else "first"
            answer = unit * wanted_parts
            prompt = (
                f"A school club shares GH₵{total} between two teams in the ratio "
                f"{parts_a}:{parts_b}. Find the {group_name} team's share."
            )
            solution = (
                f"RATIO: {parts_a}:{parts_b} means {parts_a + parts_b} equal parts altogether.\n"
                f"ONE PART: GH₵{total} ÷ {parts_a + parts_b} = GH₵{unit}.\n"
                f"SHARE: The team needs {wanted_parts} parts, so "
                f"{wanted_parts} × GH₵{unit} = GH₵{answer}.\n"
                f"CHECK: The other team gets {other_parts} × GH₵{unit} = "
                f"GH₵{unit * other_parts}; GH₵{answer} + GH₵{unit * other_parts} "
                f"= GH₵{total}."
            )
            distractors = [
                f"GH₵{unit * other_parts}",
                f"GH₵{total - unit}",
                f"GH₵{total}",
            ]
        elif form == 2:
            recipe_parts = 3 + round_number % 3
            known_amount = recipe_parts * unit
            answer = (2 + round_number % 4) * unit
            target_parts = answer // unit
            prompt = (
                f"A drink is mixed in the ratio concentrate : water = "
                f"{recipe_parts}:{target_parts}. If {known_amount} mL of "
                f"concentrate is used, how much water is needed?"
            )
            solution = (
                "SCALE-UP: Keep both parts in the ratio multiplied by the same amount.\n"
                f"{recipe_parts} parts of concentrate = {known_amount} mL, so "
                f"1 part = {known_amount} ÷ {recipe_parts} = {unit} mL.\n"
                f"Water is {target_parts} parts: {target_parts} × {unit} = {answer} mL.\n"
                f"CHECK: {known_amount}:{answer} simplifies to "
                f"{recipe_parts}:{target_parts}."
            )
            distractors = [answer + unit, answer - unit, known_amount]
        else:
            known_parts = 2 + round_number % 3
            target_parts = known_parts + 2
            unit_value = 7 + grade + round_number
            known_share = known_parts * unit_value
            answer = target_parts * unit_value
            prompt = (
                f"Two groups share money in the ratio {known_parts}:{target_parts}. "
                f"The first group receives GH₵{known_share}. How much does the "
                "second group receive?"
            )
            solution = (
                f"LINK THE RATIO TO THE MONEY: {known_parts} parts = GH₵{known_share}.\n"
                f"Find one part: GH₵{known_share} ÷ {known_parts} = GH₵{unit_value}.\n"
                f"The second group has {target_parts} parts: "
                f"{target_parts} × GH₵{unit_value} = GH₵{answer}.\n"
                "So we scale the first share by the ratio of the parts."
            )
            distractors = [
                f"GH₵{known_share + unit_value}",
                f"GH₵{known_share}",
                f"GH₵{answer + unit_value}",
            ]
        return make_question(
            kind,
            prompt,
            f"{answer} mL" if form == 2 else f"GH₵{answer}",
            [f"{value} mL" for value in distractors] if form == 2 else distractors,
            solution,
            difficulty,
            variant,
        )

    if ("fraction" in title and "decimal" not in title) or "percentage" in title or "percent" in title:
        denominator_a = 3 + round_number % 5
        denominator_b = denominator_a + 1
        numerator_a = denominator_a - 1
        numerator_b = 1 + round_number % (denominator_b - 1)
        first = Fraction(numerator_a, denominator_a)
        second = Fraction(numerator_b, denominator_b)
        if form in (0, 1):
            operator = "+" if form == 0 else "−"
            answer = first + second if form == 0 else first - second
            common_denominator = denominator_a * denominator_b
            combined_numerator = (
                numerator_a * denominator_b
                + (numerator_b * denominator_a if form == 0 else -numerator_b * denominator_a)
            )
            common_factor = gcd(abs(combined_numerator), common_denominator)
            if common_factor > 1:
                simplification = (
                    f"Divide the top and bottom by {common_factor}: "
                    f"{combined_numerator} ÷ {common_factor} over "
                    f"{common_denominator} ÷ {common_factor} = {format_fraction(answer)}."
                )
            else:
                simplification = (
                    f"{combined_numerator}/{common_denominator} has no common factor "
                    "larger than 1, so it is already in simplest form."
                )
            check = (
                "CHECK: Adding positive fractions makes the result larger than "
                "either starting fraction.\n"
                if form == 0
                else "CHECK: Subtracting a positive fraction makes the result "
                "smaller than the first fraction.\n"
            )
            prompt = (
                f"Calculate {format_fraction(first)} {operator} {format_fraction(second)}. "
                "Give your answer in its simplest form."
            )
            solution = (
                "RULE: Fractions must name equal-sized parts before we add or subtract.\n"
                f"WORKING: Use denominator {common_denominator}.\n"
                f"{format_fraction(first)} = {numerator_a * denominator_b}/{common_denominator}; "
                f"{format_fraction(second)} = {numerator_b * denominator_a}/{common_denominator}.\n"
                f"Now {numerator_a * denominator_b} {operator} "
                f"{numerator_b * denominator_a} = {combined_numerator}, so we have "
                f"{combined_numerator}/{common_denominator}. {simplification}\n"
                f"{check}"
                f"Answer: {format_fraction(answer)}."
            )
        else:
            if form == 2:
                answer = first * second
                prompt = (
                    f"A recipe uses {format_fraction(first)} cup of flour per batch. "
                    f"How much flour is needed for {format_fraction(second)} of a batch?"
                )
                solution = (
                    "IDEA: 'Of' means multiply.\n"
                    f"Multiply the numerators: {first.numerator} × {second.numerator} = "
                    f"{first.numerator * second.numerator}.\n"
                    f"Multiply the denominators: {first.denominator} × {second.denominator} = "
                    f"{first.denominator * second.denominator}.\n"
                    f"So {format_fraction(first)} × {format_fraction(second)} = "
                    f"{first.numerator * second.numerator}/{first.denominator * second.denominator} "
                    f"= {format_fraction(answer)}.\n"
                    "Answer: " + format_fraction(answer) + " cup."
                )
            else:
                answer = first / second
                prompt = (
                    f"How many {format_fraction(second)}-sized portions fit into "
                    f"{format_fraction(first)}?"
                )
                solution = (
                    "DIVISION RULE: Keep the first fraction, flip the second, then multiply.\n"
                    f"{format_fraction(first)} ÷ {format_fraction(second)} = "
                    f"{format_fraction(first)} × {format_fraction(1 / second)}.\n"
                    f"Multiply: {first.numerator} × {(1 / second).numerator} = "
                    f"{first.numerator * (1 / second).numerator}; "
                    f"{first.denominator} × {(1 / second).denominator} = "
                    f"{first.denominator * (1 / second).denominator}.\n"
                    f"Answer: {format_fraction(answer)} portions."
                )
        alternatives = [first, second, first * second, answer + Fraction(1, denominator_a * denominator_b)]
        return make_question(kind, prompt, format_fraction(answer), [format_fraction(value) for value in alternatives], solution, difficulty, variant)

    if "decimal" in title:
        quantity = 2 + round_number % 7
        price = 125 + round_number * 17
        other = 275 + round_number * 23
        if form == 0:
            answer = quantity * price
            prompt = (
                f"Each exercise book costs GH₵{format_money(price)}. Work out "
                f"the cost of {quantity} books."
            )
            solution = (
                "Think of this as equal groups: price × number of books.\n"
                f"{format_money(price)} × {quantity} = "
                f"{format_money(price * quantity)}.\n"
                "The decimal places are kept because the price is in cedis and pesewas.\n"
                f"Answer: GH₵{format_money(answer)}."
            )
        elif form == 1:
            answer = price + other
            prompt = (
                f"Add these two amounts: GH₵{format_money(price)} + "
                f"GH₵{format_money(other)}."
            )
            solution = (
                "Line up the decimal points, then add each place value:\n"
                f"  {format_money(price)}\n"
                f"+ {format_money(other)}\n"
                f"= {format_money(answer)}\n"
                f"Answer: GH₵{format_money(answer)}."
            )
        elif form == 2:
            answer = other - price
            prompt = (
                f"A notebook costs GH₵{format_money(price)} and a folder costs "
                f"GH₵{format_money(other)}. How much more does the folder cost?"
            )
            solution = (
                "The word “more” asks for the difference, so subtract the smaller "
                "amount from the larger one.\n"
                f"GH₵{format_money(other)} − GH₵{format_money(price)} = "
                f"GH₵{format_money(answer)}.\n"
                f"Check: GH₵{format_money(price)} + GH₵{format_money(answer)} "
                f"= GH₵{format_money(other)}.\n"
                f"Answer: GH₵{format_money(answer)} more."
            )
        else:
            answer = price
            total = price * quantity
            prompt = (
                f"{quantity} identical exercise books cost GH₵{format_money(total)}. "
                "What is the price of one book?"
            )
            solution = (
                "Share the total cost equally among the books.\n"
                f"GH₵{format_money(total)} ÷ {quantity} = "
                f"GH₵{format_money(answer)} per book.\n"
                f"Check by multiplying back: {quantity} × GH₵{format_money(answer)} "
                f"= GH₵{format_money(total)}."
            )
        answer_text = format_money(answer)
        distractors = [
            f"GH₵{format_money(answer + 100)}",
            f"GH₵{format_money(max(0, answer - 100))}",
            f"GH₵{format_money(answer + 10)}",
        ]
        return make_question(
            kind, prompt, f"GH₵{answer_text}", distractors, solution, difficulty, variant
        )

    if "exponent" in title or "power" in title or "square" in title or "cube" in title:
        base = 2 + round_number % 4
        if form == 0:
            first_power, second_power = 2 + round_number % 3, 1 + round_number % 3
            exponent = first_power + second_power
            answer = f"{base}^{exponent}"
            prompt = f"Simplify {base}^{first_power} × {base}^{second_power}."
            solution = (
                f"Step 1: Expand the powers: {base}^{first_power} has "
                f"{first_power} factors of {base}; {base}^{second_power} has "
                f"{second_power} more factors of {base}.\n"
                f"Step 2: Altogether there are {first_power} + {second_power} "
                "factors. This is why we add exponents when the bases are the same.\n"
                f"Step 3: {first_power} + {second_power} = {exponent}. Keep the "
                f"base {base} and write the total as its exponent.\n"
                f"Answer: {base}^{exponent}."
            )
            wrong = [f"{base}^{first_power * second_power}", f"{base + 1}^{exponent}", f"{base}^{exponent - 1}"]
        elif form == 1:
            power = 2 + round_number % 3
            answer = base ** power
            prompt = f"Find the value of {base}^{power}."
            solution = (
                f"Step 1: The exponent {power} tells how many times the base "
                f"{base} is used as a factor.\n"
                f"Step 2: Expand it: {base}^{power} = " + " × ".join([str(base)] * power) + ".\n"
                f"Step 3: Multiply the factors to get {answer}. The base is used "
                f"{power} times, as the exponent says.\n"
                f"Answer: {base}^{power} = {answer}."
            )
            wrong = [answer + base, answer - base, base * power]
        elif form == 2:
            first_power = 4 + round_number % 4
            second_power = 1 + round_number % 3
            exponent = first_power - second_power
            answer = f"{base}^{exponent}"
            prompt = (
                f"Complete the index-law simplification: "
                f"{base}^{first_power} ÷ {base}^{second_power} = {base}^□."
            )
            solution = (
                "When dividing powers with the same base, cancel matching factors. "
                "That leaves the difference between the exponents.\n"
                f"{first_power} − {second_power} = {exponent}.\n"
                f"So {base}^{first_power} ÷ {base}^{second_power} = {base}^{exponent}.\n"
                f"Answer: The missing exponent is {exponent}."
            )
            wrong = [str(exponent + 1), str(max(0, exponent - 1)), str(first_power)]
            answer = str(exponent)
        else:
            inner_power = 2 + round_number % 3
            outer_power = 2 + round_number % 2
            exponent = inner_power * outer_power
            answer = f"{base}^{exponent}"
            prompt = f"Simplify the power of a power: ({base}^{inner_power})^{outer_power}."
            solution = (
                f"Expand the brackets: there are {outer_power} groups, each with "
                f"{inner_power} factors of {base}.\n"
                f"Total factors = {inner_power} × {outer_power} = {exponent}.\n"
                f"Therefore ({base}^{inner_power})^{outer_power} = {base}^{exponent}.\n"
                f"Answer: {answer}."
            )
            wrong = [f"{base}^{inner_power + outer_power}", f"{base + 1}^{exponent}", f"{base}^{exponent - 1}"]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

    if "integer" in title and "real number" not in title:
        start, rise, fall = -2 - round_number, 8 + round_number, 3 + round_number % 5
        if form == 0:
            answer = start + rise - fall
            prompt = (
                f"At dawn it is {start}°C. The temperature rises by {rise}°C, "
                f"then falls by {fall}°C. What is it now?"
            )
            solution = (
                f"Start at {start}. A rise means add: {start} + {rise} = "
                f"{start + rise}.\n"
                f"A fall means subtract: {start + rise} − {fall} = {answer}.\n"
                f"Check the net change: +{rise} − {fall} = {rise - fall}, and "
                f"{start} + ({rise - fall}) = {answer}.\n"
                f"Answer: {answer}°C."
            )
            suffix = "°C"
        elif form == 1:
            first = -8 - round_number
            second = 3 + round_number % 4
            third = -(2 + round_number % 3)
            answer = first - second - third
            prompt = f"Work out {first} − {second} − ({third})."
            solution = (
                f"Subtracting a negative is the same as adding its positive:\n"
                f"{first} − {second} − ({third}) = {first} − {second} + "
                f"{abs(third)}.\n"
                f"First {first} − {second} = {first - second}; then "
                f"{first - second} + {abs(third)} = {answer}.\n"
                f"Answer: {answer}."
            )
            suffix = ""
        elif form == 2:
            start = -12 - round_number
            right = 7 + round_number
            left = 3 + round_number % 4
            answer = start + right - left
            prompt = (
                f"Begin at {start} on a number line. Move {right} places right "
                f"and then {left} places left. Where do you land?"
            )
            solution = (
                f"Right means add: {start} + {right} = {start + right}.\n"
                f"Left means subtract: {start + right} − {left} = {answer}.\n"
                f"Answer: You land on {answer}."
            )
            suffix = ""
        else:
            opening = -10 - round_number
            deposit = 15 + round_number
            withdrawal = 8 + round_number % 5
            answer = opening + deposit - withdrawal
            prompt = (
                f"A wallet is GH₵{abs(opening)} overdrawn. A deposit of GH₵{deposit} "
                f"is made, then GH₵{withdrawal} is spent. What is the final balance?"
            )
            solution = (
                f"Being overdrawn is below zero, so start at −{abs(opening)}.\n"
                f"Add the deposit: −{abs(opening)} + {deposit} = "
                f"{opening + deposit}.\n"
                f"Subtract the spending: {opening + deposit} − {withdrawal} = {answer}.\n"
                f"Answer: GH₵{answer}."
            )
            suffix = ""
        correct = f"GH₵{answer}" if form == 3 else f"{answer}{suffix}"
        wrong = [
            f"GH₵{answer + 2}" if form == 3 else f"{answer + 2}{suffix}",
            f"GH₵{answer - 2}" if form == 3 else f"{answer - 2}{suffix}",
            f"GH₵{-answer}" if form == 3 else f"{-answer}{suffix}",
        ]
        return make_question(kind, prompt, correct, wrong, solution, difficulty, variant)

    if "pattern" in title or "relationship" in title or "general rule" in title:
        first, difference, position = 3 + round_number, 2 + round_number % 6, 8 + round_number
        terms = [first + step * difference for step in range(5)]
        if form == 0:
            answer = first + (position - 1) * difference
            prompt = f"Find the {position}th term: {', '.join(map(str, terms[:4]))}, …"
            solution = (
                f"The sequence adds {difference} each time: {terms[1]} − "
                f"{terms[0]} = {difference}.\n"
                f"To reach term {position}, make {position} − 1 = {position - 1} "
                f"jumps. Increase = {position - 1} × {difference} = "
                f"{(position - 1) * difference}.\n"
                f"Add this to the first term: {first} + {(position - 1) * difference} = {answer}.\n"
                f"Answer: {answer}."
            )
            wrong = [answer - difference, answer + difference, first + position * difference]
        elif form == 1:
            answer = first + (position - 1) * difference
            rule_constant = first - difference
            prompt = f"The rule for a sequence is Tₙ = {difference}n {rule_constant:+}. Find T₍{position}₎."
            solution = (
                f"Substitute n = {position} into Tₙ = {difference}n {rule_constant:+}:\n"
                f"T₍{position}₎ = {difference} × {position} {rule_constant:+}.\n"
                f"Multiply first: {difference * position} {rule_constant:+} = {answer}.\n"
                f"Answer: T₍{position}₎ = {answer}."
            )
            wrong = [answer - difference, answer + difference, first + position * difference]
        elif form == 2:
            answer = terms[-1] + difference
            prompt = f"Continue the pattern by one term: {', '.join(map(str, terms))}, __."
            solution = (
                f"Compare neighbouring terms: {terms[1]} − {terms[0]} = "
                f"{difference}, and {terms[2]} − {terms[1]} = {difference}.\n"
                f"So add {difference} to the last term: {terms[-1]} + {difference} = {answer}.\n"
                f"Answer: {answer}."
            )
            wrong = [answer - difference, answer + 1, answer + difference * 2]
        else:
            answer = f"{difference}n {first - difference:+}"
            prompt = (
                f"Write the nth-term rule for this sequence: "
                f"{', '.join(map(str, terms[:4]))}, …"
            )
            solution = (
                f"The sequence goes up by {difference}, so begin with {difference}n.\n"
                f"For n = 1, {difference}n gives {difference}; the first term is "
                f"{first}. Add {first - difference:+} to make the first term correct.\n"
                f"Check n = 2: {difference * 2} {first - difference:+} = {terms[1]}.\n"
                f"Answer: Tₙ = {answer}."
            )
            wrong = [f"{difference}n {first:+}", f"{difference + 1}n {first - difference:+}", f"{difference}n {first + difference:+}"]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

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
        elif form == 1:
            answer = "a ruler and compass"
            prompt = f"Which pair of instruments is used to construct the perpendicular bisector of a {length} cm line segment accurately?"
            solution = (
                "Step 1: A ruler is used to draw the straight line and join marked points.\n"
                "Step 2: A compass draws equal arcs from both endpoints of the segment.\n"
                "Step 3: Joining the arc intersections creates a line that crosses the segment at 90° and at its midpoint.\n"
                "Answer: Use a ruler and a compass."
            )
            wrong = ["a protractor and calculator", "a tape measure and set square", "a ruler and calculator"]
        elif form == 2:
            answer = "the two arc intersections"
            prompt = (
                f"When constructing the perpendicular bisector of a {length} cm "
                "segment, what should be joined after drawing equal arcs from both ends?"
            )
            solution = (
                "Keep the compass opening the same for both ends of the segment.\n"
                "The arcs cross at two points, one on each side of the segment.\n"
                "Use a ruler to join those two crossing points. That line is the "
                "perpendicular bisector."
            )
            wrong = ["the two endpoints only", "the segment's midpoint to one end", "any two arc points"]
        else:
            answer = "90° and equal halves"
            prompt = (
                "A perpendicular bisector crosses a line segment. What two "
                "properties must the construction have?"
            )
            solution = (
                "“Perpendicular” means the crossing angle is a right angle: 90°.\n"
                "“Bisector” means the segment is split into two equal lengths.\n"
                "Answer: It crosses at 90° and makes two equal halves."
            )
            wrong = ["45° and unequal halves", "180° and equal halves", "90° and three equal parts"]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

    if "angle" in title or "polygon" in title or "straight line" in title:
        angle = 35 + (round_number % 5) * 10
        if form == 0:
            other = 55 + (round_number % 4) * 10
            answer = 180 - angle - other
            prompt = f"Two angles in a triangle are {angle}° and {other}°. Find the third angle."
            solution = (
                "Step 1: The three interior angles of a triangle form a straight "
                "turn, so their total is 180°.\n"
                f"Step 2: Add the known angles: {angle}° + {other}° = {angle + other}°.\n"
                f"Step 3: The third angle is the amount missing from 180°: "
                f"180° − {angle + other}° = {answer}°.\n"
                f"Check: {angle}° + {other}° + {answer}° = 180°.\n"
                f"Answer: The third angle is {answer}°."
            )
            correct = f"{answer}°"
            wrong = [f"{answer + 10}°", f"{answer - 10}°", f"{180 - answer}°"]
        elif form == 1:
            sides = [5, 6, 8, 9, 10, 12, 15, 18][(round_number - 1) % 8]
            answer = 360 // sides
            prompt = f"A regular polygon has {sides} sides. Find the size of one exterior angle."
            solution = (
                "Step 1: Walking once around a polygon turns through 360°, so "
                "its exterior angles total 360°.\n"
                f"Step 2: A regular polygon has equal exterior angles. Share "
                f"360° equally among its {sides} corners.\n"
                f"Step 3: 360° ÷ {sides} = {answer}°.\n"
                f"Check: {sides} × {answer}° = 360°.\n"
                f"Answer: One exterior angle is {answer}°."
            )
            correct = f"{answer}°"
            wrong = [f"{answer + 10}°", f"{answer - 10}°", f"{180 - answer}°"]
        elif form == 2:
            coefficient = 2 + round_number % 3
            answer = 20 + round_number % 10
            constant = 180 - answer * (coefficient + 1)
            other_angle = answer + constant
            prompt = (
                f"Two angles on a straight line are {coefficient}x° and "
                f"(x + {constant})°. Find x."
            )
            solution = (
                "These angles sit on a straight line, so together they make 180°.\n"
                f"{coefficient}x + (x + {constant}) = 180.\n"
                f"Combine x terms: {coefficient + 1}x + {constant} = 180.\n"
                f"Subtract {constant}, then divide by {coefficient + 1}: "
                f"x = (180 − {constant}) ÷ {coefficient + 1} = {answer}.\n"
                f"Check: {coefficient * answer}° + {other_angle}° = 180°."
            )
            correct = str(answer)
            wrong = [str(answer + 5), str(answer - 5), str(180 - answer)]
        else:
            known = [70 + round_number % 4 * 5, 85, 105]
            answer = 360 - sum(known)
            prompt = (
                f"A quadrilateral has angles {known[0]}°, {known[1]}° and "
                f"{known[2]}°. Find its fourth angle."
            )
            solution = (
                "All four inside angles of a quadrilateral add to 360°.\n"
                f"Known total = {known[0]}° + {known[1]}° + {known[2]}° "
                f"= {sum(known)}°.\n"
                f"Missing angle = 360° − {sum(known)}° = {answer}°.\n"
                f"Check: {sum(known)}° + {answer}° = 360°."
            )
            correct = f"{answer}°"
            wrong = [f"{answer + 10}°", f"{answer - 10}°", f"{180 - answer}°"]
        return make_question(kind, prompt, correct, wrong, solution, difficulty, variant)

    if "surface area" in title or "volume" in title:
        length, width, height = 3 + round_number, 2 + round_number % 4, 4 + round_number % 5
        if form == 0:
            answer = length * width * height
            prompt = f"A cuboid is {length} cm long, {width} cm wide and {height} cm high. Find its volume."
            solution = (
                "Step 1: The volume of a cuboid is length × width × height.\n"
                f"Step 2: Substitute the measurements because each layer has "
                f"{length} × {width} square centimetres and there are {height} layers: "
                f"{length} × {width} × {height}.\n"
                f"Step 3: Multiply in two parts: {length} × {width} = {length * width} "
                f"cm², then {length * width} × {height} = {answer} cm³.\n"
                f"Answer: The volume is {answer} cm³."
            )
            correct = f"{answer} cm³"
            wrong = [f"{length * width} cm³", f"{2 * (length + width + height)} cm³", f"{answer + length} cm³"]
        elif form == 1:
            answer = 2 * (length * width + length * height + width * height)
            prompt = f"A closed cuboid measures {length} cm by {width} cm by {height} cm. Find its total surface area."
            solution = (
                "Step 1: A cuboid has three different face sizes: length × width, "
                "length × height, and width × height. Each size appears on two faces.\n"
                f"Step 2: Find one face of each size: {length} × {width} = {length * width}, "
                f"{length} × {height} = {length * height}, and {width} × {height} = {width * height} cm².\n"
                f"Step 3: Add these three areas: {length * width} + {length * height} + "
                f"{width * height} = {length * width + length * height + width * height} cm².\n"
                f"Step 4: Double the sum because each face size occurs twice: "
                f"2 × {length * width + length * height + width * height} = {answer} cm².\n"
                f"Answer: The surface area is {answer} cm²."
            )
            correct = f"{answer} cm²"
            wrong = [f"{length * width + length * height + width * height} cm²", f"{answer + length} cm²", f"{2 * (length + width + height)} cm²"]
        elif form == 2:
            answer = height
            volume = length * width * height
            prompt = (
                f"A cuboid has a volume of {volume} cm³. Its base measures "
                f"{length} cm by {width} cm. How high is it?"
            )
            solution = (
                "Volume = base area × height, so first find the base area.\n"
                f"Base area = {length} × {width} = {length * width} cm².\n"
                f"Height = volume ÷ base area = {volume} ÷ {length * width} = {answer} cm.\n"
                f"Check: {length * width} × {answer} = {volume} cm³."
            )
            correct = f"{answer} cm"
            wrong = [f"{answer + 1} cm", f"{length * width} cm", f"{volume} cm"]
        else:
            answer = length * width * height
            prompt = (
                f"How many 1 cm³ cubes are needed to fill a box measuring "
                f"{length} cm × {width} cm × {height} cm?"
            )
            solution = (
                "Each 1 cm³ cube fills one cubic centimetre of space.\n"
                f"Number of cubes = box volume = {length} × {width} × {height}.\n"
                f"{length} × {width} = {length * width}, then "
                f"{length * width} × {height} = {answer}.\n"
                f"Answer: {answer} cubes."
            )
            correct = str(answer)
            wrong = [str(length * width), str(answer + length), str(answer - width)]
        return make_question(kind, prompt, correct, wrong, solution, difficulty, variant)

    if "measurement" in title or "area" in title or "perimeter" in title:
        length, width = 6 + round_number, 3 + round_number % 5
        if form == 0:
            answer = length * width
            prompt = f"A rectangular classroom is {length} m long and {width} m wide. What is its area?"
            solution = (
                "Step 1: The question asks for the space inside the rectangle, "
                "which is its area (not the distance around it).\n"
                "Step 2: A rectangle has length × width square units because it "
                "contains that many unit squares.\n"
                f"Step 3: Substitute and multiply: {length} m × {width} m = "
                f"{answer} m². The units multiply too: m × m = m².\n"
                f"Answer: The area is {answer} m²."
            )
            correct = f"{answer} m²"
            wrong = [f"{length + width} m²", f"{2 * (length + width)} m²", f"{answer + length} m²"]
        elif form == 1:
            answer = 2 * (length + width)
            prompt = f"A rectangular garden is {length} m long and {width} m wide. How much fencing is needed to go once around it?"
            solution = (
                "Step 1: Fencing goes around the outside, so we need the perimeter, "
                "not the area.\n"
                f"Step 2: A rectangle has two equal lengths and two equal widths: "
                f"{length} + {width} + {length} + {width} metres.\n"
                f"Step 3: Add one length and one width: {length} + {width} = "
                f"{length + width}. Double for the opposite sides: 2 × "
                f"{length + width} = {answer} m.\n"
                f"Answer: {answer} m of fencing is needed."
            )
            correct = f"{answer} m"
            wrong = [f"{length + width} m", f"{length * width} m", f"{answer + width} m"]
        elif form == 2:
            base = 2 * (length + 2)
            triangle_height = width
            answer = base * triangle_height // 2
            prompt = (
                f"A triangular sign has a base of {base} cm and a perpendicular "
                f"height of {triangle_height} cm. Find its area."
            )
            solution = (
                "A triangle is half of a rectangle with the same base and height.\n"
                f"Area = (base × height) ÷ 2 = ({base} × {triangle_height}) ÷ 2.\n"
                f"{base} × {triangle_height} = {base * triangle_height}; "
                f"{base * triangle_height} ÷ 2 = {answer} cm².\n"
                f"Answer: {answer} cm²."
            )
            correct = f"{answer} cm²"
            wrong = [f"{base * triangle_height} cm²", f"{base + triangle_height} cm²", f"{answer + base} cm²"]
        else:
            side = length
            answer = 4 * side
            prompt = f"A square tile has a side length of {side} cm. What is its perimeter?"
            solution = (
                "Perimeter is the distance around the outside. A square has four "
                "equal sides.\n"
                f"Add the sides: {side} + {side} + {side} + {side} = 4 × {side}.\n"
                f"4 × {side} = {answer} cm.\n"
                f"Answer: {answer} cm."
            )
            correct = f"{answer} cm"
            wrong = [f"{side * side} cm", f"{2 * side} cm", f"{answer + side} cm"]
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
            correct = answer
            wrong = [answer + 1, answer - 1, sum(values)]
        elif form == 1:
            red, blue, green = 3 + round_number, 2 + round_number % 4, 1 + round_number % 3
            total = red + blue + green
            answer = Fraction(red, total)
            prompt = f"A bag contains {red} red, {blue} blue and {green} green counters. One counter is picked without looking. What is the probability it is red?"
            solution = (
                f"Step 1: Count all the counters: {red} + {blue} + {green} = {total}.\n"
                f"Step 2: The wanted outcomes are the {red} red counters; the total "
                f"number of equally likely counters is {total}.\n"
                f"Step 3: Probability = wanted outcomes ÷ all outcomes = {red}/{total}.\n"
                f"Step 4: Divide the numerator and denominator by their common "
                f"factor, if any: {format_fraction(answer)}.\n"
                f"Answer: {format_fraction(answer)}."
            )
            correct = format_fraction(answer)
            wrong = [
                format_fraction(1 - answer),
                format_fraction(Fraction(1, answer.denominator)),
                format_fraction(answer + Fraction(1, 10)),
            ]
        elif form == 2:
            values = [3 + round_number, 8 + round_number, 5 + round_number, 12 + round_number, 7 + round_number]
            ordered = sorted(values)
            answer = ordered[len(ordered) // 2]
            prompt = f"Find the median of these scores: {', '.join(map(str, values))}."
            solution = (
                "The median is the middle value after sorting the data.\n"
                f"In order: {', '.join(map(str, ordered))}.\n"
                f"There are {len(ordered)} scores, so the middle is position "
                f"{(len(ordered) + 1) // 2}: {answer}.\n"
                f"Answer: The median is {answer}."
            )
            correct = answer
            wrong = [answer + 1, answer - 1, ordered[-1]]
        else:
            repeated = 4 + round_number
            values = [repeated, 6 + round_number, repeated, 9 + round_number, 11 + round_number, repeated]
            answer = repeated
            prompt = f"Which score is the mode: {', '.join(map(str, values))}?"
            solution = (
                "The mode is the value that appears most often.\n"
                f"{answer} appears 3 times; each other score appears once.\n"
                f"Answer: The mode is {answer}."
            )
            correct = answer
            wrong = [answer + 1, answer + 2, answer - 1]
        return make_question(kind, prompt, correct, wrong, solution, difficulty, variant)

    if "transformation" in title or "position" in title:
        x, y = 2 + round_number, 3 + round_number % 5
        if form == 0:
            answer = f"({x}, {-y})"
            prompt = f"Point P({x}, {y}) is reflected in the x-axis. What are the coordinates of its image?"
            solution = (
                "Step 1: The x-axis is the mirror line. The point stays the same "
                "horizontal distance from it, so x does not change.\n"
                f"Step 2: The point is {y} units above the x-axis, so its image "
                f"is {y} units below it: change y to −{y}.\n"
                f"Step 3: Keep coordinates in (x, y) order: ({x}, {y}) becomes "
                f"({x}, {-y}).\n"
                f"Answer: The image is {answer}."
            )
            wrong = [f"({-x}, {y})", f"({-x}, {-y})", f"({y}, {x})"]
        elif form == 1:
            dx, dy = round_number + 1, 2
            answer = f"({x + dx}, {y + dy})"
            prompt = f"Point Q({x}, {y}) is translated {dx} units right and {dy} units up. Find its new coordinates."
            solution = (
                f"Step 1: Right changes horizontal position, so add {dx} to x: "
                f"{x} + {dx} = {x + dx}.\n"
                f"Step 2: Up changes vertical position, so add {dy} to y: "
                f"{y} + {dy} = {y + dy}.\n"
                "Step 3: Coordinates are always written (x, y), horizontal first.\n"
                f"Answer: ({x + dx}, {y + dy})."
            )
            wrong = [f"({x - dx}, {y + dy})", f"({x + dx}, {y - dy})", f"({y + dy}, {x + dx})"]
        elif form == 2:
            answer = f"({-x}, {y})"
            prompt = (
                f"Point A({x}, {y}) is reflected in the y-axis. Give the image "
                "coordinates."
            )
            solution = (
                "A reflection in the y-axis reverses left and right.\n"
                f"So the x-coordinate changes sign: {x} becomes −{x}.\n"
                f"The y-coordinate stays {y}. Therefore A′ = ({-x}, {y})."
            )
            wrong = [f"({x}, {-y})", f"({-x}, {-y})", f"({y}, {-x})"]
        else:
            dx, dy = round_number + 1, 3
            answer = f"({x - dx}, {y - dy})"
            prompt = (
                f"Translate point B({x}, {y}) {dx} units left and {dy} units "
                "down. Where does it move?"
            )
            solution = (
                f"Left means subtract from x: {x} − {dx} = {x - dx}.\n"
                f"Down means subtract from y: {y} − {dy} = {y - dy}.\n"
                f"Keep the coordinate order (x, y): B′ = ({x - dx}, {y - dy})."
            )
            wrong = [f"({x + dx}, {y - dy})", f"({x - dx}, {y + dy})", f"({y - dy}, {x - dx})"]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

    if "formula" in title or "variable" in title:
        x = 3 + round_number
        y = 3 * x + 5
        if form == 0:
            answer = y
            prompt = f"Use y = 3x + 5 to find y when x = {x}."
            solution = (
                f"Replace x with {x}: y = 3 × {x} + 5.\n"
                f"Multiply before adding: 3 × {x} = {3 * x}.\n"
                f"Then {3 * x} + 5 = {answer}.\n"
                f"Answer: y = {answer}."
            )
            wrong = [answer + 3, answer - 3, 3 * (x + 5)]
        elif form == 1:
            answer = x
            prompt = f"In y = 3x + 5, find x when y = {y}."
            solution = (
                f"Substitute y = {y}: {y} = 3x + 5.\n"
                f"Undo +5 by subtracting 5: {y} − 5 = 3x, so {y - 5} = 3x.\n"
                f"Divide by 3: x = {y - 5} ÷ 3 = {answer}.\n"
                f"Check: 3 × {answer} + 5 = {y}."
            )
            wrong = [answer + 1, answer - 1, y]
        elif form == 2:
            xs = [x, x + 1, x + 2]
            ys = [3 * value + 5 for value in xs]
            answer = ys[1]
            prompt = (
                "Complete the input-output table for y = 3x + 5.\n"
                f"x: {xs[0]} | {xs[1]} | {xs[2]}\n"
                f"y: {ys[0]} | ? | {ys[2]}"
            )
            solution = (
                f"Use the middle input x = {xs[1]} in the rule.\n"
                f"y = 3 × {xs[1]} + 5 = {3 * xs[1]} + 5 = {answer}.\n"
                f"Answer: The missing table value is {answer}."
            )
            wrong = [answer + 3, answer - 3, xs[1]]
        else:
            length, width = x, x - 1
            answer = 2 * (length + width)
            prompt = (
                f"A rectangle's perimeter is P = 2l + 2w. Find P when "
                f"l = {length} cm and w = {width} cm."
            )
            solution = (
                f"Substitute the measurements: P = 2 × {length} + 2 × {width}.\n"
                f"Multiply each term: P = {2 * length} + {2 * width} = {answer}.\n"
                f"Perimeter is a length, so include cm.\n"
                f"Answer: P = {answer} cm."
            )
            wrong = [answer + 2, answer - 2, length * width]
        correct = f"{answer} cm" if form == 3 else answer
        choices = [f"{value} cm" for value in wrong] if form == 3 else wrong
        return make_question(kind, prompt, correct, choices, solution, difficulty, variant)

    if ("algebra" in title or "equation" in title) and "simultaneous" not in title:
        value = 2 + round_number
        coefficient = 2 + round_number % 4
        constant = 3 + round_number
        total = coefficient * value + constant
        if form == 0:
            answer = value
            prompt = f"Solve {coefficient}x + {constant} = {total}. Find x."
            solution = (
                f"Subtract {constant} from both sides to keep the equation balanced: "
                f"{coefficient}x = {total} − {constant} = {coefficient * value}.\n"
                f"Divide both sides by {coefficient}: x = {coefficient * value} ÷ "
                f"{coefficient} = {answer}.\n"
                f"Check: {coefficient} × {answer} + {constant} = {total}."
            )
            wrong = [answer + 1, answer - 1, total]
        elif form == 1:
            left_coefficient = 2 + round_number % 3
            right_coefficient = 1
            added = 4 + round_number
            answer = f"{left_coefficient + right_coefficient}x + {added}"
            prompt = f"Expand and simplify: {left_coefficient}(x + {round_number}) + x + {added - left_coefficient * round_number}."
            solution = (
                f"Multiply {left_coefficient} by both terms inside the bracket:\n"
                f"{left_coefficient}x + {left_coefficient * round_number} + x + "
                f"{added - left_coefficient * round_number}.\n"
                f"Collect like terms: {left_coefficient}x + x = "
                f"{left_coefficient + right_coefficient}x, and the constants add to {added}.\n"
                f"Answer: {answer}."
            )
            wrong = [f"{left_coefficient + 1}x + {added}", f"{left_coefficient + right_coefficient}x", f"{left_coefficient + right_coefficient}x + {added + 1}"]
        elif form == 2:
            left_coefficient = 3 + round_number % 3
            right_coefficient = 1 + round_number % 2
            answer = 4 + round_number
            constant = (left_coefficient - right_coefficient) * answer
            prompt = f"Solve {left_coefficient}x = {right_coefficient}x + {constant}."
            solution = (
                f"Subtract {right_coefficient}x from both sides: "
                f"{left_coefficient - right_coefficient}x = {constant}.\n"
                f"Divide both sides by {left_coefficient - right_coefficient}: "
                f"x = {constant} ÷ {left_coefficient - right_coefficient} = {answer}.\n"
                f"Check: {left_coefficient} × {answer} = "
                f"{right_coefficient} × {answer} + {constant}."
            )
            wrong = [answer + 1, answer - 1, constant]
        else:
            answer = value
            groups = coefficient
            prompt = (
                f"A number is multiplied by {groups}, then {constant} is added. "
                f"The result is {total}. What was the number?"
            )
            solution = (
                f"Undo the last operation first: subtract {constant} from {total}.\n"
                f"{total} − {constant} = {coefficient * value}.\n"
                f"Now undo multiplying by {groups}: {coefficient * value} ÷ {groups} = {answer}.\n"
                f"Check: {answer} × {groups} + {constant} = {total}."
            )
            wrong = [answer + 1, answer - 1, total]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

    if "real number" in title:
        value = round_number + 2
        if form == 0:
            answer = value * value - (value - 1) * (value - 1)
            prompt = f"Calculate {value}² − {value - 1}²."
            solution = (
                f"Step 1: Squaring means multiplying a number by itself: "
                f"{value}² = {value} × {value} = {value * value}, and "
                f"{value - 1}² = {value - 1} × {value - 1} = {(value - 1) * (value - 1)}.\n"
                f"Step 2: The minus sign means subtract the second square from "
                f"the first: {value * value} − {(value - 1) * (value - 1)} = {answer}.\n"
                f"Answer: {answer}."
            )
            wrong = [answer + 1, answer - 1, value * 2]
        elif form == 1:
            answer = "√50"
            prompt = "Which of these numbers is irrational?"
            solution = (
                "Step 1: A rational number can be written as a fraction of two whole numbers.\n"
                "Step 2: √36 = 6 and √49 = 7, so those square roots are rational. Also, 0.5 = 1/2 is rational.\n"
                "Step 3: Simplify √50: √50 = √(25 × 2) = 5√2. Since √2 is "
                "irrational, multiplying it by 5 still gives an irrational number.\n"
                "Answer: √50 is irrational."
            )
            wrong = ["√36", "√49", "0.5"]
        elif form == 2:
            answer = "√36"
            prompt = "Which number is rational: √36, √7, π, or √11?"
            solution = (
                "A rational number can be written as a fraction of integers.\n"
                "√36 = 6, and 6 = 6/1, so it is rational.\n"
                "√7 and √11 are irrational because 7 and 11 are not perfect squares; "
                "π is also irrational.\n"
                "Answer: √36 is rational."
            )
            wrong = ["√7", "π", "√11"]
        else:
            first_root = 8 + round_number % 4
            second_root = 3 + round_number % 3
            first_square = first_root * first_root
            second_square = second_root * second_root
            answer = first_root - second_root
            prompt = f"Evaluate √{first_square} − √{second_square}."
            solution = (
                "Simplify each square root before subtracting:\n"
                f"√{first_square} = {first_root} because {first_root}² = {first_square}.\n"
                f"√{second_square} = {second_root} because {second_root}² = {second_square}.\n"
                f"Subtract: {first_root} − {second_root} = {answer}."
            )
            wrong = [answer + 1, answer - 1, first_root + second_root]
        return make_question(kind, prompt, answer, wrong, solution, difficulty, variant)

    if "simultaneous" in title:
        x, y = 3 + round_number, 2 + round_number % 5
        if form in (0, 1):
            total, difference = x + y, x - y
            requested = "y" if form == 0 else "x"
            answer = y if form == 0 else x
            prompt = (
                f"Solve x + y = {total} and x − y = {difference}. "
                f"Find {requested}."
            )
            solution = (
                "Add the equations; +y and −y cancel:\n"
                f"(x + y) + (x − y) = {total} + {difference}, so "
                f"2x = {total + difference} and x = {x}.\n"
                f"Substitute into x + y = {total}: {x} + y = {total}, "
                f"so y = {total} − {x} = {y}.\n"
                f"Check: {x} + {y} = {total}; {x} − {y} = {difference}.\n"
                f"Answer: {requested} = {answer}."
            )
        elif form == 2:
            x = 4 + round_number
            y = 3 + round_number % 4
            total = 2 * x + y
            difference = x - y
            answer = x
            prompt = f"Solve this pair: 2x + y = {total}, x − y = {difference}. Find x."
            solution = (
                f"Double the second equation: 2x − 2y = {2 * difference}.\n"
                f"Subtract it from the first: (2x + y) − (2x − 2y) = "
                f"{total} − {2 * difference}, so 3y = {total - 2 * difference}.\n"
                f"Thus y = {y}. Put this into x − y = {difference}: "
                f"x − {y} = {difference}, so x = {answer}.\n"
                f"Check: 2 × {answer} + {y} = {total}."
            )
        else:
            x = 5 + round_number
            y = 2 + round_number % 4
            first_total = x + 2 * y
            second_total = 3 * x + y
            answer = x
            prompt = (
                f"Find x from x + 2y = {first_total} and "
                f"3x + y = {second_total}."
            )
            solution = (
                f"Double the second equation to make the y-terms match: "
                f"6x + 2y = {2 * second_total}.\n"
                f"Subtract the first equation: 5x = {2 * second_total} − "
                f"{first_total} = {5 * answer}.\n"
                f"Divide by 5: x = {5 * answer} ÷ 5 = {answer}.\n"
                f"Answer: x = {answer}."
            )
        return make_question(
            kind,
            prompt,
            answer,
            [answer + 1, answer - 1, answer + 2],
            solution,
            difficulty,
            variant,
        )

    answer = 2 + round_number
    form = variant % 4
    if form == 0:
        prompt = f"Calculate {answer} + {round_number}."
        solution = (
            f"Step 1: The calculation starts with {answer} and adds {round_number}.\n"
            f"Step 2: Adding means combine the amounts: {answer} + {round_number} = "
            f"{answer + round_number}.\n"
            f"Check: Subtracting {round_number} from {answer + round_number} gives "
            f"{answer} again.\n"
            f"Answer: {answer + round_number}."
        )
    elif form == 1:
        prompt = (
            f"A class has {answer} pencils and receives {round_number} more. "
            "How many pencils are there altogether?"
        )
        solution = (
            f"The question asks for the total, so we add the two amounts: "
            f"{answer} + {round_number} = {answer + round_number}.\n"
            f"Check: {answer + round_number} − {round_number} = {answer}.\n"
            f"Answer: {answer + round_number} pencils."
        )
    elif form == 2:
        prompt = f"Which number sentence matches this story: {answer} + {round_number} = ?"
        solution = (
            f"The story tells us to combine {answer} and {round_number}.\n"
            f"Adding gives {answer + round_number}.\n"
            f"The matching sentence is {answer} + {round_number} = {answer + round_number}."
        )
    else:
        prompt = (
            f"Find the missing value: {answer} + {round_number} = □. "
            "Then explain how you checked your answer."
        )
        solution = (
            f"Start with {answer} and add {round_number}: {answer} + {round_number} = "
            f"{answer + round_number}.\n"
            f"To check, subtract {round_number} from {answer + round_number}: "
            f"{answer + round_number} − {round_number} = {answer}.\n"
            f"So the missing value is {answer + round_number}."
        )
    return make_question(
        kind,
        prompt,
        answer + round_number,
        [answer, answer + round_number + 1, answer - 1],
        solution,
        difficulty,
        variant,
    )


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
