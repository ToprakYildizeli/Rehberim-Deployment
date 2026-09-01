import 'package:flutter_test/flutter_test.dart';
import 'package:rehberim_ogrenci/data/models/program_model.dart';
import 'package:rehberim_ogrenci/data/models/task_model.dart';

void main() {
  group('Weekly program models', () {
    test('ProgramModel parses nested tasks and schedule type', () {
      final program = ProgramModel.fromJson({
        'id': 1,
        'student': 4,
        'student_name': 'Ali Yılmaz',
        'counselor': 2,
        'start_date': '2026-07-15',
        'end_date': '2026-07-21',
        'schedule_type': 'timed',
        'note': 'Haftalık plan',
        'tasks': [
          {
            'id': 10,
            'program': 1,
            'subject': 6,
            'subject_label': 'TYT Matematik',
            'task_type': 3,
            'task_type_name': 'Konu Çalışması',
            'title': '20 soru',
            'description': '',
            'date': '2026-07-16',
            'start_time': '09:00:00',
            'duration_minutes': 60,
            'end_time': '10:00:00',
            'is_completed': false,
            'created_by': 5,
            'order': 0,
          }
        ],
        'created_at': '2026-07-15T10:00:00Z',
        'updated_at': '2026-07-15T10:00:00Z',
      });

      expect(program.id, 1);
      expect(program.scheduleType, ScheduleType.timed);
      expect(program.tasks.length, 1);
      expect(program.tasks.first.title, '20 soru');
      expect(program.tasks.first.isCompleted, isFalse);
    });

    test('TaskModel parses untimed payload with null time fields', () {
      final task = TaskModel.fromJson({
        'id': 11,
        'program': 1,
        'subject': 7,
        'subject_label': 'TYT Türkçe',
        'task_type': 2,
        'task_type_name': 'Okuma',
        'title': 'Metin çalış',
        'description': 'Ders çalış',
        'date': '2026-07-17',
        'start_time': null,
        'duration_minutes': null,
        'end_time': null,
        'is_completed': true,
        'created_by': 5,
        'order': 1,
      });

      expect(task.scheduleType, ScheduleType.untimed);
      expect(task.startTime, isNull);
      expect(task.durationMinutes, isNull);
      expect(task.isCompleted, isTrue);
    });
  });
}
