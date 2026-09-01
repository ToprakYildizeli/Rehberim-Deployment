import '../models/program_model.dart';
import '../models/subject_model.dart';
import '../models/task_model.dart';
import '../models/task_type_model.dart';
import '../services/api_client.dart';

/// Görev (Task) ile ilgili API çağrılarını yönetir.
class TaskRepository {
  final ApiClient _apiClient;

  TaskRepository({required this._apiClient});

  Future<List<TaskModel>> getTasks(int programId) async {
    try {
      final response = await _apiClient.dio.get('/programs/$programId/tasks/');
      final data = response.data;
      if (data is List) {
        return data
            .whereType<Map>()
            .map((item) => TaskModel.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
      return const [];
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<TaskModel> getTask(int taskId) async {
    try {
      final response = await _apiClient.dio.get('/tasks/$taskId/');
      return TaskModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<TaskModel> createTask({
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
    try {
      final payload = <String, dynamic>{
        'title': title,
        'date': _formatDate(date),
        'subject': ?subjectId,
        'task_type': ?taskTypeId,
        if (description != null && description.isNotEmpty) 'description': description,
        'order': ?order,
      };

      if (scheduleType == ScheduleType.timed) {
        payload['start_time'] = startTime ?? '';
        payload['duration_minutes'] = durationMinutes ?? 0;
      }

      final response = await _apiClient.dio.post('/programs/$programId/tasks/', data: payload);
      return TaskModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<TaskModel> updateTask({
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
    try {
      final payload = <String, dynamic>{};
      if (title != null) payload['title'] = title;
      if (description != null) payload['description'] = description;
      if (date != null) payload['date'] = _formatDate(date);
      if (isCompleted != null) payload['is_completed'] = isCompleted;
      if (subjectId != null) payload['subject'] = subjectId;
      if (taskTypeId != null) payload['task_type'] = taskTypeId;
      if (startTime != null) payload['start_time'] = startTime;
      if (durationMinutes != null) payload['duration_minutes'] = durationMinutes;
      if (order != null) payload['order'] = order;

      final response = await _apiClient.dio.patch('/tasks/$taskId/', data: payload);
      return TaskModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<void> deleteTask(int taskId) async {
    try {
      await _apiClient.dio.delete('/tasks/$taskId/');
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<List<SubjectModel>> getSubjects() async {
    try {
      final response = await _apiClient.dio.get('/subjects/');
      final data = response.data;
      if (data is List) {
        return data
            .whereType<Map>()
            .map((item) => SubjectModel.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
      return const [];
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<List<TaskTypeModel>> getTaskTypes() async {
    try {
      final response = await _apiClient.dio.get('/task-types/');
      final data = response.data;
      if (data is List) {
        return data
            .whereType<Map>()
            .map((item) => TaskTypeModel.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
      return const [];
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  String _formatDate(DateTime value) {
    return '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
  }
}
