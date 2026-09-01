import '../models/routine_model.dart';
import '../models/subject_model.dart';
import '../models/task_type_model.dart';
import '../services/api_client.dart';

/// Rutin (tekrarlayan program) API çağrıları.
///
/// Uçlar: GET/POST `/program-templates/`, GET/PATCH/DELETE
/// `/program-templates/{id}/`. Öğrenci yalnızca **kendi** rutinlerini görür;
/// `student` alanı sunucuda oturum sahibine göre atanır, gövdeden gönderilmez
/// (bkz. `program-contract.md`, "Rutini kim kurar?").
class RoutineRepository {
  final ApiClient _apiClient;

  RoutineRepository({required this._apiClient});

  Future<List<RoutineModel>> getRoutines() async {
    try {
      final response = await _apiClient.dio.get('/program-templates/');
      final data = response.data;
      if (data is List) {
        return data
            .whereType<Map>()
            .map((item) => RoutineModel.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
      return const [];
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<RoutineModel> createRoutine(RoutineModel routine) async {
    try {
      final response = await _apiClient.dio.post(
        '/program-templates/',
        data: routine.toJson(),
      );
      return RoutineModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<RoutineModel> updateRoutine(int routineId, RoutineModel routine) async {
    try {
      final response = await _apiClient.dio.patch(
        '/program-templates/$routineId/',
        data: routine.toJson(),
      );
      return RoutineModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  /// Yalnızca otomatik uygulamayı açar/kapatır; görevlere dokunmaz.
  Future<RoutineModel> setAutoApply(int routineId, bool value) async {
    try {
      final response = await _apiClient.dio.patch(
        '/program-templates/$routineId/',
        data: {'auto_apply': value},
      );
      return RoutineModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<void> deleteRoutine(int routineId) async {
    try {
      await _apiClient.dio.delete('/program-templates/$routineId/');
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  /// Rutin görevi eklerken ders/metod seçimi için referans veri.
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
}
