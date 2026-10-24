from django.db import migrations


PAPER_QUESTIONS = [
    {
        "prompt": (
            "1.\n"
            "(a) Let A = {1, 2, 3, …, 12}. List all the prime numbers in A. [2 marks]\n"
            "(b) A number is chosen at random from A. Find the probability that it is not a prime number. [2 marks]\n"
            "(c) Factorise completely: 6x² − 9xy. [2 marks]\n"
            "(d) A printer charges GH₵ 45 for the first 5 posters and GH₵ 7 for each extra poster. Find the cost of printing 17 posters. [4 marks]"
        ),
        "difficulty": "medium",
        "rubric": (
            "Total: 10 marks. (a) 2 marks for the complete list. "
            "(b) 1 mark for counting the outcomes and 1 for the probability. "
            "(c) 1 mark for the highest common factor and 1 for the bracket. "
            "(d) 1 mark for finding extra posters, 1 for their cost, 1 for adding the first charge, and 1 for GH₵ 129."
        ),
        "expected_answer": (
            "(a) {2, 3, 5, 7, 11}. (b) 7/12. (c) 3x(2x − 3y). "
            "(d) GH₵ 129."
        ),
        "explanation": (
            "Question 1 — worked solution for a learner\n\n"
            "(a) Find the prime numbers\n"
            "Step 1: A prime number is a whole number greater than 1 that has exactly two factors: 1 and itself. The number 1 is not prime.\n"
            "Step 2: Check the numbers from 2 to 12. The primes are 2, 3, 5, 7 and 11. For example, 9 is not prime because 3 × 3 = 9; 10 is not prime because 2 × 5 = 10.\n"
            "Answer: {2, 3, 5, 7, 11}.\n\n"
            "(b) Find the probability of choosing a number that is not prime\n"
            "Step 1: A contains 12 numbers altogether, so there are 12 possible choices.\n"
            "Step 2: There are 5 primes. The numbers that are not prime are 1, 4, 6, 8, 9, 10 and 12: 7 numbers.\n"
            "Step 3: Probability = number of wanted choices ÷ number of all choices = 7 ÷ 12.\n"
            "Answer: 7/12.\n\n"
            "(c) Factorise 6x² − 9xy\n"
            "Step 1: Factorising means taking out a factor shared by every term.\n"
            "Step 2: Both 6x² and 9xy can be divided by 3x. Take 3x outside the bracket.\n"
            "Step 3: 6x² ÷ 3x = 2x, and 9xy ÷ 3x = 3y. Keep the minus sign: 3x(2x − 3y).\n"
            "Check: 3x × 2x − 3x × 3y = 6x² − 9xy.\n"
            "Answer: 3x(2x − 3y).\n\n"
            "(d) Find the printing cost\n"
            "Step 1: The first 5 posters cost GH₵ 45. The total is 17 posters, so the extra posters are 17 − 5 = 12.\n"
            "Step 2: Each extra poster costs GH₵ 7. The extra charge is 12 × 7 = GH₵ 84.\n"
            "Step 3: Add the first charge and extra charge: GH₵ 45 + GH₵ 84 = GH₵ 129.\n"
            "Answer: The total cost is GH₵ 129."
        ),
    },
    {
        "prompt": (
            "2.\n"
            "(a) Share GH₵ 840 between Kena and Yaw in the ratio 3 : 4. Find each person's share. [4 marks]\n"
            "(b) A trader buys a bag for GH₵ 240 and sells it for GH₵ 300. Find the profit and the percentage profit. [3 marks]\n"
            "(c) GH₵ 500 is invested at 6% simple interest per year for 2 years. Find the interest and the total amount after 2 years. [3 marks]"
        ),
        "difficulty": "medium",
        "rubric": (
            "Total: 10 marks. (a) 1 mark for total parts, 1 for one-part value, and 1 each for the two shares. "
            "(b) 1 mark for the profit, 1 for using cost price as the base, and 1 for 25%. "
            "(c) 1 mark for the simple-interest method, 1 for GH₵ 60 interest, and 1 for GH₵ 560 total."
        ),
        "expected_answer": (
            "(a) Kena: GH₵ 360; Yaw: GH₵ 480. (b) Profit: GH₵ 60; percentage profit: 25%. "
            "(c) Interest: GH₵ 60; total amount: GH₵ 560."
        ),
        "explanation": (
            "Question 2 — worked solution for a learner\n\n"
            "(a) Share GH₵ 840 in the ratio 3 : 4\n"
            "Step 1: The ratio has 3 parts for Kena and 4 parts for Yaw. Total parts = 3 + 4 = 7.\n"
            "Step 2: Find the value of one part: GH₵ 840 ÷ 7 = GH₵ 120.\n"
            "Step 3: Kena gets 3 parts: 3 × GH₵ 120 = GH₵ 360.\n"
            "Step 4: Yaw gets 4 parts: 4 × GH₵ 120 = GH₵ 480.\n"
            "Check: GH₵ 360 + GH₵ 480 = GH₵ 840, the whole amount.\n\n"
            "(b) Find profit and percentage profit\n"
            "Step 1: Profit is the amount left after taking away the buying cost. Profit = selling price − cost price.\n"
            "Step 2: GH₵ 300 − GH₵ 240 = GH₵ 60 profit.\n"
            "Step 3: Percentage profit is compared with the cost price (the original buying price), not the selling price.\n"
            "Step 4: Percentage profit = (profit ÷ cost price) × 100 = (60 ÷ 240) × 100 = 25%.\n"
            "Answer: The profit is GH₵ 60 and the percentage profit is 25%.\n\n"
            "(c) Find simple interest and total amount\n"
            "Step 1: Simple interest is calculated on the original amount each year. Use I = (P × R × T) ÷ 100, where P is the money invested, R is the yearly rate, and T is time in years.\n"
            "Step 2: Substitute P = 500, R = 6 and T = 2: I = (500 × 6 × 2) ÷ 100.\n"
            "Step 3: 500 × 6 × 2 = 6,000; 6,000 ÷ 100 = GH₵ 60 interest.\n"
            "Step 4: Total amount = original investment + interest = GH₵ 500 + GH₵ 60 = GH₵ 560."
        ),
    },
    {
        "prompt": (
            "3.\n"
            "A rectangular garden is 12 m long and 8 m wide. A square flower bed of side 3 m is built inside the garden.\n"
            "(a) Find the area of the whole garden. [2 marks]\n"
            "(b) Find the area of the square flower bed. [2 marks]\n"
            "(c) Find the area left for grass. [2 marks]\n"
            "(d) A fence is placed all the way around the outside of the garden. Find the fence length. [2 marks]\n"
            "(e) Fencing costs GH₵ 18 per metre. Find the total fencing cost. [2 marks]"
        ),
        "difficulty": "medium",
        "rubric": (
            "Total: 10 marks. Award 2 marks each for (a) 96 m², (b) 9 m², (c) 87 m², (d) 40 m, and (e) GH₵ 720. "
            "For method marks, accept correct formulae and substitutions even if an earlier arithmetic error carries through."
        ),
        "expected_answer": (
            "(a) 96 m². (b) 9 m². (c) 87 m². (d) 40 m. (e) GH₵ 720."
        ),
        "explanation": (
            "Question 3 — worked solution for a learner\n\n"
            "(a) Area of the garden\n"
            "Step 1: A rectangle's area is length × width. Area tells how much flat space covers the floor or ground.\n"
            "Step 2: 12 m × 8 m = 96 m². The unit is square metres because we multiply metres by metres.\n\n"
            "(b) Area of the square flower bed\n"
            "Step 1: A square has four equal sides. Its area is side × side.\n"
            "Step 2: 3 m × 3 m = 9 m².\n\n"
            "(c) Area left for grass\n"
            "Step 1: The garden's total area includes the flower bed.\n"
            "Step 2: Subtract the flower-bed area: 96 m² − 9 m² = 87 m².\n"
            "Answer: 87 m² is left for grass.\n\n"
            "(d) Fence length around the outside\n"
            "Step 1: The fence goes around the garden's outside edge, so we need the rectangle's perimeter. Do not subtract the flower bed; it is inside.\n"
            "Step 2: Perimeter = 2 × (length + width) = 2 × (12 + 8) = 2 × 20 = 40 m.\n\n"
            "(e) Cost of the fence\n"
            "Step 1: Each metre costs GH₵ 18 and we need 40 metres.\n"
            "Step 2: Total cost = 40 × GH₵ 18 = GH₵ 720.\n"
            "Answer: The fencing costs GH₵ 720."
        ),
    },
    {
        "prompt": (
            "4.\n"
            "(a) Solve the simultaneous equations x + y = 17 and x − y = 5. [4 marks]\n"
            "(b) The length of a rectangle is 3 cm more than its width. Its perimeter is 30 cm. Find its length and width. [4 marks]\n"
            "(c) Find the value of 2a² − b when a = 3 and b = 4. [2 marks]"
        ),
        "difficulty": "hard",
        "rubric": (
            "Total: 10 marks. (a) 1 mark for adding/eliminating, 1 for 2x = 22, and 1 each for x = 11, y = 6. "
            "(b) 1 mark for defining a variable, 1 for using the perimeter, 1 for width 6 cm, and 1 for length 9 cm. "
            "(c) 1 mark for correct substitution and 1 for 14."
        ),
        "expected_answer": (
            "(a) x = 11, y = 6. (b) Width = 6 cm, length = 9 cm. (c) 14."
        ),
        "explanation": (
            "Question 4 — worked solution for a learner\n\n"
            "(a) Solve x + y = 17 and x − y = 5\n"
            "Step 1: Write the equations underneath each other: x + y = 17 and x − y = 5.\n"
            "Step 2: Add the equations. The +y and −y cancel, leaving 2x = 22.\n"
            "Step 3: Divide both sides by 2: x = 11.\n"
            "Step 4: Put x = 11 into the first equation: 11 + y = 17, so y = 6.\n"
            "Check: 11 − 6 = 5. Both equations are true.\n\n"
            "(b) Find the rectangle's length and width\n"
            "Step 1: Let the width be w cm. The length is 3 cm more, so length = w + 3.\n"
            "Step 2: Perimeter = 2(length + width). Put in the perimeter of 30 cm: 2((w + 3) + w) = 30.\n"
            "Step 3: Collect like terms inside the brackets: 2(2w + 3) = 30. Divide both sides by 2: 2w + 3 = 15.\n"
            "Step 4: Subtract 3: 2w = 12. Divide by 2: w = 6 cm.\n"
            "Step 5: The length is 3 cm more: 6 + 3 = 9 cm.\n"
            "Check: 2(9 + 6) = 30 cm.\n\n"
            "(c) Evaluate 2a² − b\n"
            "Step 1: Replace a with 3 and b with 4: 2 × 3² − 4.\n"
            "Step 2: Work out the square first: 3² = 3 × 3 = 9.\n"
            "Step 3: Multiply, then subtract: 2 × 9 − 4 = 18 − 4 = 14."
        ),
    },
    {
        "prompt": (
            "5.\n"
            "(a) A circular pond has radius 7 m. Find its circumference using π = 22/7. [2 marks]\n"
            "(b) A cuboid storage box is 1.2 m long, 0.5 m wide and 0.4 m high. Find its volume. [3 marks]\n"
            "(c) A right-angled ramp rises 1.5 m over a horizontal distance of 2 m. Find the length of the ramp, correct to 2 decimal places. [3 marks]\n"
            "(d) Convert 2.4 m to centimetres. [2 marks]"
        ),
        "difficulty": "hard",
        "rubric": (
            "Total: 10 marks. (a) 1 mark for circumference formula and 1 for 44 m. "
            "(b) 1 mark for multiplying all three dimensions, 1 for 0.24, and 1 for m³. "
            "(c) 1 mark for identifying the right-triangle rule, 1 for 6.25, and 1 for 2.50 m. "
            "(d) 1 mark for using 100 cm per metre and 1 for 240 cm."
        ),
        "expected_answer": (
            "(a) 44 m. (b) 0.24 m³. (c) 2.50 m. (d) 240 cm."
        ),
        "explanation": (
            "Question 5 — worked solution for a learner\n\n"
            "(a) Circumference of the pond\n"
            "Step 1: The circumference is the distance all the way around a circle. Use C = 2πr, where r means radius.\n"
            "Step 2: Substitute r = 7 m and π = 22/7: C = 2 × 22/7 × 7.\n"
            "Step 3: The 7 on top and 7 on the bottom cancel. Then 2 × 22 = 44.\n"
            "Answer: The circumference is 44 m.\n\n"
            "(b) Volume of the storage box\n"
            "Step 1: Volume is the space inside a solid box. For a cuboid, volume = length × width × height.\n"
            "Step 2: Multiply: 1.2 × 0.5 = 0.6; then 0.6 × 0.4 = 0.24.\n"
            "Step 3: Each measurement is in metres, so the volume unit is cubic metres: m × m × m = m³.\n"
            "Answer: 0.24 m³.\n\n"
            "(c) Length of the ramp\n"
            "Step 1: The ramp, the ground and the vertical rise make a right-angled triangle. The ramp is the sloping side, opposite the right angle.\n"
            "Step 2: For a right-angled triangle, (sloping side)² = (horizontal side)² + (vertical side)².\n"
            "Step 3: Ramp² = 2² + 1.5² = 4 + 2.25 = 6.25.\n"
            "Step 4: The number that multiplies by itself to make 6.25 is 2.5, because 2.5 × 2.5 = 6.25.\n"
            "Answer: The ramp is 2.50 m long to 2 decimal places.\n\n"
            "(d) Convert metres to centimetres\n"
            "Step 1: 1 metre = 100 centimetres.\n"
            "Step 2: Multiply by 100: 2.4 × 100 = 240.\n"
            "Answer: 2.4 m = 240 cm."
        ),
    },
    {
        "prompt": (
            "6.\n"
            "The table shows the number of books read by learners in one month.\n"
            "Books read:       0     1     2     3     4\n"
            "Number of learners: 2     3     6     5     4\n"
            "(a) How many learners were surveyed? [2 marks]\n"
            "(b) Which number of books was read by the greatest number of learners? [2 marks]\n"
            "(c) Find the mean number of books read. [3 marks]\n"
            "(d) One learner is chosen at random. Find the probability that the learner read at least 3 books. [3 marks]"
        ),
        "difficulty": "hard",
        "rubric": (
            "Total: 10 marks. (a) 1 mark for adding the frequencies and 1 for 20. "
            "(b) 1 mark for identifying the greatest frequency and 1 for 2 books. "
            "(c) 1 mark for using books × learners, 1 for total 46, and 1 for 2.3. "
            "(d) 1 mark for counting learners who read 3 or 4 books, 1 for 9/20, and 1 for a correct probability."
        ),
        "expected_answer": (
            "(a) 20 learners. (b) 2 books. (c) Mean = 2.3 books. (d) 9/20."
        ),
        "explanation": (
            "Question 6 — worked solution for a learner\n\n"
            "(a) Number of learners\n"
            "Step 1: The second row tells how many learners are in each group.\n"
            "Step 2: Add those numbers: 2 + 3 + 6 + 5 + 4 = 20.\n"
            "Answer: 20 learners were surveyed.\n\n"
            "(b) Most common number of books\n"
            "Step 1: Compare the numbers of learners: 2, 3, 6, 5 and 4.\n"
            "Step 2: The greatest number is 6. It lines up with 2 books in the first row.\n"
            "Answer: The most common number is 2 books. This is called the mode.\n\n"
            "(c) Mean number of books\n"
            "Step 1: For a frequency table, multiply each number of books by the number of learners who read that many books.\n"
            "Step 2: 0 × 2 = 0; 1 × 3 = 3; 2 × 6 = 12; 3 × 5 = 15; 4 × 4 = 16.\n"
            "Step 3: Add these totals: 0 + 3 + 12 + 15 + 16 = 46 books.\n"
            "Step 4: Divide by all 20 learners: 46 ÷ 20 = 2.3.\n"
            "Answer: The mean is 2.3 books per learner.\n\n"
            "(d) Probability of reading at least 3 books\n"
            "Step 1: “At least 3” means 3 or more, so include the learners who read 3 books and those who read 4 books.\n"
            "Step 2: Those groups contain 5 + 4 = 9 learners.\n"
            "Step 3: There are 20 learners in total. Probability = wanted learners ÷ all learners = 9/20.\n"
            "Answer: 9/20."
        ),
    },
]


def add_written_paper(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    Topic = apps.get_model("learning", "Topic")
    Question = apps.get_model("learning", "Question")
    mathematics = Subject.objects.get(slug="mathematics")
    topic, _ = Topic.objects.get_or_create(
        subject=mathematics,
        slug="g9-paper-2-written-practice",
        defaults={
            "title": "BECE Paper 2: Structured Mathematics",
            "summary": (
                "Practise longer, multi-part mathematics questions. Choose four of the six "
                "questions, show each step, and use the mark guide to check your work."
            ),
            "content": (
                "Paper 2 practice: There are six questions. Choose any four. Each question "
                "has several parts and is worth 10 marks. Show your working clearly. Your "
                "written work is saved but not automatically graded; compare it with the "
                "worked solution and mark guide after submitting."
            ),
            "grade": 9,
            "term": 3,
            "position": 100,
            "is_published": True,
        },
    )
    for prompt, data in ((item["prompt"], item) for item in PAPER_QUESTIONS):
        Question.objects.get_or_create(
            topic=topic,
            prompt=prompt,
            defaults={
                "kind": "theory",
                "options": [],
                "correct_answer": "",
                "expected_answer": data["expected_answer"],
                "rubric": data["rubric"],
                "explanation": data["explanation"],
                "difficulty": data["difficulty"],
                "is_published": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("learning", "0006_bece_style_mathematics_question_bank")]

    operations = [
        migrations.RunPython(add_written_paper, migrations.RunPython.noop),
    ]
