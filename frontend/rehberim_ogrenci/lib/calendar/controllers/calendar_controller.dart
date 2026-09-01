import 'package:flutter/foundation.dart';
import '../../data/models/calendar_event_model.dart';
import '../../data/repositories/calendar_repository.dart';
import '../../data/services/api_exception.dart';

/// Öğrenci tarafındaki takvim (CalendarEvent) akışını yönetir.
///
/// Salt-okunur: öğrenci yalnızca kendisine bağlı etkinlikleri görüntüler,
/// oluşturma/güncelleme/silme rehbere özeldir (bkz. `CalendarRepository`).
class CalendarController extends ChangeNotifier {
  final CalendarRepository _repository;

  CalendarController({required this._repository});

  bool _isLoading = false;
  String? _errorMessage;
  ApiException? _lastError;

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  ApiException? get lastError => _lastError;

  List<CalendarEventModel> _events = const [];

  List<CalendarEventModel> get events => _events;

  Future<void> loadEvents({DateTime? from, DateTime? to}) async {
    _setLoading(true, clearError: true);
    try {
      _events = await _repository.getEvents(from: from, to: to);
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
    }
  }

  /// Belirli bir ayı kapsayan aralığı yükler; takvim sayfasında ay değişince
  /// çağrılmak üzere düşünülmüştür.
  Future<void> loadEventsForMonth(DateTime month) {
    final from = DateTime(month.year, month.month, 1);
    final to = DateTime(month.year, month.month + 1, 0);
    return loadEvents(from: from, to: to);
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

  /// Oturum değiştiğinde bellekteki veriyi temizler.
  void reset() {
    _events = const [];
    _isLoading = false;
    _errorMessage = null;
    _lastError = null;
    notifyListeners();
  }
}
