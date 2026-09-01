/// Rehberin takvimindeki bir etkinliği temsil eder (bkz. `CalendarEvent`).
///
/// Öğrenci uçtan yalnızca kendisine bağlı etkinlikleri okuyabilir
/// (GET `/calendar/`, GET `/calendar/{id}/`); oluşturma/düzenleme/silme
/// rehbere özeldir, bu yüzden bu model salt-okunur amaçlıdır.
/// `isAllDay` — saat girilmemişse tüm gün süren etkinlik (ör. "Özdebir TYT
/// 16 Temmuz") anlamına gelir; backend'de salt-okunur hesaplanmış alandır.
class CalendarEventModel {
  final int? id;
  final int? counselor;
  final int? student;
  final String? studentName;
  final String? title;
  final String? description;
  final DateTime? date;
  final String? startTime;
  final String? endTime;
  final bool isAllDay;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const CalendarEventModel({
    this.id,
    this.counselor,
    this.student,
    this.studentName,
    this.title,
    this.description,
    this.date,
    this.startTime,
    this.endTime,
    this.isAllDay = true,
    this.createdAt,
    this.updatedAt,
  });

  factory CalendarEventModel.fromJson(Map<String, dynamic> json) {
    return CalendarEventModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      counselor: json['counselor'] is int
          ? json['counselor'] as int
          : int.tryParse('${json['counselor']}'),
      student: json['student'] is int ? json['student'] as int : int.tryParse('${json['student']}'),
      studentName: json['student_name']?.toString(),
      title: json['title']?.toString(),
      description: json['description']?.toString(),
      date: _parseDate(json['date']),
      startTime: json['start_time']?.toString(),
      endTime: json['end_time']?.toString(),
      isAllDay: json['is_all_day'] == true,
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
      updatedAt: DateTime.tryParse(json['updated_at']?.toString() ?? ''),
    );
  }

  static DateTime? _parseDate(dynamic value) {
    if (value == null) return null;
    return DateTime.tryParse(value.toString());
  }
}
