from django.db import migrations


PAPER_QUESTIONS = [
    {
        "prompt": (
            "A printer charges GH₵ 45 for the first 5 posters and GH₵ 7 for each "
            "additional poster. How much will it cost to print 17 posters?"
        ),
        "options": ["GH₵ 57", "GH₵ 84", "GH₵ 164", "GH₵ 129"],
        "correct_answer": "GH₵ 129",
        "expected_answer": "17 − 5 = 12 extra posters. 12 × GH₵ 7 = GH₵ 84. GH₵ 45 + GH₵ 84 = GH₵ 129.",
        "rubric": (
            "Working guide (10 marks): 2 marks for finding 12 extra posters; "
            "3 marks for calculating GH₵ 84 for the extra posters; "
            "3 marks for adding the GH₵ 45 first charge; "
            "2 marks for the final answer with the correct currency."
        ),
        "explanation": (
            "Work it out on paper first, then choose the matching answer.\n\n"
            "Step 1: The first 5 posters are already covered by the GH₵ 45 charge. "
            "So do not charge GH₵ 7 for those same 5 posters again.\n"
            "Step 2: Find how many posters are extra: 17 − 5 = 12 posters.\n"
            "Step 3: Each extra poster costs GH₵ 7. Multiply: 12 × 7 = GH₵ 84.\n"
            "Step 4: Add the first charge to the extra charge: GH₵ 45 + GH₵ 84 = GH₵ 129.\n"
            "Answer: GH₵ 129. Check: the cost is more than GH₵ 45 because there are extra posters."
        ),
        "difficulty": "medium",
    },
    {
        "prompt": (
            "Joyce and Richard invested GH₵ 10,000 and GH₵ 5,000 in a business. "
            "Richard first receives one-third of a GH₵ 9,000 profit for managing. "
            "The rest is shared in the ratio of their investments. How much does Richard receive altogether?"
        ),
        "options": ["GH₵ 3,000", "GH₵ 4,000", "GH₵ 5,000", "GH₵ 6,000"],
        "correct_answer": "GH₵ 5,000",
        "expected_answer": (
            "Manager's share = GH₵ 9,000 ÷ 3 = GH₵ 3,000. Remaining profit = GH₵ 6,000. "
            "Investment ratio = 2 : 1, so Richard's investment share = GH₵ 2,000. "
            "Richard receives GH₵ 3,000 + GH₵ 2,000 = GH₵ 5,000."
        ),
        "rubric": (
            "Working guide (10 marks): 2 marks for finding the manager's one-third; "
            "2 marks for finding the remaining profit; 2 marks for simplifying the "
            "investment ratio to 2 : 1; 2 marks for Richard's investment share; "
            "2 marks for his total share."
        ),
        "explanation": (
            "Work it out on paper first, then choose the matching answer.\n\n"
            "Step 1: Find Richard's manager's payment. One-third of GH₵ 9,000 is "
            "GH₵ 9,000 ÷ 3 = GH₵ 3,000.\n"
            "Step 2: This GH₵ 3,000 is taken out first. The profit left to share is "
            "GH₵ 9,000 − GH₵ 3,000 = GH₵ 6,000.\n"
            "Step 3: Simplify the investment ratio: GH₵ 10,000 : GH₵ 5,000 = 2 : 1. "
            "There are 3 parts altogether, and Richard has 1 part.\n"
            "Step 4: Find one part of the remaining GH₵ 6,000: GH₵ 6,000 ÷ 3 = GH₵ 2,000. "
            "Richard's investment share is GH₵ 2,000.\n"
            "Step 5: Add Richard's two payments: GH₵ 3,000 + GH₵ 2,000 = GH₵ 5,000.\n"
            "Answer: Richard receives GH₵ 5,000 altogether."
        ),
        "difficulty": "hard",
    },
    {
        "prompt": (
            "A worker earns GH₵ 25 per day. The daily wage increases by 10%. "
            "How much will the worker earn for 30 days at the new daily wage?"
        ),
        "options": ["GH₵ 750", "GH₵ 825", "GH₵ 850", "GH₵ 900"],
        "correct_answer": "GH₵ 825",
        "expected_answer": (
            "10% of GH₵ 25 = GH₵ 2.50. New daily wage = GH₵ 27.50. "
            "30 × GH₵ 27.50 = GH₵ 825."
        ),
        "rubric": (
            "Working guide (10 marks): 3 marks for finding the 10% increase; "
            "3 marks for adding it to the original daily wage; "
            "2 marks for multiplying by 30 days; 2 marks for the final amount."
        ),
        "explanation": (
            "Work it out on paper first, then choose the matching answer.\n\n"
            "Step 1: Find 10% of GH₵ 25. Ten percent means 10 out of every 100, "
            "or one-tenth. GH₵ 25 ÷ 10 = GH₵ 2.50.\n"
            "Step 2: Add the increase to the old wage: GH₵ 25 + GH₵ 2.50 = GH₵ 27.50 per day.\n"
            "Step 3: The worker earns this amount for 30 days, so multiply: "
            "GH₵ 27.50 × 30 = GH₵ 825.\n"
            "Answer: The worker earns GH₵ 825. Check: GH₵ 25 × 30 is GH₵ 750, "
            "so the increased total must be a little more than GH₵ 750."
        ),
        "difficulty": "medium",
    },
    {
        "prompt": (
            "A room has an L-shaped floor. It fits inside an 8 m by 5 m rectangle, "
            "but a 5 m by 2 m rectangle is cut out of one corner. Carpet costs "
            "GH₵ 20 per square metre. What is the cost to carpet the L-shaped floor?"
        ),
        "options": ["GH₵ 260", "GH₵ 520", "GH₵ 600", "GH₵ 800"],
        "correct_answer": "GH₵ 600",
        "expected_answer": (
            "Large rectangle area = 8 × 5 = 40 m². Cut-out area = 5 × 2 = 10 m². "
            "L-shaped floor area = 30 m². Carpet cost = 30 × GH₵ 20 = GH₵ 600."
        ),
        "rubric": (
            "Working guide (10 marks): 2 marks for the full rectangle area; "
            "2 marks for the cut-out area; 2 marks for subtracting to get the floor area; "
            "2 marks for multiplying by the cost per square metre; "
            "2 marks for the final cost with the correct currency."
        ),
        "explanation": (
            "Work it out on paper first, then choose the matching answer.\n\n"
            "Step 1: Imagine filling in the missing corner. The whole shape would then "
            "be a rectangle measuring 8 m by 5 m.\n"
            "Step 2: Find the area of that whole rectangle: 8 × 5 = 40 m².\n"
            "Step 3: Find the area of the missing corner: 5 × 2 = 10 m².\n"
            "Step 4: Take away the missing part: 40 m² − 10 m² = 30 m² of floor to carpet.\n"
            "Step 5: Each square metre costs GH₵ 20. Multiply: 30 × GH₵ 20 = GH₵ 600.\n"
            "Answer: It costs GH₵ 600 to carpet the floor."
        ),
        "difficulty": "hard",
    },
    {
        "prompt": (
            "A cyclist rides 20 km/h for 35 minutes. The cyclist travels the same "
            "distance at 28 km/h. How many minutes does the second journey take?"
        ),
        "options": ["16 minutes", "25 minutes", "35 minutes", "49 minutes"],
        "correct_answer": "25 minutes",
        "expected_answer": (
            "35 minutes = 35/60 hours. Distance = 20 × 35/60 = 35/3 km. "
            "Time at 28 km/h = (35/3) ÷ 28 hours = 5/12 hour = 25 minutes."
        ),
        "rubric": (
            "Working guide (10 marks): 2 marks for recognising the distance is unchanged; "
            "2 marks for converting minutes to hours or using a correct proportional method; "
            "3 marks for finding the distance or applying inverse speed-time proportion; "
            "3 marks for 25 minutes."
        ),
        "explanation": (
            "Work it out on paper first, then choose the matching answer.\n\n"
            "Step 1: The cyclist covers the same distance on both journeys. A higher speed "
            "means less time for that same distance.\n"
            "Step 2: Find the first distance. Change 35 minutes to hours: 35 ÷ 60 = 7/12 hour.\n"
            "Step 3: Distance = speed × time = 20 × 7/12 = 35/3 km.\n"
            "Step 4: Find the new time: time = distance ÷ speed = (35/3) ÷ 28 = 5/12 hour.\n"
            "Step 5: Change hours to minutes: 5/12 × 60 = 25 minutes.\n"
            "Answer: The second journey takes 25 minutes. Check: the cyclist is going faster, "
            "so the time is less than 35 minutes."
        ),
        "difficulty": "hard",
    },
    {
        "prompt": (
            "The table shows the number of books read by learners in one month.\n"
            "Books read: 0, 1, 2, 3, 4\n"
            "Number of learners: 2, 3, 6, 5, 4\n"
            "What is the mean number of books read per learner?"
        ),
        "options": ["2 books", "2.3 books", "3 books", "46 books"],
        "correct_answer": "2.3 books",
        "expected_answer": (
            "Total learners = 2 + 3 + 6 + 5 + 4 = 20. "
            "Total books = 0×2 + 1×3 + 2×6 + 3×5 + 4×4 = 46. "
            "Mean = 46 ÷ 20 = 2.3 books."
        ),
        "rubric": (
            "Working guide (10 marks): 2 marks for totaling the learners; "
            "4 marks for multiplying each books-read value by its frequency and adding; "
            "2 marks for dividing total books by total learners; "
            "2 marks for 2.3 books."
        ),
        "explanation": (
            "Work it out on paper first, then choose the matching answer.\n\n"
            "Step 1: A mean is a fair-share average: total amount divided by number of people.\n"
            "Step 2: Find the total books. Multiply each number of books by how many learners "
            "read that many: 0×2 = 0, 1×3 = 3, 2×6 = 12, 3×5 = 15, and 4×4 = 16.\n"
            "Step 3: Add the book totals: 0 + 3 + 12 + 15 + 16 = 46 books.\n"
            "Step 4: Add the learners: 2 + 3 + 6 + 5 + 4 = 20 learners.\n"
            "Step 5: Divide total books by total learners: 46 ÷ 20 = 2.3.\n"
            "Answer: The mean is 2.3 books per learner."
        ),
        "difficulty": "medium",
    },
]


def update_paper_questions(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    Topic = apps.get_model("learning", "Topic")
    Question = apps.get_model("learning", "Question")
    mathematics = Subject.objects.get(slug="mathematics")
    topic = Topic.objects.get(
        subject=mathematics,
        slug="g9-paper-2-written-practice",
    )
    topic.title = "Structured Mathematics: Work It Out, Then Choose"
    topic.summary = (
        "Choose four of six longer, multi-step problems. Work them out with pen and paper, "
        "then select the matching A–D answer."
    )
    topic.content = (
        "Choose any four of the six questions. First show your working on paper, just as "
        "you would in a written examination. Then choose the A–D option that matches your "
        "answer. After submitting, use the clear worked solution and mark guide to check "
        "each step. The app marks the selected answer; it does not mark handwritten working."
    )
    topic.save(update_fields=["title", "summary", "content"])

    for index, data in enumerate(PAPER_QUESTIONS, start=1):
        question = Question.objects.get(topic=topic, prompt__startswith=f"{index}.")
        question.prompt = data["prompt"]
        question.options = data["options"]
        question.correct_answer = data["correct_answer"]
        question.expected_answer = data["expected_answer"]
        question.rubric = data["rubric"]
        question.explanation = data["explanation"]
        question.difficulty = data["difficulty"]
        question.save(
            update_fields=[
                "prompt",
                "options",
                "correct_answer",
                "expected_answer",
                "rubric",
                "explanation",
                "difficulty",
            ]
        )


class Migration(migrations.Migration):
    dependencies = [("learning", "0007_mathematics_paper_two_written_practice")]

    operations = [
        migrations.RunPython(update_paper_questions, migrations.RunPython.noop),
    ]
