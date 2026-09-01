/// Program açarken listelenen öğrenci özet bilgisini temsil eder.
class StudentSummaryModel {
  final int? id;
  final String? fullName;
  final String? grade;
  final String? gradeDisplay;
  final String? studyField;

  const StudentSummaryModel({
    this.id,
    this.fullName,
    this.grade,
    this.gradeDisplay,
    this.studyField,
  });

  factory StudentSummaryModel.fromJson(Map<String, dynamic> json) {
    return StudentSummaryModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      fullName: json['full_name']?.toString(),
      grade: json['grade']?.toString(),
      gradeDisplay: json['grade_display']?.toString(),
      studyField: json['study_field']?.toString(),
    );
  }
}
