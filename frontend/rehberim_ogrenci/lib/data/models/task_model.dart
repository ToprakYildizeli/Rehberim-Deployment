import 'program_model.dart';

/// Haftalık program içindeki tek bir görevi temsil eder.
class TaskModel {
  final int? id;
  final int? program;
  final int? subject;
  final String? subjectLabel;
  final int? taskType;
  final String? taskTypeName;
  final String title;
  final String? description;
  final DateTime? date;
  final String? startTime;
  final int? durationMinutes;
  final String? endTime;
  final bool isCompleted;
  final int? createdBy;
  final int order;
  final ScheduleType scheduleType;

  const TaskModel({
    this.id,
    this.program,
    this.subject,
    this.subjectLabel,
    this.taskType,
    this.taskTypeName,
    required this.title,
    this.description,
    this.date,
    this.startTime,
    this.durationMinutes,
    this.endTime,
    this.isCompleted = false,
    this.createdBy,
    this.order = 0,
    this.scheduleType = ScheduleType.untimed,
  });

  factory TaskModel.fromJson(Map<String, dynamic> json, {ScheduleType? scheduleType}) {
    final resolvedScheduleType = scheduleType ?? _inferScheduleType(json);

    return TaskModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      program: json['program'] is int ? json['program'] as int : int.tryParse('${json['program']}'),
      subject: json['subject'] is int ? json['subject'] as int : int.tryParse('${json['subject']}'),
      subjectLabel: json['subject_label']?.toString(),
      taskType: json['task_type'] is int ? json['task_type'] as int : int.tryParse('${json['task_type']}'),
      taskTypeName: json['task_type_name']?.toString(),
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString(),
      date: _parseDate(json['date']),
      startTime: json['start_time']?.toString(),
      durationMinutes: json['duration_minutes'] is int
          ? json['duration_minutes'] as int
          : int.tryParse('${json['duration_minutes']}'),
      endTime: json['end_time']?.toString(),
      isCompleted: json['is_completed'] == true,
      createdBy: json['created_by'] is int ? json['created_by'] as int : int.tryParse('${json['created_by']}'),
      order: json['order'] is int ? json['order'] as int : int.tryParse('${json['order']}') ?? 0,
      scheduleType: resolvedScheduleType,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'program': program,
      'subject': subject,
      'subject_label': subjectLabel,
      'task_type': taskType,
      'task_type_name': taskTypeName,
      'title': title,
      'description': description,
      'date': _formatDate(date),
      'start_time': startTime,
      'duration_minutes': durationMinutes,
      'end_time': endTime,
      'is_completed': isCompleted,
      'created_by': createdBy,
      'order': order,
    };
  }

  static ScheduleType _inferScheduleType(Map<String, dynamic> json) {
    final hasStartTime = json['start_time'] != null && '${json['start_time']}'.isNotEmpty;
    final hasDuration = json['duration_minutes'] != null && '${json['duration_minutes']}'.isNotEmpty;
    return (hasStartTime || hasDuration) ? ScheduleType.timed : ScheduleType.untimed;
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

/// Aynı güne ait görevlerin gösterim sırasını belirler.
///
/// Saatli programlarda görevler başlangıç saatine göre sıralanır (saat
/// bilgisi olmayanlar sona düşer); saatsiz programlarda kullanıcının manuel
/// olarak belirlediği `order` alanı kullanılır. Ev ve haftalık takvim
/// görünümleri aynı sıralamayı paylaşır.
int compareTasksForDisplay(TaskModel a, TaskModel b, ScheduleType scheduleType) {
  if (scheduleType == ScheduleType.timed) {
    final aTime = a.startTime;
    final bTime = b.startTime;
    if (aTime == null && bTime != null) return 1;
    if (aTime != null && bTime == null) return -1;
    if (aTime != null && bTime != null) {
      final timeCompare = aTime.compareTo(bTime);
      if (timeCompare != 0) return timeCompare;
    }
  }
  return a.order.compareTo(b.order);
}
