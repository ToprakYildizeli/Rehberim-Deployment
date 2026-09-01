import '../models/program_model.dart';
import '../models/student_summary_model.dart';
import '../services/api_client.dart';

/// Haftalık program ile ilgili API çağrılarını yönetir.
///
/// Görev (Task) CRUD işlemleri [TaskRepository]'de yer alır.
class WeeklyProgramRepository {
  final ApiClient _apiClient;

  WeeklyProgramRepository({required this._apiClient});

  Future<List<ProgramModel>> getPrograms() async {
    try {
      final response = await _apiClient.dio.get('/programs/');
      final data = response.data;
      if (data is List) {
        return data
            .whereType<Map>()
            .map((item) => ProgramModel.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
      return const [];
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<ProgramModel> getProgram(int id) async {
    try {
      final response = await _apiClient.dio.get('/programs/$id/');
      return ProgramModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<ProgramModel> getCurrentProgram() async {
    try {
      final response = await _apiClient.dio.get('/programs/current/');
      return ProgramModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<List<StudentSummaryModel>> getStudents() async {
    try {
      final response = await _apiClient.dio.get('/students/');
      final data = response.data;
      if (data is List) {
        return data
            .whereType<Map>()
            .map((item) => StudentSummaryModel.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
      return const [];
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }
}
