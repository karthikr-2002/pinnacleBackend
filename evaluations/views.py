from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count
from .models import Unit, EvaluationTemplate, Question, Evaluation, EvaluationSubmission, Rating
from .forms import UnitForm, EvaluationTemplateForm, EvaluationForm
from users.models import User


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') == 'admin')


# -------------------------------------------------------------
# ADMIN VIEWS
# -------------------------------------------------------------

@login_required(login_url='users:login')
def evaluation_list(request):
    """Admin view: List all evaluations."""
    if not is_admin(request.user):
        return redirect('evaluations:user_evaluations')

    evaluations = Evaluation.objects.all().select_related('template', 'created_by').prefetch_related('units', 'submissions')
    return render(request, 'evaluations/admin/evaluation_list.html', {
        'evaluations': evaluations,
        'active_menu': 'evaluations',
    })


@login_required(login_url='users:login')
def evaluation_create(request):
    """Admin view: Create a new evaluation and tag units."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can create evaluations.")

    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.created_by = request.user
            evaluation.save()
            form.save_m2m()  # Save tagged units
            messages.success(request, f"Evaluation '{evaluation.title}' created and tagged successfully!")
            return redirect('evaluations:evaluation_list')
    else:
        form = EvaluationForm()

    return render(request, 'evaluations/admin/evaluation_form.html', {
        'form': form,
        'title': 'Create New Evaluation',
        'active_menu': 'evaluations',
    })


@login_required(login_url='users:login')
def evaluation_detail(request, pk):
    """Admin view: View evaluation details, tagged units, and peer submissions matrix."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can view evaluation analytics.")

    evaluation = get_object_or_404(
        Evaluation.objects.select_related('template').prefetch_related('units', 'template__questions'),
        pk=pk
    )
    submissions = evaluation.submissions.select_related('evaluator', 'evaluatee', 'unit').prefetch_related('ratings__question').all()
    questions = evaluation.template.questions.all()

    avg_score = submissions.aggregate(avg=Avg('ratings__score'))['avg'] or 0

    return render(request, 'evaluations/admin/evaluation_detail.html', {
        'evaluation': evaluation,
        'submissions': submissions,
        'questions': questions,
        'avg_score': round(avg_score, 2),
        'active_menu': 'evaluations',
    })


@login_required(login_url='users:login')
def template_list(request):
    """Admin view: List all evaluation templates."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can view templates.")

    templates = EvaluationTemplate.objects.all().prefetch_related('questions', 'evaluations')
    return render(request, 'evaluations/admin/template_list.html', {
        'templates': templates,
        'active_menu': 'templates',
    })


@login_required(login_url='users:login')
def template_create(request):
    """Admin view: Create a new template and its questions."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can create templates.")

    if request.method == 'POST':
        form = EvaluationTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()

            # Process questions from lines
            questions_text = form.cleaned_data.get('questions_input', '')
            lines = [q.strip() for q in questions_text.splitlines() if q.strip()]
            for order, line in enumerate(lines, start=1):
                if '|' in line:
                    parts = line.split('|', 1)
                    q_text = parts[0].strip()
                    custom_labels = [lbl.strip() for lbl in parts[1].split(',') if lbl.strip()]
                    q_kwargs = {'template': template, 'question_text': q_text, 'order': order}
                    for idx in range(min(len(custom_labels), 6)):
                        q_kwargs[f'label_{idx}'] = custom_labels[idx]
                    Question.objects.create(**q_kwargs)
                else:
                    Question.objects.create(template=template, question_text=line, order=order)

            messages.success(request, f"Template '{template.title}' created with {len(lines)} questions!")
            return redirect('evaluations:template_list')
    else:
        form = EvaluationTemplateForm()

    return render(request, 'evaluations/admin/template_form.html', {
        'form': form,
        'title': 'Create Evaluation Template',
        'active_menu': 'templates',
    })


@login_required(login_url='users:login')
def unit_list(request):
    """Admin view: List all care units and their assigned employees."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can view units.")

    units = Unit.objects.all().prefetch_related('users', 'evaluations')
    return render(request, 'evaluations/admin/unit_list.html', {
        'units': units,
        'active_menu': 'units',
    })


@login_required(login_url='users:login')
def unit_create(request):
    """Admin view: Create a new care unit and assign users."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can create units.")

    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f"Unit '{unit.name}' created successfully!")
            return redirect('evaluations:unit_list')
    else:
        form = UnitForm()

    return render(request, 'evaluations/admin/unit_form.html', {
        'form': form,
        'title': 'Create Care Unit',
        'active_menu': 'units',
    })


@login_required(login_url='users:login')
def admin_submissions_list(request):
    """Admin view: Global list of all employee evaluations submissions."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can view user evaluation data.")

    submissions = EvaluationSubmission.objects.all().select_related('evaluation', 'evaluator', 'evaluatee', 'unit').prefetch_related('ratings')
    return render(request, 'evaluations/admin/submission_list.html', {
        'submissions': submissions,
        'active_menu': 'submissions',
    })


@login_required(login_url='users:login')
def admin_submission_detail(request, pk):
    """Admin view: Single employee submission breakdown."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can view user evaluation data.")

    submission = get_object_or_404(
        EvaluationSubmission.objects.select_related('evaluation', 'evaluator', 'evaluatee', 'unit').prefetch_related('ratings__question'),
        pk=pk
    )
    return render(request, 'evaluations/admin/submission_detail.html', {
        'submission': submission,
        'active_menu': 'submissions',
    })


# -------------------------------------------------------------
# USER (EMPLOYEE PEER EVALUATION) VIEWS
# -------------------------------------------------------------

@login_required(login_url='users:login')
def user_evaluations(request):
    """User view: List active evaluations and the colleagues in their unit to evaluate."""
    user = request.user
    user_units = user.assigned_units.all()

    # Find evaluations where user's unit is tagged
    available_evaluations = Evaluation.objects.filter(
        status='active'
    ).filter(
        units__in=user_units
    ).distinct().select_related('template').prefetch_related('template__questions', 'units')

    evaluations_data = []
    for eval_obj in available_evaluations:
        # Colleague peers in the unit (excluding self)
        peers = eval_obj.get_peers_to_evaluate(user)
        total_peers = peers.count()

        # Build list of peers with evaluation status for each
        peer_items = []
        completed_count = 0
        for peer in peers:
            submission = eval_obj.get_peer_submission(evaluator=user, evaluatee=peer)
            is_done = submission is not None
            if is_done:
                completed_count += 1
            peer_items.append({
                'peer': peer,
                'has_evaluated': is_done,
                'submission': submission,
            })

        progress_pct = int((completed_count / total_peers * 100)) if total_peers > 0 else 0

        evaluations_data.append({
            'evaluation': eval_obj,
            'peers': peer_items,
            'completed_count': completed_count,
            'total_peers': total_peers,
            'progress_pct': progress_pct,
            'is_fully_completed': (completed_count == total_peers and total_peers > 0),
            'questions_count': eval_obj.template.questions_count,
        })

    return render(request, 'evaluations/user/my_evaluations.html', {
        'evaluations_data': evaluations_data,
        'user_units': user_units,
        'active_menu': 'my_evaluations',
    })


@login_required(login_url='users:login')
def evaluation_rate(request, pk, evaluatee_id):
    """User view: Rate questions for a specific colleague in their unit."""
    evaluation = get_object_or_404(
        Evaluation.objects.select_related('template').prefetch_related('units', 'template__questions'),
        pk=pk
    )
    evaluatee = get_object_or_404(User, pk=evaluatee_id)

    # Cannot evaluate oneself
    if request.user.id == evaluatee.id:
        messages.error(request, "You cannot evaluate yourself. You evaluate other colleagues in your unit.")
        return redirect('evaluations:user_evaluations')

    # Check eligibility of evaluator and evaluatee
    if not evaluation.is_user_eligible(request.user):
        messages.error(request, "You are not assigned to any unit tagged in this evaluation.")
        return redirect('evaluations:user_evaluations')

    # Find the shared unit between evaluator and evaluatee
    shared_units = request.user.assigned_units.filter(id__in=evaluatee.assigned_units.values_list('id', flat=True))
    unit = shared_units.first() or request.user.assigned_units.first()

    # Check if this colleague has already been evaluated by this user
    existing_submission = evaluation.get_peer_submission(evaluator=request.user, evaluatee=evaluatee)
    if existing_submission:
        messages.info(request, f"You have already completed the evaluation for {evaluatee.get_full_name() or evaluatee.username}.")
        return redirect('evaluations:user_history_detail', pk=existing_submission.pk)

    questions = evaluation.template.questions.all()

    if request.method == 'POST':
        feedback = request.POST.get('feedback', '').strip()

        # Validate that all questions are answered with valid scores (0 to 5)
        ratings_to_create = []
        errors = []

        for q in questions:
            score_val = request.POST.get(f'rating_{q.id}')
            comment_val = request.POST.get(f'comment_{q.id}', '').strip()

            if score_val is None or score_val == '':
                errors.append(f"Please provide a rating for: '{q.question_text[:40]}...'")
            else:
                try:
                    score_int = int(score_val)
                    if not (0 <= score_int <= 5):
                        errors.append(f"Rating for '{q.question_text[:40]}' must be between 0 and 5.")
                    else:
                        ratings_to_create.append((q, score_int, comment_val))
                except ValueError:
                    errors.append(f"Invalid rating value for '{q.question_text[:40]}'.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            # Create peer submission
            submission = EvaluationSubmission.objects.create(
                evaluation=evaluation,
                evaluator=request.user,
                evaluatee=evaluatee,
                unit=unit,
                feedback=feedback
            )

            # Create individual ratings
            for question, score, comment in ratings_to_create:
                Rating.objects.create(
                    submission=submission,
                    question=question,
                    score=score,
                    comment=comment or None
                )

            messages.success(request, f"Evaluation for {evaluatee.get_full_name() or evaluatee.username} submitted successfully!")
            return redirect('evaluations:user_evaluations')

    return render(request, 'evaluations/user/evaluation_rate.html', {
        'evaluation': evaluation,
        'evaluatee': evaluatee,
        'unit': unit,
        'questions': questions,
        'active_menu': 'my_evaluations',
    })


@login_required(login_url='users:login')
def user_history(request):
    """User view: View past peer evaluations submitted by the logged in employee."""
    submissions = EvaluationSubmission.objects.filter(
        evaluator=request.user
    ).select_related('evaluation', 'evaluatee', 'unit').prefetch_related('ratings')

    return render(request, 'evaluations/user/my_history.html', {
        'submissions': submissions,
        'active_menu': 'my_history',
    })


@login_required(login_url='users:login')
def user_history_detail(request, pk):
    """User view: View details of a past submission made by this employee."""
    submission = get_object_or_404(
        EvaluationSubmission.objects.select_related('evaluation', 'evaluatee', 'unit').prefetch_related('ratings__question'),
        pk=pk,
        evaluator=request.user
    )

    return render(request, 'evaluations/user/my_history_detail.html', {
        'submission': submission,
        'active_menu': 'my_history',
    })
