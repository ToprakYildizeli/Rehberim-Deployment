import 'package:flutter/foundation.dart';
import '../../data/models/goal_model.dart';
import '../../data/models/subject_model.dart';
import '../../data/repositories/goal_repository.dart';
import '../../data/services/api_exception.dart';

/// Öğrenci tarafındaki hedef (Goal) akışını yönetir: listeleme, oluşturma,
/// güncelleme ve silme.
class GoalController extends ChangeNotifier {
  final GoalRepository _repository;

  GoalController({required this._repository});

  bool _isLoading = false;
  bool _isSubmitting = false;
  String? _errorMessage;
  ApiException? _lastError;

  bool get isLoading => _isLoading;
  bool get isSubmitting => _isSubmitting;
  String? get errorMessage => _errorMessage;
  ApiException? get lastError => _lastError;

  List<GoalModel> _goals = const [];
  List<SubjectModel> _subjects = const [];

  List<GoalModel> get goals => _goals;
  List<SubjectModel> get subjects => _subjects;

  Future<void> loadGoals() async {
    _setLoading(true, clearError: true);
    try {
      _goals = await _repository.getGoals();
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

  Future<bool> createGoal({
    required GoalType goalType,
    String? title,
    String? description,
    DateTime? targetDate,
    bool isAchieved = false,
    ExamScope examScope = ExamScope.none,
    int? subjectId,
    double? targetNet,
  }) async {
    _setSubmitting(true, clearError: true);
    try {
      final createdGoal = await _repository.createGoal(
        goalType: goalType,
        title: title,
        description: description,
        targetDate: targetDate,
        isAchieved: isAchieved,
        examScope: examScope,
        subjectId: subjectId,
        targetNet: targetNet,
      );
      _goals = [createdGoal, ..._goals];
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
  }

  Future<bool> updateGoal({
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
    _setSubmitting(true, clearError: true);
    try {
      final updatedGoal = await _repository.updateGoal(
        goalId: goalId,
        goalType: goalType,
        title: title,
        description: description,
        targetDate: targetDate,
        isAchieved: isAchieved,
        examScope: examScope,
        subjectId: subjectId,
        targetNet: targetNet,
      );
      _goals = _goals.map((goal) => goal.id == goalId ? updatedGoal : goal).toList();
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      return false;
    } finally {
      _setSubmitting(false);
    }
  }

  /// Hızlıca "ulaşıldı" durumunu değiştirmek için kısayol.
  Future<bool> toggleAchieved(GoalModel goal) {
    return updateGoal(goalId: goal.id!, isAchieved: !goal.isAchieved);
  }

  Future<bool> deleteGoal(int goalId) async {
    _setSubmitting(true, clearError: true);
    try {
      await _repository.deleteGoal(goalId);
      _goals = _goals.where((goal) => goal.id != goalId).toList();
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
    _goals = const [];
    _subjects = const [];
    _isLoading = false;
    _isSubmitting = false;
    _errorMessage = null;
    _lastError = null;
    notifyListeners();
  }
}
