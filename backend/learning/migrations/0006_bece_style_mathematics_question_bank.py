import re

from django.db import migrations


EXTRA_QUESTIONS = [
    (
        "g7-whole-numbers-factors",
        "A school has 84 pencils and 126 pens. It wants to make the greatest possible number of identical prize packs, with no stationery left over. How many packs can it make?",
        ["14", "21", "42", "210"],
        "42",
        "mcq",
        [
            "The number of identical packs must divide both 84 and 126 exactly, so we need their highest common factor (HCF).",
            "Prime-factorise: 84 = 2 × 2 × 3 × 7, and 126 = 2 × 3 × 3 × 7.",
            "The factors shared by both numbers are 2, 3 and 7. Multiply them: 2 × 3 × 7 = 42.",
            "Check: 84 ÷ 42 = 2 pencils per pack and 126 ÷ 42 = 3 pens per pack, with nothing left over.",
        ],
        "medium",
    ),
    (
        "g7-ratio-rate-finance",
        "A recipe uses flour and sugar in the ratio 5 : 2. If 350 g of flour is used, how much sugar is needed?",
        ["70 g", "140 g", "175 g", "245 g"],
        "140 g",
        "mcq",
        [
            "The ratio 5 : 2 means 5 equal parts of flour match 2 equal parts of sugar.",
            "The 5 flour parts weigh 350 g, so one part weighs 350 ÷ 5 = 70 g.",
            "Sugar is 2 parts, so its mass is 2 × 70 g = 140 g.",
            "Check: 350 : 140 simplifies to 5 : 2.",
        ],
        "medium",
    ),
    (
        "g7-fractions-percentages",
        "A water tank is 3/5 full. What fraction of the tank is empty?",
        ["1/5", "2/5", "3/5", "5/8"],
        "2/5",
        "mcq",
        [
            "A full tank represents 1 whole, which is the same as 5/5.",
            "The full part is 5/5 and the water takes 3/5.",
            "Subtract the filled part: 5/5 − 3/5 = 2/5.",
            "So 2/5 of the tank is empty. The filled and empty parts add to 3/5 + 2/5 = 5/5.",
        ],
        "easy",
    ),
    (
        "g7-decimal-fractions",
        "A student buys 3 exercise books at GH₵4.75 each. How much does the student pay?",
        ["GH₵12.25", "GH₵13.25", "GH₵14.25", "GH₵15.75"],
        "GH₵14.25",
        "theory",
        [
            "Each book costs GH₵4.75, and there are 3 books. Multiply 4.75 by 3.",
            "Multiply the whole-number parts: 4 × 3 = 12.",
            "Multiply the decimal parts: 0.75 × 3 = 2.25.",
            "Add the two parts: GH₵12 + GH₵2.25 = GH₵14.25.",
            "Check: 3 × GH₵5 would be GH₵15, so a total slightly below GH₵15 is reasonable.",
        ],
        "easy",
    ),
    (
        "g7-exponents-squares-cubes",
        "A square garden has a side length of 9 m. What is its area?",
        ["18 m²", "36 m²", "72 m²", "81 m²"],
        "81 m²",
        "mcq",
        [
            "The area of a square is side length multiplied by side length.",
            "Put 9 m into both places: area = 9 m × 9 m.",
            "Multiply 9 × 9 = 81, and m × m = m².",
            "Therefore, the area is 81 m².",
        ],
        "easy",
    ),
    (
        "g7-integers",
        "At dawn the temperature is −3°C. It rises by 8°C and then falls by 4°C. What is the final temperature?",
        ["−15°C", "−1°C", "1°C", "9°C"],
        "1°C",
        "theory",
        [
            "Start at −3°C. A rise means add, so the next temperature is −3 + 8.",
            "Calculate −3 + 8 = 5°C.",
            "A fall means subtract 4: 5 − 4 = 1°C.",
            "The final temperature is 1°C. Check the changes together: +8 − 4 = +4, and −3 + 4 = 1.",
        ],
        "easy",
    ),
    (
        "g7-patterns",
        "A pattern is 5, 9, 13, 17, … . What is the 15th term?",
        ["57", "61", "65", "69"],
        "61",
        "mcq",
        [
            "Compare neighbouring terms: 9 − 5 = 4, 13 − 9 = 4 and 17 − 13 = 4. The pattern adds 4 each time.",
            "From term 1 to term 15 there are 14 jumps.",
            "The total increase is 14 × 4 = 56.",
            "Start with the first term: 5 + 56 = 61.",
            "Therefore, the 15th term is 61.",
        ],
        "medium",
    ),
    (
        "g7-constructions",
        "A learner constructs the perpendicular bisector of a 10 cm line segment. How far from either endpoint is the midpoint?",
        ["2 cm", "5 cm", "10 cm", "20 cm"],
        "5 cm",
        "mcq",
        [
            "A perpendicular bisector meets a line segment at its midpoint and makes a right angle.",
            "A midpoint divides the whole length into two equal parts.",
            "Divide 10 cm by 2: 10 ÷ 2 = 5 cm.",
            "The midpoint is 5 cm from each endpoint.",
        ],
        "easy",
    ),
    (
        "g7-2d-shapes-angles",
        "Two angles on a straight line are (3x)° and 60°. Find x.",
        ["30", "40", "60", "120"],
        "40",
        "theory",
        [
            "Angles on a straight line add up to 180°.",
            "Write an equation: 3x + 60 = 180.",
            "Subtract 60 from both sides: 3x = 120.",
            "Divide both sides by 3: x = 40.",
            "Check: 3 × 40 = 120, and 120° + 60° = 180°.",
        ],
        "medium",
    ),
    (
        "g7-measurement",
        "A rectangular classroom floor is 8 m long and 5 m wide. What is its perimeter?",
        ["13 m", "26 m", "40 m", "80 m"],
        "26 m",
        "mcq",
        [
            "Perimeter is the distance all the way around a shape.",
            "A rectangle has two lengths and two widths, so add 8 + 5 + 8 + 5.",
            "The total is 26 m.",
            "Check with the shortcut: 2 × (8 + 5) = 2 × 13 = 26 m.",
        ],
        "easy",
    ),
    (
        "g7-data-handling",
        "The scores are 6, 8, 9, 5 and 7. Find their mean.",
        ["6", "7", "8", "35"],
        "7",
        "mcq",
        [
            "The mean is the total of the scores divided by the number of scores.",
            "Add the scores: 6 + 8 + 9 + 5 + 7 = 35.",
            "There are 5 scores, so divide: 35 ÷ 5 = 7.",
            "The mean score is 7.",
        ],
        "easy",
    ),
    (
        "g8-whole-numbers-factors",
        "Two bells ring every 12 minutes and 18 minutes. If they ring together now, after how many minutes will they next ring together?",
        ["6 minutes", "30 minutes", "36 minutes", "216 minutes"],
        "36 minutes",
        "theory",
        [
            "We need the first time that is a multiple of both 12 and 18. This is their lowest common multiple (LCM).",
            "List multiples of 12: 12, 24, 36, 48, …",
            "List multiples of 18: 18, 36, 54, …",
            "The first shared multiple is 36.",
            "So the bells next ring together after 36 minutes.",
        ],
        "medium",
    ),
    (
        "g8-exponents",
        "Simplify (3²)³.",
        ["3⁵", "3⁶", "9⁵", "9⁶"],
        "3⁶",
        "mcq",
        [
            "The power outside the brackets applies to the power inside.",
            "When a power is raised to another power, multiply the exponents: (aᵐ)ⁿ = aᵐˣⁿ.",
            "So (3²)³ = 3²ˣ³ = 3⁶.",
            "Check by expanding: (3 × 3) × (3 × 3) × (3 × 3) has six factors of 3.",
        ],
        "medium",
    ),
    (
        "g8-patterns",
        "The nth term of a pattern is 5n − 2. Find the 18th term.",
        ["80", "86", "88", "92"],
        "88",
        "mcq",
        [
            "The 18th term means replace n with 18.",
            "Calculate 5 × 18 = 90.",
            "Subtract 2: 90 − 2 = 88.",
            "Therefore, the 18th term is 88.",
        ],
        "easy",
    ),
    (
        "g8-algebraic-expressions",
        "Simplify 4a + 3b − 2a + 5b.",
        ["2a + 8b", "6a + 2b", "2a + 2b", "9ab"],
        "2a + 8b",
        "theory",
        [
            "Like terms have the same letter. Group the a-terms and the b-terms: (4a − 2a) + (3b + 5b).",
            "Subtract the a coefficients: 4 − 2 = 2, giving 2a.",
            "Add the b coefficients: 3 + 5 = 8, giving 8b.",
            "The simplified expression is 2a + 8b. We cannot combine a-terms with b-terms.",
        ],
        "easy",
    ),
    (
        "g8-fractions-decimals",
        "Calculate 2.4 ÷ 0.6.",
        ["0.4", "4", "14.4", "40"],
        "4",
        "mcq",
        [
            "A divisor is easier to use when it is a whole number. Multiply both numbers by 10.",
            "Multiplying both numbers by the same amount keeps the quotient unchanged: 2.4 ÷ 0.6 = 24 ÷ 6.",
            "Now divide: 24 ÷ 6 = 4.",
            "Check: 0.6 × 4 = 2.4.",
        ],
        "easy",
    ),
    (
        "g8-ratio-rate",
        "A map uses a scale of 1 cm to 5 km. Two towns are 7 cm apart on the map. What is their actual distance?",
        ["12 km", "25 km", "35 km", "70 km"],
        "35 km",
        "mcq",
        [
            "Each centimetre on the map represents 5 km in real life.",
            "The map distance is 7 cm, so multiply 7 by 5 km for each centimetre.",
            "7 × 5 km = 35 km.",
            "The actual distance is 35 km.",
        ],
        "medium",
    ),
    (
        "g8-algebraic-equations",
        "Solve 5x − 8 = 27.",
        ["x = 5", "x = 7", "x = 19", "x = 35"],
        "x = 7",
        "theory",
        [
            "We want x by itself. First undo the subtraction of 8 by adding 8 to both sides.",
            "5x − 8 + 8 = 27 + 8, so 5x = 35.",
            "Undo multiplication by 5 by dividing both sides by 5: x = 35 ÷ 5 = 7.",
            "Check in the original equation: 5 × 7 − 8 = 35 − 8 = 27.",
            "Therefore, x = 7.",
        ],
        "easy",
    ),
    (
        "g8-constructions",
        "A triangle has side lengths 4 cm, 6 cm and x cm. Which value of x can form a triangle?",
        ["2 cm", "3 cm", "10 cm", "11 cm"],
        "3 cm",
        "mcq",
        [
            "For three lengths to make a triangle, the two shorter sides must add to more than the longest side.",
            "The remaining side must be greater than the difference of 6 and 4: x > 2.",
            "It must also be less than their sum: x < 10.",
            "So x must be between 2 cm and 10 cm, not including the ends. Of the options, only 3 cm works.",
        ],
        "medium",
    ),
    (
        "g8-2d-shapes-straight-lines",
        "An isosceles triangle has a vertex angle of 40°. Find each of its equal base angles.",
        ["40°", "70°", "80°", "140°"],
        "70°",
        "theory",
        [
            "The angles inside every triangle add up to 180°.",
            "The two equal base angles share the remaining amount: 180° − 40° = 140°.",
            "Divide equally between the two base angles: 140° ÷ 2 = 70°.",
            "Each base angle is 70°. Check: 40° + 70° + 70° = 180°.",
        ],
        "medium",
    ),
    (
        "g8-measurement",
        "A rectangle has an area of 96 cm² and a width of 8 cm. Find its length.",
        ["12 cm", "16 cm", "88 cm", "768 cm"],
        "12 cm",
        "mcq",
        [
            "For a rectangle, area = length × width.",
            "Put in the known values: 96 = length × 8.",
            "Divide both sides by 8: length = 96 ÷ 8 = 12.",
            "The length is 12 cm. Check: 12 × 8 = 96 cm².",
        ],
        "easy",
    ),
    (
        "g8-data-handling",
        "Find the median of 3, 11, 7, 5 and 9.",
        ["5", "7", "9", "11"],
        "7",
        "mcq",
        [
            "The median is the middle value after the numbers are put in order.",
            "Order them from smallest to largest: 3, 5, 7, 9, 11.",
            "There are 5 values, so the third value is in the middle.",
            "The median is 7.",
        ],
        "easy",
    ),
    (
        "g9-real-numbers-integers",
        "Evaluate 18 − 3(4 − 7).",
        ["9", "21", "27", "33"],
        "27",
        "mcq",
        [
            "Work inside the brackets first: 4 − 7 = −3.",
            "Multiply next: 3 × (−3) = −9.",
            "Now calculate 18 − (−9). Subtracting a negative is the same as adding: 18 + 9 = 27.",
            "The answer is 27.",
        ],
        "medium",
    ),
    (
        "g9-exponents",
        "Simplify 2⁵ × 2³ ÷ 2⁴.",
        ["2²", "2⁴", "2⁸", "2¹²"],
        "2⁴",
        "theory",
        [
            "All the powers have the same base, 2. When multiplying, add the exponents: 5 + 3 = 8.",
            "The expression becomes 2⁸ ÷ 2⁴.",
            "When dividing powers with the same base, subtract the exponents: 8 − 4 = 4.",
            "So the simplified answer is 2⁴, which equals 16.",
            "Check: 2⁵ × 2³ ÷ 2⁴ = 32 × 8 ÷ 16 = 16.",
        ],
        "medium",
    ),
    (
        "g9-patterns",
        "The first three terms of a pattern are 7, 12, 17. Find an expression for the nth term.",
        ["5n + 2", "5n − 2", "7n + 5", "12n − 5"],
        "5n + 2",
        "mcq",
        [
            "Find the common difference: 12 − 7 = 5 and 17 − 12 = 5. The pattern increases by 5 each time.",
            "Start the rule with 5n because the amount added each time is 5.",
            "Use the first term, where n = 1: 5 × 1 = 5. To reach 7, add 2.",
            "The rule is 5n + 2.",
            "Check the next terms: n = 2 gives 12, and n = 3 gives 17.",
        ],
        "medium",
    ),
    (
        "g9-algebra-expressions-equations",
        "Solve 2(x + 3) = 18.",
        ["x = 3", "x = 6", "x = 9", "x = 12"],
        "x = 6",
        "theory",
        [
            "The 2 multiplies everything inside the brackets: 2(x + 3) = 2x + 6.",
            "So 2x + 6 = 18. Subtract 6 from both sides: 2x = 12.",
            "Divide both sides by 2: x = 6.",
            "Check: 2(6 + 3) = 2 × 9 = 18.",
            "Therefore, x = 6.",
        ],
        "easy",
    ),
    (
        "g9-2d-shapes-measurement",
        "A circle has diameter 14 cm. Using π = 22/7, find its circumference.",
        ["22 cm", "44 cm", "154 cm", "308 cm"],
        "44 cm",
        "mcq",
        [
            "The circumference is the distance around a circle. Use circumference = π × diameter.",
            "The diameter is already given as 14 cm, so substitute: (22/7) × 14.",
            "Divide 14 by 7 to get 2, then multiply: 22 × 2 = 44.",
            "The circumference is 44 cm. It is measured in centimetres, not square centimetres.",
        ],
        "easy",
    ),
    (
        "g9-ratio-proportion-consumer-arithmetic",
        "A radio marked GH₵800 is sold at a 15% discount. What is the sale price?",
        ["GH₵120", "GH₵680", "GH₵785", "GH₵920"],
        "GH₵680",
        "mcq",
        [
            "First find the discount: 15% of GH₵800.",
            "10% of 800 is 80, and 5% is half of 10%, which is 40.",
            "So 15% is 80 + 40 = GH₵120.",
            "Subtract the discount from the marked price: GH₵800 − GH₵120 = GH₵680.",
            "The sale price is GH₵680.",
        ],
        "medium",
    ),
    (
        "g9-algebraic-fractions-simultaneous-equations",
        "Solve x + y = 13 and x − y = 5. Find y.",
        ["3", "4", "5", "9"],
        "4",
        "theory",
        [
            "Add the two equations. The +y and −y cancel each other.",
            "(x + y) + (x − y) = 13 + 5, so 2x = 18.",
            "Divide by 2: x = 9.",
            "Put x = 9 into x + y = 13: 9 + y = 13.",
            "Subtract 9 from both sides: y = 4.",
            "Check in the second equation: 9 − 4 = 5. Therefore, y = 4.",
        ],
        "medium",
    ),
    (
        "g9-variables-formulas",
        "The formula for the perimeter of a rectangle is P = 2l + 2w. Find P when l = 7 cm and w = 3 cm.",
        ["10 cm", "20 cm", "21 cm", "42 cm"],
        "20 cm",
        "mcq",
        [
            "Replace l with 7 and w with 3 in P = 2l + 2w.",
            "P = 2 × 7 + 2 × 3.",
            "Multiply first: 14 + 6 = 20.",
            "Perimeter is measured in centimetres, so P = 20 cm.",
        ],
        "easy",
    ),
    (
        "g9-straight-lines-polygons",
        "The interior angles of a quadrilateral are 85°, 95°, 110° and x°. Find x.",
        ["60°", "70°", "80°", "90°"],
        "70°",
        "theory",
        [
            "The interior angles of every quadrilateral add up to 360°.",
            "Add the three known angles: 85° + 95° + 110° = 290°.",
            "Subtract this total from 360°: x = 360° − 290° = 70°.",
            "Check: 85° + 95° + 110° + 70° = 360°.",
            "Therefore, x = 70°.",
        ],
        "medium",
    ),
    (
        "g9-surface-area-volume",
        "A cuboid measures 8 cm by 5 cm by 3 cm. Find its volume.",
        ["16 cm³", "40 cm³", "120 cm³", "240 cm³"],
        "120 cm³",
        "mcq",
        [
            "Volume measures the space inside a solid. For a cuboid, volume = length × width × height.",
            "Substitute the three measurements: 8 × 5 × 3.",
            "Multiply 8 × 5 = 40, then 40 × 3 = 120.",
            "The measurements are in centimetres, so volume is in cubic centimetres: 120 cm³.",
        ],
        "easy",
    ),
    (
        "g9-position-transformation",
        "Point A(−2, 5) is translated 4 units right and 3 units down. What are its new coordinates?",
        ["(2, 2)", "(2, 8)", "(−6, 2)", "(−6, 8)"],
        "(2, 2)",
        "mcq",
        [
            "Moving right increases the x-coordinate. Add 4 to −2: −2 + 4 = 2.",
            "Moving down decreases the y-coordinate. Subtract 3 from 5: 5 − 3 = 2.",
            "Write the new x-coordinate first and the new y-coordinate second.",
            "The new coordinates are (2, 2).",
        ],
        "medium",
    ),
    (
        "g9-data-probability",
        "A bag contains 4 red, 3 blue and 5 yellow counters. One counter is chosen at random. What is the probability that it is blue?",
        ["1/4", "1/3", "1/2", "5/12"],
        "1/4",
        "theory",
        [
            "Probability = number of favourable outcomes ÷ total number of equally likely outcomes.",
            "There are 3 blue counters, so there are 3 favourable outcomes.",
            "Count all counters: 4 + 3 + 5 = 12.",
            "The probability is 3/12. Divide the top and bottom by 3 to simplify: 3/12 = 1/4.",
            "So the probability of choosing blue is 1/4.",
        ],
        "easy",
    ),
]


def _vertical_steps(explanation, correct_answer):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])|\s*;\s*", explanation.strip())
    parts = [part.strip() for part in parts if part.strip()]
    lines = ["Let's work it out one step at a time."]
    lines.extend(f"Step {index}: {part}" for index, part in enumerate(parts, start=1))
    lines.append(f"Final answer: {correct_answer}")
    return "\n\n".join(lines)


def improve_existing_explanations(apps, schema_editor):
    Question = apps.get_model("learning", "Question")
    existing = Question.objects.filter(
        topic__subject__slug="mathematics",
        is_published=True,
    ).exclude(explanation="")
    for item in existing.iterator():
        if item.explanation.startswith("Let's work it out one step at a time."):
            continue
        item.explanation = _vertical_steps(item.explanation, item.correct_answer)
        item.save(update_fields=["explanation"])


def add_original_questions(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    Topic = apps.get_model("learning", "Topic")
    Question = apps.get_model("learning", "Question")
    Subject.objects.get(slug="mathematics")

    for topic_slug, prompt, options, answer, kind, steps, difficulty in EXTRA_QUESTIONS:
        topic = Topic.objects.get(
            slug=topic_slug,
            subject__slug="mathematics",
        )
        explanation = "\n\n".join(
            [f"Step {index}: {step}" for index, step in enumerate(steps, start=1)]
            + [f"Final answer: {answer}"]
        )
        Question.objects.get_or_create(
            topic=topic,
            prompt=prompt,
            defaults={
                "kind": kind,
                "options": options,
                "correct_answer": answer,
                "expected_answer": explanation if kind == "theory" else "",
                "rubric": (
                    "Award credit for a correct method, clearly shown steps, and the final answer."
                    if kind == "theory"
                    else ""
                ),
                "explanation": explanation,
                "difficulty": difficulty,
                "is_published": True,
            },
        )


def seed_mathematics_practice(apps, schema_editor):
    improve_existing_explanations(apps, schema_editor)
    add_original_questions(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [("learning", "0005_seed_jhs_mathematics_bank")]

    operations = [
        migrations.RunPython(seed_mathematics_practice, migrations.RunPython.noop),
    ]
