from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count
from django.utils import timezone
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

    evaluations = Evaluation.objects.all().select_related('template', 'created_by').prefetch_related('units__users', 'submissions')
    for ev in evaluations:
        ev.sync_status()

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

    units = Unit.objects.all().prefetch_related('users')
    return render(request, 'evaluations/admin/evaluation_form.html', {
        'form': form,
        'title': 'Create New Evaluation',
        'active_menu': 'evaluations',
        'units': units,
    })


@login_required(login_url='users:login')
def evaluation_detail(request, pk):
    """Admin view: View evaluation details, tagged units, and employee completion status per unit."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can view evaluation analytics.")

    evaluation = get_object_or_404(
        Evaluation.objects.select_related('template').prefetch_related('units__users', 'template__questions'),
        pk=pk
    )
    questions = evaluation.template.questions.all()

    # Pre-fetch all submissions for this evaluation
    submissions = list(
        evaluation.submissions.select_related('evaluator', 'evaluatee', 'unit')
        .prefetch_related('ratings__question')
        .all()
    )

    avg_score = evaluation.submissions.aggregate(avg=Avg('ratings__score'))['avg'] or 0

    # Build per-unit and per-employee evaluation status
    units_data = []
    total_tagged_employees = 0
    total_completed_employees = 0

    for unit in evaluation.units.all():
        employees = list(unit.users.all())
        total_unit_employees = len(employees)
        total_tagged_employees += total_unit_employees

        unit_completed_count = 0
        employees_data = []

        for emp in employees:
            # Peers this employee evaluates in this unit
            peers = [p for p in employees if p.id != emp.id]
            total_peers = len(peers)

            # Submissions by this employee in this unit for this evaluation
            emp_subs = [
                s for s in submissions
                if s.evaluator_id == emp.id and s.evaluatee_id in [p.id for p in peers] and (s.unit_id == unit.id or s.unit_id is None)
            ]
            completed_peers_count = len(emp_subs)

            # Determine status: completed, in_progress, started, not_started
            if total_peers == 0 or completed_peers_count >= total_peers:
                status = 'completed'
                status_label = 'Completed'
                unit_completed_count += 1
            elif completed_peers_count > 1:
                status = 'in_progress'
                status_label = 'In Progress'
            elif completed_peers_count == 1:
                status = 'started'
                status_label = 'Started'
            else:
                status = 'not_started'
                status_label = 'Not Started'

            # Progress percentage
            progress_pct = int((completed_peers_count / total_peers * 100)) if total_peers > 0 else 100

            # Submitted at timestamps
            emp_subs_sorted = sorted(emp_subs, key=lambda s: s.submitted_at, reverse=True)
            latest_submitted_at = emp_subs_sorted[0].submitted_at if emp_subs_sorted else None

            # Average score given
            scores_given = [s.average_score for s in emp_subs if s.average_score]
            avg_score_given = round(sum(scores_given) / len(scores_given), 2) if scores_given else None

            # Build peer-by-peer breakdown for this employee
            peers_breakdown = []
            evaluated_map = {s.evaluatee_id: s for s in emp_subs}
            for peer in peers:
                peer_sub = evaluated_map.get(peer.id)
                peers_breakdown.append({
                    'peer': peer,
                    'is_evaluated': peer_sub is not None,
                    'submission': peer_sub,
                    'submitted_at': peer_sub.submitted_at if peer_sub else None,
                    'avg_score': peer_sub.average_score if peer_sub else None,
                })

            employees_data.append({
                'employee': emp,
                'status': status,
                'status_label': status_label,
                'completed_peers_count': completed_peers_count,
                'total_peers': total_peers,
                'progress_pct': progress_pct,
                'latest_submitted_at': latest_submitted_at,
                'avg_score_given': avg_score_given,
                'peers_breakdown': peers_breakdown,
                'submissions_count': len(emp_subs),
            })

        total_completed_employees += unit_completed_count
        unit_progress_pct = int((unit_completed_count / total_unit_employees * 100)) if total_unit_employees > 0 else 0

        units_data.append({
            'unit': unit,
            'total_employees': total_unit_employees,
            'completed_employees_count': unit_completed_count,
            'progress_pct': unit_progress_pct,
            'employees': employees_data,
        })

    overall_progress_pct = int((total_completed_employees / total_tagged_employees * 100)) if total_tagged_employees > 0 else 0

    return render(request, 'evaluations/admin/evaluation_detail.html', {
        'evaluation': evaluation,
        'units_data': units_data,
        'questions': questions,
        'avg_score': round(avg_score, 2),
        'total_submissions': len(submissions),
        'total_tagged_employees': total_tagged_employees,
        'total_completed_employees': total_completed_employees,
        'overall_progress_pct': overall_progress_pct,
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
    """Admin view: Create a new template and its questions (admin-style dynamic form)."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can create templates.")

    if request.method == 'POST':
        form = EvaluationTemplateForm(request.POST)
        if form.is_valid():
            # Check dynamic question inputs
            question_texts = request.POST.getlist('question_text')
            question_orders = request.POST.getlist('question_order')
            labels_0 = request.POST.getlist('label_0')
            labels_1 = request.POST.getlist('label_1')
            labels_2 = request.POST.getlist('label_2')
            labels_3 = request.POST.getlist('label_3')
            labels_4 = request.POST.getlist('label_4')
            labels_5 = request.POST.getlist('label_5')

            valid_questions = []
            for i, q_text in enumerate(question_texts):
                q_text = q_text.strip()
                if not q_text:
                    continue
                try:
                    ord_val = int(question_orders[i]) if i < len(question_orders) and question_orders[i] else len(valid_questions) + 1
                except (ValueError, IndexError):
                    ord_val = len(valid_questions) + 1

                l0 = labels_0[i].strip() if i < len(labels_0) and labels_0[i].strip() else '0 - Not Acceptable / NA'
                l1 = labels_1[i].strip() if i < len(labels_1) and labels_1[i].strip() else '1 - Poor'
                l2 = labels_2[i].strip() if i < len(labels_2) and labels_2[i].strip() else '2 - Below Average'
                l3 = labels_3[i].strip() if i < len(labels_3) and labels_3[i].strip() else '3 - Average'
                l4 = labels_4[i].strip() if i < len(labels_4) and labels_4[i].strip() else '4 - Good'
                l5 = labels_5[i].strip() if i < len(labels_5) and labels_5[i].strip() else '5 - Excellent'

                valid_questions.append({
                    'question_text': q_text,
                    'order': ord_val,
                    'label_0': l0,
                    'label_1': l1,
                    'label_2': l2,
                    'label_3': l3,
                    'label_4': l4,
                    'label_5': l5,
                })

            # Fallback if questions_input textarea was used
            questions_text = form.cleaned_data.get('questions_input', '')
            if not valid_questions and questions_text:
                lines = [q.strip() for q in questions_text.splitlines() if q.strip()]
                for order, line in enumerate(lines, start=1):
                    valid_questions.append({
                        'question_text': line,
                        'order': order,
                        'label_0': '0 - Not Acceptable / NA',
                        'label_1': '1 - Poor',
                        'label_2': '2 - Below Average',
                        'label_3': '3 - Average',
                        'label_4': '4 - Good',
                        'label_5': '5 - Excellent',
                    })

            if not valid_questions:
                messages.error(request, "Please add at least one question to the template.")
                return render(request, 'evaluations/admin/template_form.html', {
                    'form': form,
                    'title': 'Create Evaluation Template',
                    'active_menu': 'templates',
                })

            template = form.save(commit=False)
            template.created_by = request.user
            template.save()

            for q_data in valid_questions:
                Question.objects.create(template=template, **q_data)

            messages.success(request, f"Template '{template.title}' created with {len(valid_questions)} questions!")
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
    """Admin view: List all care units. Select a unit to view its employees."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can view units.")

    units = Unit.objects.all().prefetch_related('users', 'evaluations')
    return render(request, 'evaluations/admin/unit_list.html', {
        'units': units,
        'active_menu': 'units',
    })


@login_required(login_url='users:login')
def unit_detail(request, pk):
    """Admin view: Show employees assigned to a selected care unit."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can view units.")

    unit = get_object_or_404(
        Unit.objects.prefetch_related('users', 'evaluations'),
        pk=pk,
    )
    employees = unit.users.all().order_by('first_name', 'last_name', 'username')
    return render(request, 'evaluations/admin/unit_detail.html', {
        'unit': unit,
        'employees': employees,
        'active_menu': 'units',
    })


@login_required(login_url='users:login')
def unit_create(request):
    """Admin view: Create a new care unit. Staff are assigned from the employee page."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can create units.")

    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f"Unit '{unit.name}' created successfully!")
            return redirect('evaluations:unit_detail', pk=unit.pk)
    else:
        form = UnitForm()

    return render(request, 'evaluations/admin/unit_form.html', {
        'form': form,
        'title': 'Create Care Unit',
        'subtitle': 'Add a care unit. Assign each employee to one unit from the employee page.',
        'active_menu': 'units',
    })


@login_required(login_url='users:login')
def unit_edit(request, pk):
    """Admin view: Update a care unit name and location."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can edit units.")

    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f"Unit '{unit.name}' updated successfully!")
            return redirect('evaluations:unit_detail', pk=unit.pk)
    else:
        form = UnitForm(instance=unit)

    return render(request, 'evaluations/admin/unit_form.html', {
        'form': form,
        'unit': unit,
        'title': 'Edit Care Unit',
        'subtitle': 'Update this unit name or location. Staff stay assigned from the employee page.',
        'active_menu': 'units',
    })



@login_required(login_url='users:login')
def admin_submissions_list(request):
    """Admin view: Global list of all employee evaluations submissions grouped unit-wise."""
    if not is_admin(request.user):
        raise PermissionDenied("Only administrators can view user evaluation data.")

    submissions_qs = EvaluationSubmission.objects.all().select_related(
        'evaluation', 'evaluator', 'evaluatee', 'unit'
    ).prefetch_related('ratings')

    selected_unit_id = request.GET.get('unit', '')
    search_q = request.GET.get('q', '').strip().lower()

    if selected_unit_id and selected_unit_id.isdigit():
        submissions_qs = submissions_qs.filter(unit_id=int(selected_unit_id))

    # Group submissions by unit
    units_dict = {}
    for sub in submissions_qs:
        if search_q:
            evaluator_name = (sub.evaluator.get_full_name() or sub.evaluator.username).lower()
            evaluatee_name = (sub.evaluatee.get_full_name() or sub.evaluatee.username).lower()
            eval_title = sub.evaluation.title.lower()
            if search_q not in evaluator_name and search_q not in evaluatee_name and search_q not in eval_title:
                continue

        unit_key = sub.unit.id if sub.unit else 0
        if unit_key not in units_dict:
            units_dict[unit_key] = {
                'unit': sub.unit,
                'unit_name': sub.unit.name if sub.unit else 'General / Unassigned',
                'unit_place': sub.unit.place if sub.unit else 'Facility-wide',
                'submissions': [],
                'total_score': 0.0,
                'count': 0,
            }
        units_dict[unit_key]['submissions'].append(sub)
        units_dict[unit_key]['total_score'] += float(sub.average_score or 0)
        units_dict[unit_key]['count'] += 1

    unit_groups = []
    for g in units_dict.values():
        g['avg_score'] = round(g['total_score'] / g['count'], 1) if g['count'] > 0 else 0.0
        unit_groups.append(g)

    unit_groups.sort(key=lambda x: x['unit_name'])
    all_units = Unit.objects.all()

    return render(request, 'evaluations/admin/submission_list.html', {
        'unit_groups': unit_groups,
        'all_units': all_units,
        'selected_unit_id': selected_unit_id,
        'search_q': search_q,
        'total_submissions': submissions_qs.count(),
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
    """User view: List active evaluations that have reached start_date and colleagues to evaluate."""
    user = request.user
    user_units = user.assigned_units.all()
    today = timezone.now().date()

    # Find evaluations where user's unit is tagged AND start_date has arrived (start_date <= today)
    available_evaluations = Evaluation.objects.filter(
        status__in=['not_started', 'in_progress', 'active'],
        start_date__lte=today,
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
    if evaluation.is_upcoming:
        messages.warning(
            request,
            f"This evaluation is scheduled to start on {evaluation.start_date.strftime('%B %d, %Y')}. It is not open for rating yet."
        )
        return redirect('evaluations:user_evaluations')

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

            # Sync evaluation status dynamically (transitions to in_progress or completed)
            evaluation.sync_status()

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
    """User view: View past peer evaluations submitted by the logged in employee, grouped unit-wise."""
    submissions = EvaluationSubmission.objects.filter(
        evaluator=request.user
    ).select_related('evaluation', 'evaluatee', 'unit').prefetch_related('ratings')

    # Group submissions by unit
    units_dict = {}
    for sub in submissions:
        unit_key = sub.unit.id if sub.unit else 0
        if unit_key not in units_dict:
            units_dict[unit_key] = {
                'unit': sub.unit,
                'unit_name': sub.unit.name if sub.unit else 'General / Unassigned',
                'unit_place': sub.unit.place if sub.unit else 'Facility-wide',
                'submissions': [],
                'total_score': 0.0,
                'count': 0,
            }
        units_dict[unit_key]['submissions'].append(sub)
        units_dict[unit_key]['total_score'] += float(sub.average_score or 0)
        units_dict[unit_key]['count'] += 1

    unit_groups = []
    for g in units_dict.values():
        g['avg_score'] = round(g['total_score'] / g['count'], 1) if g['count'] > 0 else 0.0
        unit_groups.append(g)

    unit_groups.sort(key=lambda x: x['unit_name'])

    return render(request, 'evaluations/user/my_history.html', {
        'unit_groups': unit_groups,
        'total_submissions': submissions.count(),
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
