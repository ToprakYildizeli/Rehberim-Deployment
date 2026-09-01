/// Ders/konu referans bilgisini temsil eder.
///
/// `category` backend'de 'tyt' / 'ayt' / 'okul' değerlerinden birini alır
/// (bkz. `Subject.Category`); TYT/AYT netleri için ders listesini filtrelemek
/// amacıyla kullanılır. `label`, kategori önekiyle birlikte gösterim metnidir
/// (ör. "TYT Matematik"). `questionCount` dersin sınavdaki soru sayısıdır —
/// doğru+yanlış bu değeri aşamaz, boş = soru sayısı - doğru - yanlış. Okul
/// dersleri sınav dersi olmadığından 0'dır (sınır uygulanmaz).
class SubjectModel {
  final int? id;
  final String? name;
  final String? category;
  final String? label;
  final int questionCount;

  const SubjectModel({
    this.id,
    this.name,
    this.category,
    this.label,
    this.questionCount = 0,
  });

  factory SubjectModel.fromJson(Map<String, dynamic> json) {
    return SubjectModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      name: json['name']?.toString(),
      category: json['category']?.toString(),
      label: json['label']?.toString(),
      questionCount: _parseInt(json['question_count']) ?? 0,
    );
  }

  static int? _parseInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse(value.toString());
  }

  String get displayName {
    if (label?.trim().isNotEmpty == true) return label!;
    return name?.trim().isNotEmpty == true ? name! : '';
  }
}
