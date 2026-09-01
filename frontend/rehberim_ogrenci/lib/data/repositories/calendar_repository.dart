import '../models/calendar_event_model.dart';
import '../services/api_client.dart';

/// Takvim etkinliği (CalendarEvent) ile ilgili API çağrılarını yönetir.
///
/// Öğrenci uçları salt-okunurdur: GET `/calendar/`, GET `/calendar/{id}/`.
/// Etkinlik oluşturma/düzenleme/silme rehbere özeldir (`IsCounselor`); bu
/// yüzden bu repository kasıtlı olarak yalnızca okuma metodları sunar.
class CalendarRepository {
  final ApiClient _apiClient;

  CalendarRepository({required this._apiClient});

  /// [from]/[to] verilirse tarih aralığına göre filtreler (backend'de
  /// `?from=&to=`, dahil-dahil).
  Future<List<CalendarEventModel>> getEvents({DateTime? from, DateTime? to}) async {
    try {
      final queryParameters = <String, dynamic>{
        if (from != null) 'from': _formatDate(from),
        if (to != null) 'to': _formatDate(to),
      };
      final response = await _apiClient.dio.get(
        '/calendar/',
        queryParameters: queryParameters.isEmpty ? null : queryParameters,
      );
      final data = response.data;
      if (data is List) {
        return data
            .whereType<Map>()
            .map((item) => CalendarEventModel.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
      return const [];
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  Future<CalendarEventModel> getEvent(int eventId) async {
    try {
      final response = await _apiClient.dio.get('/calendar/$eventId/');
      return CalendarEventModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  String _formatDate(DateTime value) {
    return '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
  }
}
