import 'task_model.dart';

enum ScheduleType { timed, untimed }

extension ScheduleTypeX on ScheduleType {
  String get apiValue => switch (this) {
        ScheduleType.timed => 'timed',
        ScheduleType.untimed => 'untimed',
      };

  static ScheduleType fromValue(String? value) {
    switch (value?.toLowerCase()) {
      case 'timed':
        return ScheduleType.timed;
      case 'untimed':
        return ScheduleType.untimed;
      default:
        return ScheduleType.untimed;
    }
  }
}

/// Öğrencinin haftalık programını temsil eder.
class ProgramModel {
  final int? id;
  final int? student;
  final String? studentName;
  final int? counselor;
  final DateTime? startDate;
  final DateTime? endDate;
  final ScheduleType scheduleType;
  final String? note;
  final List<TaskModel> tasks;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const ProgramModel({
    this.id,
    this.student,
    this.studentName,
    this.counselor,
    this.startDate,
    this.endDate,
    required this.scheduleType,
    this.note,
    this.tasks = const [],
    this.createdAt,
    this.updatedAt,
  });

  factory ProgramModel.fromJson(Map<String, dynamic> json) {
    final rawScheduleType = json['schedule_type']?.toString();
    final parsedTasks = <TaskModel>[];
    final tasksJson = json['tasks'];
    if (tasksJson is List) {
      for (final item in tasksJson) {
        if (item is Map) {
          parsedTasks.add(TaskModel.fromJson(
            Map<String, dynamic>.from(item),
            scheduleType: ScheduleTypeX.fromValue(rawScheduleType),
          ));
        }
      }
    }

    return ProgramModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      student: json['student'] is int ? json['student'] as int : int.tryParse('${json['student']}'),
      studentName: json['student_name']?.toString(),
      counselor: json['counselor'] is int ? json['counselor'] as int : int.tryParse('${json['counselor']}'),
      startDate: _parseDate(json['start_date']),
      endDate: _parseDate(json['end_date']),
      scheduleType: ScheduleTypeX.fromValue(rawScheduleType),
      note: json['note']?.toString(),
      tasks: parsedTasks,
      createdAt: _parseDateTime(json['created_at']),
      updatedAt: _parseDateTime(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'student': student,
      'student_name': studentName,
      'counselor': counselor,
      'start_date': _formatDate(startDate),
      'end_date': _formatDate(endDate),
      'schedule_type': scheduleType.apiValue,
      'note': note,
      'tasks': tasks.map((task) => task.toJson()).toList(),
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  static DateTime? _parseDate(dynamic value) {
    if (value == null) return null;
    return DateTime.tryParse(value.toString());
  }

  static DateTime? _parseDateTime(dynamic value) {
    if (value == null) return null;
    return DateTime.tryParse(value.toString());
  }

  static String? _formatDate(DateTime? value) {
    if (value == null) return null;
    return '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
  }
}
