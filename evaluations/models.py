from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Unit(models.Model):
    name = models.CharField(max_length=150, help_text="e.g. Sunrise Care Wing, Ward 3")
    place = models.CharField(max_length=200, help_text="e.g. Building A - Level 2")
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_units',
        blank=True,
        help_text="Employees assigned to this unit"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.place})"

    @property
    def total_employees(self):
        return self.users.count()


class EvaluationTemplate(models.Model):
    title = models.CharField(max_length=200, help_text="e.g. Monthly Clinical Care & Hygiene Standards")
    description = models.TextField(blank=True, help_text="Instructions or scope of the template")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def questions_count(self):
        return self.questions.count()


class Question(models.Model):
    template = models.ForeignKey(
        EvaluationTemplate,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.CharField(max_length=500)
    order = models.PositiveIntegerField(default=1)

    # Dynamic Choice Labels for permanent scores 0 to 5
    label_0 = models.CharField(max_length=120, default='0 - Not Acceptable / NA', help_text="Text for score 0")
    label_1 = models.CharField(max_length=120, default='1 - Poor', help_text="Text for score 1")
    label_2 = models.CharField(max_length=120, default='2 - Below Average', help_text="Text for score 2")
    label_3 = models.CharField(max_length=120, default='3 - Average', help_text="Text for score 3")
    label_4 = models.CharField(max_length=120, default='4 - Good', help_text="Text for score 4")
    label_5 = models.CharField(max_length=120, default='5 - Excellent', help_text="Text for score 5")

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.order}: {self.question_text}"

    @property
    def choices(self):
        """Returns list of (score, label) tuples for scores 0 to 5."""
        return [
            (0, self.label_0),
            (1, self.label_1),
            (2, self.label_2),
            (3, self.label_3),
            (4, self.label_4),
            (5, self.label_5),
        ]

    def get_label_for_score(self, score):
        labels = {
            0: self.label_0,
            1: self.label_1,
            2: self.label_2,
            3: self.label_3,
            4: self.label_4,
            5: self.label_5,
        }
        return labels.get(score, str(score))


class Evaluation(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('draft', 'Draft'),
    )

    title = models.CharField(max_length=200, help_text="e.g. Q4 Care Performance Evaluation")
    description = models.TextField(blank=True)
    template = models.ForeignKey(
        EvaluationTemplate,
        on_delete=models.CASCADE,
        related_name='evaluations',
        help_text="Template containing questions for this evaluation"
    )
    units = models.ManyToManyField(
        Unit,
        related_name='evaluations',
        blank=True,
        help_text="Units tagged to this evaluation (all employees in these units evaluate peers)"
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='tagged_evaluations',
        blank=True,
        help_text="Directly tagged users"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_evaluations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def is_user_eligible(self, user):
        """Check if user belongs to tagged units or is directly tagged, or is admin."""
        if user.is_superuser or getattr(user, 'role', '') == 'admin':
            return True
        if self.users.filter(id=user.id).exists():
            return True
        return self.units.filter(users=user).exists()

    def get_peers_to_evaluate(self, user):
        """
        Returns colleagues in the user's unit(s) tagged in this evaluation,
        excluding the user themselves.
        """
        user_units = self.units.filter(users=user)
        if not user_units.exists():
            from users.models import User
            return User.objects.none()
        from users.models import User
        return User.objects.filter(assigned_units__in=user_units).exclude(id=user.id).distinct()

    def get_user_progress(self, user):
        """Returns (completed_count, total_peers_count) for the logged-in evaluator."""
        peers = self.get_peers_to_evaluate(user)
        total = peers.count()
        completed = self.submissions.filter(evaluator=user, evaluatee__in=peers).count()
        return completed, total

    def is_peer_evaluated_by(self, evaluator, evaluatee):
        return self.submissions.filter(evaluator=evaluator, evaluatee=evaluatee).exists()

    def get_peer_submission(self, evaluator, evaluatee):
        return self.submissions.filter(evaluator=evaluator, evaluatee=evaluatee).first()


class EvaluationSubmission(models.Model):
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='evaluations_given',
        help_text="Employee providing the evaluation"
    )
    evaluatee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='evaluations_received',
        help_text="Employee being evaluated"
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submissions',
        help_text="The care unit this peer evaluation belongs to"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True, null=True, help_text="Optional general feedback or comments for this colleague")

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ('evaluation', 'evaluator', 'evaluatee')

    def __str__(self):
        return f"{self.evaluator.username} evaluated {self.evaluatee.username} - {self.evaluation.title}"

    @property
    def average_score(self):
        ratings = self.ratings.all()
        if not ratings:
            return 0
        total = sum(r.score for r in ratings)
        return round(total / len(ratings), 2)


class Rating(models.Model):
    # The scores 0-5 are permanent numeric values
    SCORE_CHOICES = [(i, str(i)) for i in range(6)]

    submission = models.ForeignKey(
        EvaluationSubmission,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    score = models.IntegerField(
        choices=SCORE_CHOICES,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Permanent numeric score from 0 to 5"
    )
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('submission', 'question')

    def __str__(self):
        return f"Q: {self.question_id} -> {self.score_label}"

    @property
    def score_label(self):
        """Dynamically pulls the descriptive text defined for this score on the specific question."""
        return self.question.get_label_for_score(self.score)
