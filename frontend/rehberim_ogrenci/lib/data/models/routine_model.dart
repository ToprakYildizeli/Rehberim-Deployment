/// Öğrencinin **rutini**: haftanın günlerine göre tutulan, tarihten bağımsız
/// bir çalışma planı.
///
/// Backend'de rutin ayrı bir model değil — bir öğrenciye bağlanmış ve
/// `auto_apply` açılmış `ProgramTemplate`'tir (bkz. `program-contract.md`,
/// "Rutin"). Uçlar: `/program-templates/`.
///
/// [autoApply] açıkken **rehber öğrenciye yeni bir hafta açtığında** rutindeki
/// görevler o haftaya kendiliğinden düşer. Haftayı öğrenci açamaz; bu yüzden
/// rutin hemen değil, sıradaki hafta açıldığında görünür.
class RoutineModel {
  final int? id;
  final String name;
  final String scheduleType;   // 'timed' | 'untimed'
  final bool autoApply;
  final List<RoutineTaskModel> tasks;

  const RoutineModel({
    this.id,
    this.name = '',
    this.scheduleType = 'timed',
    this.autoApply = false,
    this.tasks = const [],
  });

  factory RoutineModel.fromJson(Map<String, dynamic> json) {
    final rawTasks = json['tasks'];
    final parsed = <RoutineTaskModel>[];
    if (rawTasks is List) {
      for (final item in rawTasks) {
        if (item is Map) {
          parsed.add(RoutineTaskModel.fromJson(Map<String, dynamic>.from(item)));
        }
      }
    }
    return RoutineModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      name: json['name']?.toString() ?? '',
      scheduleType: json['schedule_type']?.toString() ?? 'timed',
      autoApply: json['auto_apply'] == true,
      tasks: parsed,
    );
  }

  /// Oluşturma/güncelleme gövdesi. `student` gönderilmez: sunucu oturum
  /// sahibini kullanır, gövdedeki değeri yok sayar.
  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'schedule_type': scheduleType,
      'auto_apply': autoApply,
      'tasks': tasks.map((t) => t.toJson()).toList(),
    };
  }

  RoutineModel copyWith({
    String? name,
    String? scheduleType,
    bool? autoApply,
    List<RoutineTaskModel>? tasks,
  }) {
    return RoutineModel(
      id: id,
      name: name ?? this.name,
      scheduleType: scheduleType ?? this.scheduleType,
      autoApply: autoApply ?? this.autoApply,
      tasks: tasks ?? this.tasks,
    );
  }

  /// Rutindeki toplam çalışma süresi (dakika).
  int get totalMinutes =>
      tasks.fold(0, (sum, t) => sum + (t.durationMinutes ?? 0));
}

/// Rutindeki tek çalışma bloğu. Normal görevden farkı: tarih yerine haftanın
/// günü ([weekday]) tutulur — 0 = Pazartesi … 6 = Pazar.
class RoutineTaskModel {
  final int? id;
  final int? subject;
  final String? subjectLabel;
  final int? taskType;
  final String? taskTypeName;
  final String title;
  final int weekday;
  final String? startTime;        // 'HH:mm:ss' | 'HH:mm'
  final int? durationMinutes;
  final int order;

  const RoutineTaskModel({
    this.id,
    this.subject,
    this.subjectLabel,
    this.taskType,
    this.taskTypeName,
    this.title = '',
    this.weekday = 0,
    this.startTime,
    this.durationMinutes,
    this.order = 0,
  });

  factory RoutineTaskModel.fromJson(Map<String, dynamic> json) {
    return RoutineTaskModel(
      id: _parseInt(json['id']),
      subject: _parseInt(json['subject']),
      subjectLabel: json['subject_label']?.toString(),
      taskType: _parseInt(json['task_type']),
      taskTypeName: json['task_type_name']?.toString(),
      title: json['title']?.toString() ?? '',
      weekday: _parseInt(json['weekday']) ?? 0,
      startTime: json['start_time']?.toString(),
      durationMinutes: _parseInt(json['duration_minutes']),
      order: _parseInt(json['order']) ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'subject': subject,
      'task_type': taskType,
      'title': title,
      'weekday': weekday,
      'start_time': startTime,
      'duration_minutes': durationMinutes,
      'order': order,
    };
  }

  RoutineTaskModel copyWith({
    int? subject,
    String? subjectLabel,
    int? taskType,
    String? taskTypeName,
    String? title,
    int? weekday,
    String? startTime,
    int? durationMinutes,
    int? order,
  }) {
    return RoutineTaskModel(
      id: id,
      subject: subject ?? this.subject,
      subjectLabel: subjectLabel ?? this.subjectLabel,
      taskType: taskType ?? this.taskType,
      taskTypeName: taskTypeName ?? this.taskTypeName,
      title: title ?? this.title,
      weekday: weekday ?? this.weekday,
      startTime: startTime ?? this.startTime,
      durationMinutes: durationMinutes ?? this.durationMinutes,
      order: order ?? this.order,
    );
  }

  /// Saati 'HH:mm' olarak gösterir; saatsiz rutinlerde boş döner.
  String get displayTime {
    final raw = startTime;
    if (raw == null || raw.length < 5) return '';
    return raw.substring(0, 5);
  }

  static int? _parseInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse(value.toString());
  }
}

/// 0 = Pazartesi … 6 = Pazar (backend `weekday` ile birebir).
const List<String> kWeekdayNames = [
  'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar',
];

String weekdayName(int weekday) =>
    (weekday >= 0 && weekday < kWeekdayNames.length) ? kWeekdayNames[weekday] : '';
