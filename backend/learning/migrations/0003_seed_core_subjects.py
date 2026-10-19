from django.db import migrations


def add_core_subjects(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    subjects = (
        ("English", "english", "Build reading, writing, and language skills."),
        ("Mathematics", "mathematics", "Strengthen your problem-solving skills."),
        ("Science", "science", "Explore the world through science."),
    )
    for position, (name, slug, description) in enumerate(subjects):
        Subject.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "description": description,
                "is_published": True,
                "position": position,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("learning", "0002_initial")]

    operations = [
        migrations.RunPython(add_core_subjects, migrations.RunPython.noop),
    ]
