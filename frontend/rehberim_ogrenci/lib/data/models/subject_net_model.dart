/// Bir denemede tek bir dersin sonucu.
///
/// Öğrenci **doğru** ([correct]) ve **yanlış** ([wrong]) sayısını girer; **boş**
/// ([blank]) ve **net** sunucuda türetilir ve salt-okunurdur:
/// `net = doğru - yanlış/4`, `boş = soru sayısı - doğru - yanlış`.
/// Bütün yanıtlar yanlışsa net doğal olarak negatif çıkar.
class SubjectNetModel {
  final int? id;
  final int? subject;
  final String? subjectLabel;
  final int correct;
  final int wrong;

  /// Sunucuda hesaplanır (`doğru - yanlış/4`); gönderilmez.
  final double net;

  /// Sunucuda hesaplanır; dersin soru sayısı bilinmiyorsa `null` gelir.
  final int? blank;

  /// Dersin sınavdaki soru sayısı (salt-okunur; doğru+yanlış üst sınırı).
  final int? questionCount;

  const SubjectNetModel({
    this.id,
    this.subject,
    this.subjectLabel,
    this.correct = 0,
    this.wrong = 0,
    this.net = 0,
    this.blank,
    this.questionCount,
  });

  factory SubjectNetModel.fromJson(Map<String, dynamic> json) {
    return SubjectNetModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      subject: json['subject'] is int ? json['subject'] as int : int.tryParse('${json['subject']}'),
      subjectLabel: json['subject_label']?.toString(),
      correct: _parseInt(json['correct']) ?? 0,
      wrong: _parseInt(json['wrong']) ?? 0,
      net: _parseDouble(json['net']) ?? 0,
      blank: _parseInt(json['blank']),
      questionCount: _parseInt(json['question_count']),
    );
  }

  /// Sunucuya gönderilecek gövde: `subject` + `correct` + `wrong`. `id`,
  /// `subject_label`, `net`, `blank` ve `question_count` salt-okunurdur;
  /// backend her kaydetmede netleri silip yeniden oluşturur.
  Map<String, dynamic> toJson() {
    return {
      'subject': subject,
      'correct': correct,
      'wrong': wrong,
    };
  }

  SubjectNetModel copyWith({
    int? subject,
    String? subjectLabel,
    int? correct,
    int? wrong,
  }) {
    return SubjectNetModel(
      id: id,
      subject: subject ?? this.subject,
      subjectLabel: subjectLabel ?? this.subjectLabel,
      correct: correct ?? this.correct,
      wrong: wrong ?? this.wrong,
      net: net,
      blank: blank,
      questionCount: questionCount,
    );
  }

  static double? _parseDouble(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString());
  }

  static int? _parseInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse(value.toString());
  }
}
