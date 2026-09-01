/// Hedefin türü. Backend'de `goal_type` (bkz. `Goal.GoalType`).
///
/// `deneme_net` dışındaki türler henüz konu/kitap referanslarına bağlı değil;
/// bu yüzden şimdilik serbest metin `title` ile tutulur.
enum GoalType { denemeNeti, konu, kitapBitirme, kitapOkuma }

extension GoalTypeX on GoalType {
  String get apiValue => switch (this) {
        GoalType.denemeNeti => 'deneme_net',
        GoalType.konu => 'konu',
        GoalType.kitapBitirme => 'kitap_bitirme',
        GoalType.kitapOkuma => 'kitap_okuma',
      };

  String get label => switch (this) {
        GoalType.denemeNeti => 'Deneme Neti',
        GoalType.konu => 'Konu Bitirme',
        GoalType.kitapBitirme => 'Kitap Bitirme',
        GoalType.kitapOkuma => 'Kitap Okuma', 
      };

  static GoalType fromValue(String? value) {
    switch (value) {
      case 'konu':
        return GoalType.konu;
      case 'kitap_bitirme':
        return GoalType.kitapBitirme;
      case 'kitap_okuma':
        return GoalType.kitapOkuma;
      default:
        return GoalType.denemeNeti;
    }
  }
}

/// Deneme neti hedefinde sınav türü. Backend'de `exam_scope` (bkz.
/// `Goal.ExamScope`). Deneme dışı hedeflerde boş bırakılır.
enum ExamScope { tyt, ayt, none }

extension ExamScopeX on ExamScope {
  String get apiValue => switch (this) {
        ExamScope.tyt => 'tyt',
        ExamScope.ayt => 'ayt',
        ExamScope.none => '',
      };

  String get label => switch (this) {
        ExamScope.tyt => 'TYT',
        ExamScope.ayt => 'AYT',
        ExamScope.none => '',
      };

  static ExamScope fromValue(String? value) {
    switch (value?.toLowerCase()) {
      case 'tyt':
        return ExamScope.tyt;
      case 'ayt':
        return ExamScope.ayt;
      default:
        return ExamScope.none;
    }
  }
}

/// Öğrencinin kendine koyduğu hedefi temsil eder.
///
/// `student` sunucuda oturum sahibi öğrenciye göre atanır (salt-okunur alan);
/// oluşturma/güncellemede gönderilmesine gerek yoktur ve backend zaten yok
/// sayar. `label`, backend'in ürettiği gösterim metnidir (ör. "AYT Matematik
/// 25 net").
class GoalModel {
  final int? id;
  final int? student;
  final String? studentName;
  final GoalType goalType;
  final String? title;
  final String? label;
  final String? description;
  final DateTime? targetDate;
  final bool isAchieved;
  final ExamScope examScope;
  final int? subjectId;
  final String? subjectLabel;
  final double? targetNet;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const GoalModel({
    this.id,
    this.student,
    this.studentName,
    this.goalType = GoalType.denemeNeti,
    this.title,
    this.label,
    this.description,
    this.targetDate,
    this.isAchieved = false,
    this.examScope = ExamScope.none,
    this.subjectId,
    this.subjectLabel,
    this.targetNet,
    this.createdAt,
    this.updatedAt,
  });

  factory GoalModel.fromJson(Map<String, dynamic> json) {
    return GoalModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      student: json['student'] is int ? json['student'] as int : int.tryParse('${json['student']}'),
      studentName: json['student_name']?.toString(),
      goalType: GoalTypeX.fromValue(json['goal_type']?.toString()),
      title: json['title']?.toString(),
      label: json['label']?.toString(),
      description: json['description']?.toString(),
      targetDate: _parseDate(json['target_date']),
      isAchieved: json['is_achieved'] == true,
      examScope: ExamScopeX.fromValue(json['exam_scope']?.toString()),
      subjectId: json['subject'] is int ? json['subject'] as int : int.tryParse('${json['subject']}'),
      subjectLabel: json['subject_label']?.toString(),
      targetNet: _parseDouble(json['target_net']),
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
      updatedAt: DateTime.tryParse(json['updated_at']?.toString() ?? ''),
    );
  }

  /// Oluşturma/güncelleme gövdesi. `student`, `label`, `subject_label` ve
  /// zaman damgaları sunucu tarafından atanır, buradan gönderilmez.
  Map<String, dynamic> toJson() {
    final payload = <String, dynamic>{
      'goal_type': goalType.apiValue,
      'title': title ?? '',
      'description': description ?? '',
      'target_date': _formatDate(targetDate),
      'is_achieved': isAchieved,
    };
    if (goalType == GoalType.denemeNeti) {
      payload['exam_scope'] = examScope.apiValue;
      payload['target_net'] = targetNet;
      payload['subject'] = subjectId;
    }
    return payload;
  }

  static double? _parseDouble(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString());
  }

  static DateTime? _parseDate(dynamic value) {
    if (value == null) return null;
    return DateTime.tryParse(value.toString());
  }

  static String? _formatDate(DateTime? value) {
    if (value == null) return null;
    return '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
  }
}
