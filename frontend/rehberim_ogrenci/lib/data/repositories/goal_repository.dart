import '../models/goal_model.dart';
import '../models/subject_model.dart';
import '../services/api_client.dart';

/// Hedef (Goal) ile ilgili API çağrılarını yönetir.
///
/// Öğrenci uçları: GET/POST `/goals/`, GET/PATCH/DELETE `/goals/{id}/`.
/// `student` alanı sunucuda oturum sahibi öğrenciye göre atanır; buradan
/// gönderilmesine gerek yoktur (ve backend zaten yok sayar). Hedef sahibi
/// öğrenci tam yetkiliyken rehberi ve velisi yalnızca okuyabilir.
class GoalRepository {
  final ApiClient _apiClient;

  GoalRepository({required this._apiClient});

  Future<List<GoalModel>> getGoals() async {
    try {
      final response = await _apiClient.dio.get('/goals/');
      final data = response.data;
      if (data is List) {
        return data
            .whereType<Map>()
            .map((item) => GoalModel.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
      return const [];
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<GoalModel> getGoal(int goalId) async {
    try {
      final response = await _apiClient.dio.get('/goals/$goalId/');
      return GoalModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<GoalModel> createGoal({
    required GoalType goalType,
    String? title,
    String? description,
    DateTime? targetDate,
    bool isAchieved = false,
    ExamScope examScope = ExamScope.none,
    int? subjectId,
    double? targetNet,
  }) async {
    try {
      final payload = GoalModel(
        goalType: goalType,
        title: title,
        description: description,
        targetDate: targetDate,
        isAchieved: isAchieved,
        examScope: examScope,
        subjectId: subjectId,
        targetNet: targetNet,
      ).toJson();

      final response = await _apiClient.dio.post('/goals/', data: payload);
      return GoalModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<GoalModel> updateGoal({
    required int goalId,
    GoalType? goalType,
    String? title,
    String? description,
    DateTime? targetDate,
    bool? isAchieved,
    ExamScope? examScope,
    int? subjectId,
    double? targetNet,
  }) async {
    try {
      final payload = <String, dynamic>{};
      if (title != null) payload['title'] = title;
      if (description != null) payload['description'] = description;
      if (targetDate != null) payload['target_date'] = _formatDate(targetDate);
      if (isAchieved != null) payload['is_achieved'] = isAchieved;

      if (goalType != null) {
        // Tür bilgisi geldiğinde deneme alanları o türe göre yeniden
        // belirlenir — böylece türü değiştirmek (ör. deneme netinden konu
        // hedefine) veya "Toplam" dersini (null) yeniden seçmek eski
        // değerleri arkada bırakmaz.
        payload['goal_type'] = goalType.apiValue;
        if (goalType == GoalType.denemeNeti) {
          payload['exam_scope'] = (examScope ?? ExamScope.none).apiValue;
          payload['subject'] = subjectId;
          payload['target_net'] = targetNet;
        } else {
          payload['exam_scope'] = '';
          payload['subject'] = null;
          payload['target_net'] = null;
        }
      } else {
        if (examScope != null) payload['exam_scope'] = examScope.apiValue;
        if (subjectId != null) payload['subject'] = subjectId;
        if (targetNet != null) payload['target_net'] = targetNet;
      }

      final response = await _apiClient.dio.patch('/goals/$goalId/', data: payload);
      return GoalModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<void> deleteGoal(int goalId) async {
    try {
      await _apiClient.dio.delete('/goals/$goalId/');
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  /// Deneme neti hedefinde ders seçimi için referans veri. `TaskRepository`
  /// / `ExamRepository` ile aynı uca gider; her repository kendi ihtiyacı
  /// için bağımsız çağırır.
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

  String _formatDate(DateTime value) {
    return '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
  }
}
