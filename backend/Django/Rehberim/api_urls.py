from django.urls import path

from . import api_views

urlpatterns = [
    # Referans veri (dropdown'lar)
    path("subjects/", api_views.SubjectListView.as_view(), name="api-subjects"),
    path("task-types/", api_views.TaskTypeListView.as_view(), name="api-task-types"),
    path("publishers/", api_views.PublisherListView.as_view(), name="api-publishers"),
    path("block-durations/", api_views.BlockDurationDefaultListView.as_view(), name="api-block-durations"),

    # Programlar
    path("programs/", api_views.ProgramListCreateView.as_view(), name="api-programs"),
    path("programs/current/", api_views.CurrentProgramView.as_view(), name="api-program-current"),
    path("programs/assign/", api_views.ProgramAssignView.as_view(), name="api-program-assign"),
    path("programs/compliance/", api_views.ProgramComplianceView.as_view(), name="api-program-compliance"),
    path("programs/<int:pk>/", api_views.ProgramDetailView.as_view(), name="api-program-detail"),
    path("programs/<int:pk>/approve/", api_views.ProgramApprovalView.as_view(), name="api-program-approve"),

    # Program şablonları (rehberin tekrar kullanılabilir planları)
    path("program-templates/", api_views.ProgramTemplateListCreateView.as_view(), name="api-program-templates"),
    path("program-templates/<int:pk>/", api_views.ProgramTemplateDetailView.as_view(), name="api-program-template-detail"),

    # Görevler (Task) — programa bağlı
    path("programs/<int:program_pk>/tasks/", api_views.TaskListCreateView.as_view(), name="api-program-tasks"),
    path("tasks/<int:pk>/", api_views.TaskDetailView.as_view(), name="api-task-detail"),

    # Başarımlar (C3) — tanımlar rehbere ait, ilerleme öğrenci bazında hesaplanır
    path("achievements/", api_views.AchievementListCreateView.as_view(), name="api-achievements"),
    path("achievements/progress/", api_views.AchievementProgressView.as_view(), name="api-achievement-progress"),
    path("achievements/<int:pk>/", api_views.AchievementDetailView.as_view(), name="api-achievement-detail"),

    # Çalışma istatistikleri (E2)
    path("study-stats/", api_views.StudyStatsView.as_view(), name="api-study-stats"),

    # Denemeler (ExamResult)
    path("exams/", api_views.ExamResultListCreateView.as_view(), name="api-exams"),
    path("exams/<int:pk>/", api_views.ExamResultDetailView.as_view(), name="api-exam-detail"),

    # Hedefler (Goal)
    path("goals/", api_views.GoalListCreateView.as_view(), name="api-goals"),
    path("goals/<int:pk>/", api_views.GoalDetailView.as_view(), name="api-goal-detail"),

    # Kitaplık (Book) + kitap içi konular (BookTopic)
    path("books/", api_views.BookListCreateView.as_view(), name="api-books"),
    path("books/<int:pk>/", api_views.BookDetailView.as_view(), name="api-book-detail"),
    path("book-topics/<int:pk>/", api_views.BookTopicDetailView.as_view(), name="api-book-topic-detail"),

    # Konular (Topic katalog + öğrenci ilerlemesi)
    path("topics/", api_views.TopicListView.as_view(), name="api-topics"),
    path("topic-progress/", api_views.TopicProgressListCreateView.as_view(), name="api-topic-progress"),
    path("topic-progress/<int:pk>/", api_views.TopicProgressDetailView.as_view(), name="api-topic-progress-detail"),

    # Takvim (CalendarEvent)
    path("calendar/", api_views.CalendarEventListCreateView.as_view(), name="api-calendar"),
    path("calendar/<int:pk>/", api_views.CalendarEventDetailView.as_view(), name="api-calendar-detail"),
]
