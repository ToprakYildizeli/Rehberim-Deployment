import 'package:flutter/foundation.dart';
import '../../data/models/program_model.dart';
import '../../data/models/student_summary_model.dart';
import '../../data/repositories/weekly_program_repository.dart';
import '../../data/services/api_exception.dart';

/// Öğrenci tarafındaki haftalık program akışını yönetir.
///
/// Görev (Task) CRUD işlemleri için [TaskController] kullanılır; bu controller
/// yalnızca program listeleme/seçme ile ilgilenir.
class WeeklyProgramController extends ChangeNotifier {
  final WeeklyProgramRepository _repository;

  WeeklyProgramController({required this._repository});

  bool _isLoading = false;
  String? _errorMessage;
  ApiException? _lastError;

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  ApiException? get lastError => _lastError;

  List<ProgramModel> _programs = const [];
  ProgramModel? _currentProgram;
  List<StudentSummaryModel> _students = const [];

  List<ProgramModel> get programs => _programs;
  ProgramModel? get currentProgram => _currentProgram;
  List<StudentSummaryModel> get students => _students;

  Future<void> loadPrograms() async {
    _setLoading(true, clearError: true);
    try {
      _programs = await _repository.getPrograms();
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> loadCurrentProgram() async {
    _setLoading(true, clearError: true);
    try {
      _currentProgram = await _repository.getCurrentProgram();
    } on ApiException catch (e) {
      // Aktif program yoksa sunucu 404 döner. Eski değeri BIRAKMAMAK kritik:
      // başka bir hesaba geçildiğinde önceki kullanıcının programı ekranda
      // kalıyordu.
      _currentProgram = null;
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
    }
  }

  /// Oturum değiştiğinde çağrılır — bellekteki her şeyi temizler ki yeni
  /// kullanıcı önceki hesabın verisini görmesin.
  void reset() {
    _programs = const [];
    _currentProgram = null;
    _students = const [];
    _isLoading = false;
    _errorMessage = null;
    _lastError = null;
    notifyListeners();
  }

  Future<void> loadProgramDetails(int programId) async {
    _setLoading(true, clearError: true);
    try {
      _currentProgram = await _repository.getProgram(programId);
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> selectProgram(int programId) async {
    _setLoading(true, clearError: true);
    try {
      _currentProgram = await _repository.getProgram(programId);
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
      _students = await _repository.getStudents();
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
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
}
