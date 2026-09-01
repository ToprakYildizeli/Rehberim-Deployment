import 'package:flutter/foundation.dart';
import '../../data/models/program_model.dart';
import '../../data/models/subject_model.dart';
import '../../data/models/task_model.dart';
import '../../data/models/task_type_model.dart';
import '../../data/repositories/task_repository.dart';
import '../../data/services/api_exception.dart';

/// Öğrenci tarafındaki görev (Task) akışını yönetir: listeleme, oluşturma,
/// güncelleme, tamamlama ve silme.
class TaskController extends ChangeNotifier {
  final TaskRepository _repository;

  TaskController({required this._repository});

  bool _isLoading = false;
  bool _isSubmitting = false;
  String? _errorMessage;
  ApiException? _lastError;

  bool get isLoading => _isLoading;
  bool get isSubmitting => _isSubmitting;
  String? get errorMessage => _errorMessage;
  ApiException? get lastError => _lastError;

  List<TaskModel> _tasks = const [];
  List<SubjectModel> _subjects = const [];
  List<TaskTypeModel> _taskTypes = const [];

  List<TaskModel> get tasks => _tasks;
  List<SubjectModel> get subjects => _subjects;
  List<TaskTypeModel> get taskTypes => _taskTypes;

  Future<void> loadTasks(int programId) async {
    _setLoading(true, clearError: true);
    try {
      _tasks = await _repository.getTasks(programId);
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> loadReferenceData() async {
    _setLoading(true, clearError: true);
    try {
      final subjectsFuture = _repository.getSubjects();
      final taskTypesFuture = _repository.getTaskTypes();

      final results = await Future.wait([subjectsFuture, taskTypesFuture]);
      _subjects = results[0] as List<SubjectModel>;
      _taskTypes = results[1] as List<TaskTypeModel>;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> createTask({
    required int programId,
    required String title,
    required DateTime date,
    required ScheduleType scheduleType,
    int? subjectId,
    int? taskTypeId,
    String? description,
    String? startTime,
    int? durationMinutes,
    int? order,
  }) async {
    _setSubmitting(true, clearError: true);
    try {
      final createdTask = await _repository.createTask(
        programId: programId,
        title: title,
        date: date,
        scheduleType: scheduleType,
        subjectId: subjectId,
        taskTypeId: taskTypeId,
        description: description,
        startTime: startTime,
        durationMinutes: durationMinutes,
        order: order,
      );
      _tasks = [..._tasks, createdTask];
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
  }

  Future<bool> updateTask({
    required int taskId,
    String? title,
    String? description,
    DateTime? date,
    bool? isCompleted,
    int? subjectId,
    int? taskTypeId,
    String? startTime,
    int? durationMinutes,
    int? order,
  }) async {
    _setSubmitting(true, clearError: true);
    try {
      final updatedTask = await _repository.updateTask(
        taskId: taskId,
        title: title,
        description: description,
        date: date,
        isCompleted: isCompleted,
        subjectId: subjectId,
        taskTypeId: taskTypeId,
        startTime: startTime,
        durationMinutes: durationMinutes,
        order: order,
      );
      _tasks = _tasks.map((task) => task.id == taskId ? updatedTask : task).toList();
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
  }

  /// Görevi tamamlandı/tamamlanmadı olarak işaretlemek için kısayol.
  Future<bool> toggleCompletion(int taskId, bool isCompleted, {String? description}) {
    return updateTask(
      taskId: taskId,
      isCompleted: isCompleted,
      description: description,
    );
  }

  Future<bool> deleteTask(int taskId) async {
    _setSubmitting(true, clearError: true);
    try {
      await _repository.deleteTask(taskId);
      _tasks = _tasks.where((task) => task.id != taskId).toList();
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
  }

  void clearError() {
    _errorMessage = null;
    _lastError = null;
    notifyListeners();
  }

  void _setLoading(bool value, {bool clearError = false}) {
    _isLoading = value;
    if (clearError) {
      _errorMessage = null;
      _lastError = null;
    }
    notifyListeners();
  }

  void _setSubmitting(bool value, {bool clearError = false}) {
    _isSubmitting = value;
    if (clearError) {
      _errorMessage = null;
      _lastError = null;
    }
    notifyListeners();
  }

  /// Oturum değiştiğinde bellekteki veriyi temizler.
  void reset() {
    _tasks = const [];
    _subjects = const [];
    _taskTypes = const [];
    _isLoading = false;
    _isSubmitting = false;
    _errorMessage = null;
    _lastError = null;
    notifyListeners();
  }
}
