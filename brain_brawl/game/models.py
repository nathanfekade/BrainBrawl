from django.db import models
from django.contrib.auth.models import User
from . import validators as validate

class Group(models.Model):
    group_name = models.CharField(max_length=100, unique=True)
    creator = models.ForeignKey(User, related_name='created_groups', on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/', validators=[validate.validate_file_size_and_type])

    def __str__(self):
        return self.group_name

class GroupMember(models.Model):
    group = models.ForeignKey(Group, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='group_memberships', on_delete=models.CASCADE)

    class Meta:
        unique_together = (('group', 'user'),)

    def __str__(self):
        return f"{self.user.username} in {self.group.group_name}"

class Quiz(models.Model):
    group = models.ForeignKey(Group, related_name='quizzes', on_delete=models.CASCADE)
    start_time = models.DateTimeField()

    def __str__(self):
        return f"Quiz {self.id} for {self.group.group_name}"

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=500)

    def __str__(self):
        return f"Question {self.id} for Quiz {self.quiz.id}"

class UserGroupScore(models.Model):
    group = models.ForeignKey(Group, related_name='scores', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='group_scores', on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = (('group', 'user'),)

    def __str__(self):
        return f"{self.user.username}: {self.points} pts in {self.group.group_name}"
