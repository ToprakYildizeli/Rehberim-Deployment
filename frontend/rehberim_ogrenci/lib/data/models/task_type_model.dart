/// Görev metodunu (konu çalışması, deneme, tekrar vb.) temsil eder.
class TaskTypeModel {
  final int? id;
  final String? name;

  const TaskTypeModel({this.id, this.name});

  factory TaskTypeModel.fromJson(Map<String, dynamic> json) {
    return TaskTypeModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      name: json['name']?.toString() ?? json['label']?.toString(),
    );
  }

  String get displayName => name?.trim().isNotEmpty == true ? name! : '';
}
