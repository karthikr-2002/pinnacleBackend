import os
import sys
from pathlib import Path
import random
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pinnacleBackend.settings')
import django
django.setup()

from django.utils import timezone
from users.models import User
from evaluations.models import Unit, EvaluationTemplate, Question, Evaluation, EvaluationSubmission, Rating

def run_seed():
    print("=== Starting Pinnacle Care Home Seed Script ===")

    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True).first()

    # 1. Ensure / Create Staff Users
    staff_data = [
        # Sunrise Wing Staff
        ('john', 'John', 'Doe', 'manager', 'Senior Unit Manager', 'https://api.dicebear.com/7.x/bottts/svg?seed=John'),
        ('sarah', 'Sarah', 'Jenkins', 'user', 'Senior Registered Nurse', 'https://api.dicebear.com/7.x/bottts/svg?seed=Sarah'),
        ('alex', 'Alex', 'Smith', 'user', 'Attending Physician', 'https://api.dicebear.com/7.x/bottts/svg?seed=Alex'),
        ('maria', 'Maria', 'Garcia', 'user', 'Lead Care Assistant', 'https://api.dicebear.com/7.x/bottts/svg?seed=Maria'),
        ('david', 'David', 'Chen', 'user', 'Clinical Nurse Specialist', 'https://api.dicebear.com/7.x/bottts/svg?seed=David'),
        # Meadow Haven Staff
        ('emma', 'Emma', 'Watson', 'user', 'Senior Care Assistant', 'https://api.dicebear.com/7.x/bottts/svg?seed=Emma'),
        ('lucas', 'Lucas', 'Bennett', 'user', 'Registered Care Nurse', 'https://api.dicebear.com/7.x/bottts/svg?seed=Lucas'),
        ('clara', 'Clara', 'Oswald', 'user', 'Occupational Therapist', 'https://api.dicebear.com/7.x/bottts/svg?seed=Clara'),
        ('samuel', 'Samuel', 'Taylor', 'user', 'Night Care Lead', 'https://api.dicebear.com/7.x/bottts/svg?seed=Samuel'),
        ('olivia', 'Olivia', 'Martinez', 'user', 'Palliative Care Specialist', 'https://api.dicebear.com/7.x/bottts/svg?seed=Olivia'),
        # Additional specialist
        ('liam', 'Liam', 'Wilson', 'user', 'Physiotherapy Coordinator', 'https://api.dicebear.com/7.x/bottts/svg?seed=Liam'),
    ]

    users_map = {}
    for username, first_name, last_name, role, job_title, avatar_url in staff_data:
        user, created = User.objects.get_or_create(username=username)
        user.first_name = first_name
        user.last_name = last_name
        user.role = role
        user.job_title = job_title
        user.avatar_url = avatar_url
        if created or not user.has_usable_password():
            user.set_password('Password123!')
        user.save()
        users_map[username] = user
        status = "Created" if created else "Updated"
        print(f"  [{status} User] {username} ({user.get_full_name()} - {job_title})")

    # 2. Ensure / Create Units
    unit_sunrise, _ = Unit.objects.get_or_create(name='Sunrise Wing', defaults={'place': 'Building A - Level 1'})
    unit_sunrise.users.set([users_map['john'], users_map['sarah'], users_map['alex'], users_map['david']])
    unit_sunrise.save()

    unit_meadow, _ = Unit.objects.get_or_create(name='Meadow Haven', defaults={'place': 'Building B - Level 2'})
    unit_meadow.users.set([users_map['emma'], users_map['lucas'], users_map['clara'], users_map['olivia']])
    unit_meadow.save()

    unit_cedar, _ = Unit.objects.get_or_create(name='Cedar Grove Memory Suite', defaults={'place': 'Building C - Ground Floor'})
    unit_cedar.users.set([users_map['maria'], users_map['samuel'], users_map['liam']])
    unit_cedar.save()

    print(f"  [Units Configured] Sunrise Wing ({unit_sunrise.users.count()} staff), Meadow Haven ({unit_meadow.users.count()} staff), Cedar Grove ({unit_cedar.users.count()} staff)")

    # 3. Create Templates & Questions
    templates_defs = [
        {
            'title': 'Dementia Care & Compassion Protocol',
            'description': 'Evaluates staff competency in empathetic person-centered communication, de-escalation techniques, memory stimulation, and dignity preservation for residents with cognitive conditions.',
            'questions': [
                (
                    'Practices empathetic, person-centered communication tailored to memory care residents.',
                    ['0 - Non-responsive / Insensitive', '1 - Infrequently communicates', '2 - Basic communication only', '3 - Consistently calm & clear', '4 - Highly compassionate & empathetic', '5 - Masterful emotional connection']
                ),
                (
                    'De-escalation skills during episodes of resident agitation, disorientation, or sundowning.',
                    ['0 - Ineffective / Escalates tension', '1 - Struggles to calm residents', '2 - Requires senior intervention', '3 - Follows standard de-escalation', '4 - Very soothing & proactive', '5 - Exceptional conflict diffuser']
                ),
                (
                    'Preservation of resident autonomy, dignity, and personal choice in daily routines.',
                    ['0 - Disregards resident choices', '1 - Minimal choices offered', '2 - Rushes personal care tasks', '3 - Patient & respectful', '4 - Empowers resident decisions', '5 - Champion of dignity & autonomy']
                ),
                (
                    'Engagement in sensory, musical, and cognitive stimulation activities.',
                    ['0 - Never engages in activities', '1 - Rare participation', '2 - Only during scheduled events', '3 - Regular positive engagement', '4 - Enthusiastic & creative', '5 - Inspires high resident joy']
                ),
                (
                    'Thoroughness in documenting behavioral changes and communicating with families.',
                    ['0 - Missing or late records', '1 - Incomplete behavioral notes', '2 - Satisfactory documentation', '3 - Timely & clear logs', '4 - Detailed & insightful notes', '5 - Exemplary family liaison']
                ),
            ]
        },
        {
            'title': 'Medication Administration & Clinical Safety Audit',
            'description': 'Audits adherence to 6 Rights of medication administration, controlled drug records, aseptic wound dressing techniques, and prompt physician escalation.',
            'questions': [
                (
                    'Adherence to the 6 Rights of Medication Delivery (Resident, Drug, Dose, Time, Route, Record).',
                    ['0 - Severe protocol breach', '1 - Frequent minor oversights', '2 - Needs occasional reminders', '3 - Strictly follows protocol', '4 - Meticulous & safety-first', '5 - Zero error clinical benchmark']
                ),
                (
                    'Accurate MAR (Medication Administration Record) chart logging and controlled drug witnessing.',
                    ['0 - Unsigned / Discrepant charts', '1 - Inconsistent double-checks', '2 - Minor chart delays', '3 - Prompt & accurate logging', '4 - Rigorous compliance', '5 - Flawless audits every shift']
                ),
                (
                    'Vigilance in identifying, monitoring, and reporting adverse drug reactions or allergies.',
                    ['0 - Missed reaction symptoms', '1 - Slow to recognize issues', '2 - Identifies obvious reactions', '3 - Proactively monitors vitals', '4 - Rapid & precise escalation', '5 - Expert clinical intuition']
                ),
                (
                    'Aseptic technique, sterile gloves, hand hygiene, and sharp instrument disposal.',
                    ['0 - Cross-contamination risk', '1 - Inconsistent glove changes', '2 - Basic compliance', '3 - Follows infection control', '4 - Outstanding clean technique', '5 - Gold standard hygiene']
                ),
                (
                    'Prompt coordination with attending GPs, pharmacies, and out-of-hours triage.',
                    ['0 - Unreachable / Poor handover', '1 - Delayed communications', '2 - Average coordination', '3 - Clear & timely updates', '4 - Highly proactive advocacy', '5 - Seamless inter-agency partner']
                ),
            ]
        },
        {
            'title': 'Palliative & End-of-Life Dignity Protocols',
            'description': 'Evaluates compassionate pain management, holistic resident comfort, advance care planning adherence, and empathetic family support.',
            'questions': [
                (
                    'Attentiveness to subtle non-verbal cues of pain, restlessness, or discomfort.',
                    ['0 - Inattentive to distress', '1 - Noticeable delay in response', '2 - Identifies pain when alerted', '3 - Regularly monitors comfort', '4 - Highly intuitive comfort care', '5 - Outstanding palliative empathy']
                ),
                (
                    'Gentle repositioning, pressure area care, mouth care, and physical comfort maintenance.',
                    ['0 - Neglects turning schedule', '1 - Inconsistent mouth care', '2 - Meets minimum comfort specs', '3 - Punctual & gentle care', '4 - Impeccable attention to detail', '5 - Maximum tenderness & care']
                ),
                (
                    'Sensitivity, empathy, and emotional warmth extended to resident families & loved ones.',
                    ['0 - Cold / Detached interaction', '1 - Awkward or strained communication', '2 - Polite but transactional', '3 - Warm & reassuring presence', '4 - Deeply empathetic & supportive', '5 - Exceptional solace & comfort']
                ),
                (
                    'Adherence to Advance Care Directives, DNR orders, and resident spiritual wishes.',
                    ['0 - Disregards care wishes', '1 - Unclear on resident directives', '2 - Checks records when reminded', '3 - Strictly honors wishes', '4 - Advocate for resident choices', '5 - Reverent & holistic execution']
                ),
                (
                    'Close collaboration with hospice nurses, chaplains, and bereavement specialists.',
                    ['0 - Operates in isolation', '1 - Infrequent collaboration', '2 - Adequate handover info', '3 - Smooth multidisciplinary teamwork', '4 - Proactive care coordinator', '5 - Exemplary team leadership']
                ),
            ]
        },
        {
            'title': 'Mobility, Fall Prevention & Emergency Preparedness',
            'description': 'Assesses safe resident transfer techniques, hoist safety, hazard mitigation, rapid emergency response, and post-fall documentation.',
            'questions': [
                (
                    'Adherence to manual handling risk assessments, transfer slings, and hoist operations.',
                    ['0 - Dangerous transfer practice', '1 - Bypasses safety checks', '2 - Safe with supervision', '3 - Competent hoist handling', '4 - Exceptional ergonomics', '5 - Manual handling mentor']
                ),
                (
                    'Active vigilance in identifying and removing slip, trip, and spill hazards.',
                    ['0 - Ignores visible hazards', '1 - Slow to clean or report', '2 - Cleans when pointed out', '3 - Proactively maintains pathways', '4 - Anticipates hazard risks', '5 - Zero-hazard champion']
                ),
                (
                    'Calmness, speed, and protocol adherence during fire alarms and medical crash calls.',
                    ['0 - Panics or freezes', '1 - Hesitant response', '2 - Follows lead of others', '3 - Prompt & composed response', '4 - Swift emergency leadership', '5 - Flawless crisis response']
                ),
                (
                    'Speed and accuracy of incident logging, vital signs checking, and GP notification.',
                    ['0 - Missing incident report', '1 - Incomplete post-fall vitals', '2 - Basic report filed', '3 - Thorough & timely reporting', '4 - Detailed root-cause logging', '5 - Gold standard compliance']
                ),
                (
                    'Sanitization of resident rooms, call buzzers, bed rails, and communal dining spaces.',
                    ['0 - Unsanitary conditions', '1 - Superficial wipe downs', '2 - Meets baseline hygiene', '3 - Clean & odor-free standards', '4 - Thorough multi-surface sanitization', '5 - Hospital-grade cleanliness']
                ),
            ]
        },
    ]

    created_templates = {}
    for t_def in templates_defs:
        template, t_created = EvaluationTemplate.objects.get_or_create(
            title=t_def['title'],
            defaults={
                'description': t_def['description'],
                'created_by': admin_user
            }
        )
        if t_created:
            for order, (q_text, labels) in enumerate(t_def['questions'], start=1):
                Question.objects.create(
                    template=template,
                    question_text=q_text,
                    order=order,
                    label_0=labels[0],
                    label_1=labels[1],
                    label_2=labels[2],
                    label_3=labels[3],
                    label_4=labels[4],
                    label_5=labels[5],
                )
            print(f"  [Created Template] {template.title} with {len(t_def['questions'])} questions")
        else:
            print(f"  [Existing Template] {template.title}")
        created_templates[t_def['title']] = template

    # Also grab existing template 1
    t1 = EvaluationTemplate.objects.filter(title__icontains='Care Quality & Resident Safety').first()
    if t1:
        created_templates['Care Quality'] = t1

    # 4. Create Evaluations
    evaluations_defs = [
        {
            'title': 'Q4 Dementia & Cognitive Care Review',
            'description': 'Peer review across memory care and residential units assessing empathy, de-escalation, and family communication.',
            'template': created_templates['Dementia Care & Compassion Protocol'],
            'units': [unit_sunrise, unit_meadow, unit_cedar],
            'status': 'active'
        },
        {
            'title': 'November Clinical Safety & Medication Protocol Audit',
            'description': 'Monthly clinical evaluation of medication administration, MAR records, and aseptic protocols among nursing staff.',
            'template': created_templates['Medication Administration & Clinical Safety Audit'],
            'units': [unit_sunrise, unit_meadow],
            'status': 'active'
        },
        {
            'title': 'Annual Palliative Care & Resident Dignity Benchmark',
            'description': 'Comprehensive assessment of holistic resident comfort, non-verbal pain response, and family bereavement support.',
            'template': created_templates['Palliative & End-of-Life Dignity Protocols'],
            'units': [unit_sunrise, unit_meadow],
            'status': 'completed'
        },
        {
            'title': 'Quarterly Mobility & Emergency Preparedness Inspection',
            'description': 'Unit-wide peer evaluation of manual handling, hoist safety, hazard avoidance, and emergency fire drill coordination.',
            'template': created_templates['Mobility, Fall Prevention & Emergency Preparedness'],
            'units': [unit_meadow, unit_cedar],
            'status': 'active'
        },
    ]

    created_evals = []
    # Include existing evaluation 1
    existing_eval_1 = Evaluation.objects.filter(title__icontains='October 2026').first()
    if existing_eval_1:
        existing_eval_1.units.add(unit_sunrise, unit_meadow)
        created_evals.append(existing_eval_1)

    for e_def in evaluations_defs:
        evaluation, e_created = Evaluation.objects.get_or_create(
            title=e_def['title'],
            defaults={
                'description': e_def['description'],
                'template': e_def['template'],
                'status': e_def['status'],
                'created_by': admin_user
            }
        )
        evaluation.units.set(e_def['units'])
        evaluation.save()
        created_evals.append(evaluation)
        status = "Created" if e_created else "Updated"
        print(f"  [{status} Evaluation] {evaluation.title} (Status: {evaluation.status})")

    # 5. Generate Random Ratings and Submissions
    print("\n--- Generating Peer Submissions & Random Ratings ---")

    # Sample realistic feedback notes
    feedback_samples = [
        "Consistently exhibits outstanding care and warmth with all residents. Very proactive during shift handovers.",
        "Demonstrates great clinical precision and composure during demanding emergency situations. A pleasure to work alongside.",
        "Very supportive teammate. Always steps in to assist junior staff with complex resident transfers and repositioning.",
        "Exceptional empathy when communicating with resident families during difficult updates. True asset to the unit.",
        "Always punctual, thorough with daily care documentation, and maintains high standards of infection hygiene.",
        "Maintains a remarkably calming influence in the dementia wing, especially during sundowning hours.",
        "Excellent attention to medication schedules and always ensures double-checks are done methodically.",
        "Great active listener. Residents constantly comment on how dignified and respected they feel under their care.",
        "Consistently attentive to subtle changes in resident vitality and promptly escalates issues to senior doctors.",
        "Shows fantastic dedication and collaborative spirit. Handles challenging behavioral moments with utmost grace."
    ]

    question_comment_samples = [
        "Very thorough and meticulous.",
        "Always complies with unit protocols.",
        "Warm and patient approach with residents.",
        "Zero errors observed throughout the shift cycle.",
        "Sets a positive example for other carers.",
        "Quick and reliable response time.",
        "Detailed and clear notes provided.",
        "Maintains a high standard of cleanliness.",
        "Great communication with physicians.",
        "Highly compassionate and respectful."
    ]

    # Weighted scores: realistic care home distribution with high scores (3, 4, 5) and occasional lower (1, 2)
    score_choices = [3, 4, 4, 5, 5, 5, 4, 3, 2, 5, 4, 4]

    submissions_created_count = 0
    ratings_created_count = 0

    now = timezone.now()

    for evaluation in created_evals:
        questions = list(evaluation.template.questions.all())
        tagged_units = list(evaluation.units.all())

        for unit in tagged_units:
            staff_in_unit = list(unit.users.all())
            if len(staff_in_unit) < 2:
                continue

            # In each unit, generate peer reviews
            # Randomly pick pairs so not everyone evaluates everyone, but a good healthy realistic proportion (e.g. 3-4 evaluations per staff)
            for evaluator in staff_in_unit:
                potential_peers = [p for p in staff_in_unit if p.id != evaluator.id]
                # Pick 2 to 3 peers to evaluate for this evaluation
                num_to_evaluate = min(len(potential_peers), random.randint(2, 4))
                selected_peers = random.sample(potential_peers, num_to_evaluate)

                for evaluatee in selected_peers:
                    # Check if already submitted
                    submission, sub_created = EvaluationSubmission.objects.get_or_create(
                        evaluation=evaluation,
                        evaluator=evaluator,
                        evaluatee=evaluatee,
                        defaults={
                            'unit': unit,
                            'feedback': random.choice(feedback_samples),
                        }
                    )

                    # Adjust submitted_at to a realistic past timestamp (1 to 20 days ago)
                    if sub_created:
                        submissions_created_count += 1
                        random_days = random.randint(1, 18)
                        random_hours = random.randint(1, 23)
                        submission.submitted_at = now - timedelta(days=random_days, hours=random_hours)
                        submission.save(update_fields=['submitted_at'])

                    # Now generate ratings for each question in this evaluation's template
                    for q in questions:
                        if not Rating.objects.filter(submission=submission, question=q).exists():
                            score = random.choice(score_choices)
                            # 40% chance of adding a comment
                            has_comment = random.random() < 0.45
                            comment = random.choice(question_comment_samples) if has_comment else None

                            Rating.objects.create(
                                submission=submission,
                                question=q,
                                score=score,
                                comment=comment
                            )
                            ratings_created_count += 1

    print(f"\n[Completed] Created {submissions_created_count} new submissions and {ratings_created_count} new question ratings.")
    print(f"Total Evaluations in DB: {Evaluation.objects.count()}")
    print(f"Total Templates in DB: {EvaluationTemplate.objects.count()}")
    print(f"Total Submissions in DB: {EvaluationSubmission.objects.count()}")
    print(f"Total Ratings in DB: {Rating.objects.count()}")

if __name__ == '__main__':
    run_seed()
