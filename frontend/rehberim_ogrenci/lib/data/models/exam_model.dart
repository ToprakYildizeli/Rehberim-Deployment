import 'subject_net_model.dart';

/// Denemenin türü (TYT/AYT). Backend'de `exam_type` boş bırakılabilir.
enum ExamType { tyt, ayt, none }

extension ExamTypeX on ExamType {
  String get apiValue => switch (this) {
        ExamType.tyt => 'tyt',
        ExamType.ayt => 'ayt',
        ExamType.none => '',
      };

  String get label => switch (this) {
        ExamType.tyt => 'TYT',
        ExamType.ayt => 'AYT',
        ExamType.none => 'Genel',
      };

  static ExamType fromValue(String? value) {
    switch (value?.toLowerCase()) {
      case 'tyt':
        return ExamType.tyt;
      case 'ayt':
        return ExamType.ayt;
      default:
        return ExamType.none;
    }
  }
}

/// Öğrencinin bir deneme sonucunu (ders bazlı netleriyle birlikte) temsil eder.
class ExamModel {
  final int? id;
  final int? student;
  final String? studentName;
  final ExamType examType;
  final String? name;
  final DateTime? examDate;
  final double totalNet;
  final List<SubjectNetModel> subjectNets;

  const ExamModel({
    this.id,
    this.student,
    this.studentName,
    this.examType = ExamType.none,
    this.name,
    this.examDate,
    this.totalNet = 0,
    this.subjectNets = const [],
  });

  factory ExamModel.fromJson(Map<String, dynamic> json) {
    final netsJson = json['subject_nets'];
    final parsedNets = <SubjectNetModel>[];
    if (netsJson is List) {
      for (final item in netsJson) {
        if (item is Map) {
          parsedNets.add(SubjectNetModel.fromJson(Map<String, dynamic>.from(item)));
        }
      }
    }

    return ExamModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      student: json['student'] is int ? json['student'] as int : int.tryParse('${json['student']}'),
      studentName: json['student_name']?.toString(),
      examType: ExamTypeX.fromValue(json['exam_type']?.toString()),
      name: json['name']?.toString(),
      examDate: _parseDate(json['exam_date']),
      totalNet: _parseDouble(json['total_net']) ?? 0,
      subjectNets: parsedNets,
    );
  }

  /// Oluşturma/güncelleme gövdesi. `student` ve `total_net` sunucu tarafından
  /// atanır, buradan gönderilmez.
  Map<String, dynamic> toJson() {
    return {
      'exam_type': examType.apiValue,
      'name': name,
      'exam_date': _formatDate(examDate),
      'subject_nets': subjectNets.map((net) => net.toJson()).toList(),
    };
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
