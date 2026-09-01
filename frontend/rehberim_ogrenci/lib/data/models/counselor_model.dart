/// Öğrenciye bağlı danışman (counselor) bilgisini temsil eder.
class CounselorModel {
  final int? id;
  final String name;

  const CounselorModel({
    this.id,
    required this.name,
  });

  factory CounselorModel.fromJson(Map<String, dynamic> json) {
    return CounselorModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      name: json['name']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
    };
  }
}
