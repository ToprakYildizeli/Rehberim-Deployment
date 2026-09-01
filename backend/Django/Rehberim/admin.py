from django.contrib import admin

from .models import (
    BlockDurationDefault, Book, BookTopic, CalendarEvent, ExamResult, Goal,
    Publisher, Subject, SubjectNet, Task, TaskType, Topic, TopicProgress,
    WeeklyProgram,
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    ordering = ('category', 'name')


class SubjectNetInline(admin.TabularInline):
    model = SubjectNet
    extra = 1
    autocomplete_fields = ()


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'student', 'exam_type', 'exam_date', 'total_net')
    list_filter = ('exam_type', 'exam_date')
    inlines = [SubjectNetInline]


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    fields = ('date', 'start_time', 'duration_minutes', 'kind', 'exam_scope',
              'subject', 'task_type', 'title', 'is_completed', 'order')


@admin.register(WeeklyProgram)
class WeeklyProgramAdmin(admin.ModelAdmin):
    list_display = ('student', 'start_date', 'day_count', 'end_date', 'schedule_type',
                    'counselor', 'created_at')
    list_filter = ('schedule_type', 'start_date', 'counselor')
    date_hierarchy = 'start_date'
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('program', 'date', 'start_time', 'end_time', 'kind', 'subject',
                    'task_type', 'title', 'is_completed', 'created_by')
    list_filter = ('kind', 'is_completed', 'date', 'task_type', 'subject')


@admin.register(BlockDurationDefault)
class BlockDurationDefaultAdmin(admin.ModelAdmin):
    list_display = ('counselor', 'subject', 'task_type', 'topic', 'duration_minutes',
                    'updated_at')
    list_filter = ('counselor', 'subject', 'task_type')
    search_fields = ('topic',)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'student', 'goal_type', 'target_date', 'is_achieved', 'created_at')
    list_filter = ('goal_type', 'is_achieved', 'target_date')
    search_fields = ('title', 'student__user__first_name', 'student__user__last_name')


class BookTopicInline(admin.TabularInline):
    model = BookTopic
    extra = 0
    fields = ('topic', 'status', 'tests_solved', 'order')
    raw_id_fields = ('topic',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'student', 'kind', 'subject', 'book_format', 'status', 'created_at')
    list_filter = ('kind', 'book_format', 'status', 'subject')
    search_fields = ('title', 'publisher', 'author',
                     'student__user__first_name', 'student__user__last_name')
    inlines = [BookTopicInline]


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'grade', 'curriculum', 'order')
    list_filter = ('curriculum', 'grade', 'subject')
    search_fields = ('name',)
    ordering = ('subject', 'grade', 'order')


@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'student', 'topic', 'status', 'tests_solved', 'updated_at')
    list_filter = ('status', 'topic__grade', 'topic__subject')
    search_fields = ('topic__name', 'student__user__first_name', 'student__user__last_name')


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'end_time', 'counselor', 'student')
    list_filter = ('date', 'counselor')
    date_hierarchy = 'date'
    search_fields = ('title',)
