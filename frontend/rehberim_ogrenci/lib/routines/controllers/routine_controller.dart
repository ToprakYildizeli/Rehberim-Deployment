import 'package:flutter/foundation.dart';
import '../../data/models/routine_model.dart';
import '../../data/models/subject_model.dart';
import '../../data/models/task_type_model.dart';
import '../../data/repositories/routine_repository.dart';
import '../../data/services/api_exception.dart';

/// Öğrencinin rutin akışını yönetir: listeleme, oluşturma, güncelleme, silme
/// ve otomatik uygulamayı açıp kapatma.
class RoutineController extends ChangeNotifier {
  final RoutineRepository _repository;

  RoutineController({required this._repository});

  bool _isLoading = false;
  bool _isSubmitting = false;
  String? _errorMessage;
  ApiException? _lastError;

  bool get isLoading => _isLoading;
  bool get isSubmitting => _isSubmitting;
  String? get errorMessage => _errorMessage;
  ApiException? get lastError => _lastError;

  List<RoutineModel> _routines = const [];
  List<SubjectModel> _subjects = const [];
  List<TaskTypeModel> _taskTypes = const [];

  List<RoutineModel> get routines => _routines;
  List<SubjectModel> get subjects => _subjects;
  List<TaskTypeModel> get taskTypes => _taskTypes;

  /// Şu an otomatik uygulanan rutin (en fazla bir tane olabilir).
  RoutineModel? get activeRoutine {
    for (final r in _routines) {
      if (r.autoApply) return r;
    }
    return null;
  }

  Future<void> loadRoutines() async {
    _setLoading(true, clearError: true);
    try {
      _routines = await _repository.getRoutines();
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> loadReferenceData() async {
    if (_subjects.isNotEmpty && _taskTypes.isNotEmpty) return;
    _setLoading(true, clearError: true);
    try {
      _subjects = await _repository.getSubjects();
      _taskTypes = await _repository.getTaskTypes();
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> saveRoutine(RoutineModel routine) async {
    _setSubmitting(true, clearError: true);
    try {
      if (routine.id == null) {
        await _repository.createRoutine(routine);
      } else {
        await _repository.updateRoutine(routine.id!, routine);
      }
      _routines = await _repository.getRoutines();
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
  }

  Future<bool> setAutoApply(RoutineModel routine, bool value) async {
    if (routine.id == null) return false;
    _setSubmitting(true, clearError: true);
    try {
      await _repository.setAutoApply(routine.id!, value);
      _routines = await _repository.getRoutines();
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
  }

  Future<bool> deleteRoutine(RoutineModel routine) async {
    if (routine.id == null) return false;
    _setSubmitting(true, clearError: true);
    try {
      await _repository.deleteRoutine(routine.id!);
      _routines = await _repository.getRoutines();
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
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
    _routines = const [];
    _subjects = const [];
    _taskTypes = const [];
    _isLoading = false;
    _isSubmitting = false;
    _errorMessage = null;
    _lastError = null;
    notifyListeners();
  }
}
