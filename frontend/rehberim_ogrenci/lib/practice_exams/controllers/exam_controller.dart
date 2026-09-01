import 'package:flutter/foundation.dart';
import '../../data/models/exam_model.dart';
import '../../data/models/subject_model.dart';
import '../../data/models/subject_net_model.dart';
import '../../data/repositories/exam_repository.dart';
import '../../data/services/api_exception.dart';

/// Öğrenci tarafındaki deneme (ExamResult) akışını yönetir: listeleme,
/// oluşturma, güncelleme ve silme.
class ExamController extends ChangeNotifier {
  final ExamRepository _repository;

  ExamController({required this._repository});

  bool _isLoading = false;
  bool _isSubmitting = false;
  String? _errorMessage;
  ApiException? _lastError;

  bool get isLoading => _isLoading;
  bool get isSubmitting => _isSubmitting;
  String? get errorMessage => _errorMessage;
  ApiException? get lastError => _lastError;

  List<ExamModel> _exams = const [];
  List<SubjectModel> _subjects = const [];

  List<ExamModel> get exams => _exams;
  List<SubjectModel> get subjects => _subjects;

  Future<void> loadExams({int? studentId}) async {
    _setLoading(true, clearError: true);
    try {
      _exams = await _repository.getExams(studentId: studentId);
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
      _subjects = await _repository.getSubjects();
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> createExam({
    required DateTime examDate,
    required List<SubjectNetModel> subjectNets,
    ExamType examType = ExamType.none,
    String? name,
  }) async {
    _setSubmitting(true, clearError: true);
    try {
      final createdExam = await _repository.createExam(
        examDate: examDate,
        subjectNets: subjectNets,
        examType: examType,
        name: name,
      );
      _exams = [createdExam, ..._exams];
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
  }

  Future<bool> updateExam({
    required int examId,
    DateTime? examDate,
    ExamType? examType,
    String? name,
    List<SubjectNetModel>? subjectNets,
  }) async {
    _setSubmitting(true, clearError: true);
    try {
      final updatedExam = await _repository.updateExam(
        examId: examId,
        examDate: examDate,
        examType: examType,
        name: name,
        subjectNets: subjectNets,
      );
      _exams = _exams.map((exam) => exam.id == examId ? updatedExam : exam).toList();
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
  }

  Future<bool> deleteExam(int examId) async {
    _setSubmitting(true, clearError: true);
    try {
      await _repository.deleteExam(examId);
      _exams = _exams.where((exam) => exam.id != examId).toList();
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
    _exams = const [];
    _subjects = const [];
    _isLoading = false;
    _isSubmitting = false;
    _errorMessage = null;
    _lastError = null;
    notifyListeners();
  }
}
