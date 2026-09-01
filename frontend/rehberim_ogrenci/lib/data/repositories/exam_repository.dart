import '../models/exam_model.dart';
import '../models/subject_model.dart';
import '../models/subject_net_model.dart';
import '../services/api_client.dart';

/// Deneme sonucu (ExamResult) ile ilgili API çağrılarını yönetir.
///
/// Öğrenci uçları: GET/POST `/exams/`, GET/PATCH/DELETE `/exams/{id}/`.
/// `student` alanı sunucuda oturum sahibi öğrenciye göre atanır; buradan
/// gönderilmesine gerek yoktur (ve backend zaten yok sayar).
class ExamRepository {
  final ApiClient _apiClient;

  ExamRepository({required this._apiClient});

  Future<List<ExamModel>> getExams({int? studentId}) async {
    try {
      final response = await _apiClient.dio.get(
        '/exams/',
        queryParameters: studentId != null ? {'student': studentId} : null,
      );
      final data = response.data;
      if (data is List) {
        return data
            .whereType<Map>()
            .map((item) => ExamModel.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
      return const [];
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<ExamModel> getExam(int examId) async {
    try {
      final response = await _apiClient.dio.get('/exams/$examId/');
      return ExamModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<ExamModel> createExam({
    required DateTime examDate,
    required List<SubjectNetModel> subjectNets,
    ExamType examType = ExamType.none,
    String? name,
  }) async {
    try {
      final payload = <String, dynamic>{
        'exam_date': _formatDate(examDate),
        'exam_type': examType.apiValue,
        'subject_nets': subjectNets.map((net) => net.toJson()).toList(),
      };
      if (name != null && name.isNotEmpty) payload['name'] = name;

      final response = await _apiClient.dio.post('/exams/', data: payload);
      return ExamModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<ExamModel> updateExam({
    required int examId,
    DateTime? examDate,
    ExamType? examType,
    String? name,
    List<SubjectNetModel>? subjectNets,
  }) async {
    try {
      final payload = <String, dynamic>{};
      if (examDate != null) payload['exam_date'] = _formatDate(examDate);
      if (examType != null) payload['exam_type'] = examType.apiValue;
      if (name != null) payload['name'] = name;
      if (subjectNets != null) {
        payload['subject_nets'] = subjectNets.map((net) => net.toJson()).toList();
      }

      final response = await _apiClient.dio.patch('/exams/$examId/', data: payload);
      return ExamModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<void> deleteExam(int examId) async {
    try {
      await _apiClient.dio.delete('/exams/$examId/');
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  /// Net girişinde ders seçimi için referans veri. `TaskRepository.getSubjects`
  /// ile aynı uca gider; her repository kendi ihtiyacı için bağımsız çağırır.
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
