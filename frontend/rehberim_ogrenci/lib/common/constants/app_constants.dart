/// Uygulama genelinde kullanılan sabit değerler.
abstract class AppConstants {
  AppConstants._();

  static const String appName = 'Sınav Mentor';

  // .env içindeki anahtarlar
  static const String envApiBaseUrl = 'API_BASE_URL';

  // Secure storage anahtarları
  static const String accessTokenKey = 'ACCESS_TOKEN';
  static const String refreshTokenKey = 'REFRESH_TOKEN';

  // Sayfalar arası standart boşluklar
  static const double screenPadding = 20;
  static const double sectionSpacing = 24;
}

/// Öğrencinin bulunduğu sınıf seviyeleri.
/// Backend ile birebir aynı string değerleri kullanır.
class GradeOption {
  final String value;
  final String label;

  const GradeOption(this.value, this.label);

  static const List<GradeOption> all = [
    GradeOption('9', '9. Sınıf'),
    GradeOption('10', '10. Sınıf'),
    GradeOption('11', '11. Sınıf'),
    GradeOption('12', '12. Sınıf'),
    GradeOption('mezun', 'Mezun'),
  ];

  /// 11, 12 ve mezun için alan seçimi zorunludur.
  static bool requiresStudyField(String grade) {
    return grade == '11' || grade == '12' || grade == 'mezun';
  }

  static String labelOf(String value) {
    return all.firstWhere(
      (e) => e.value == value,
      orElse: () => GradeOption(value, value),
    ).label;
  }
}

/// Öğrencinin çalışma alanı (bölüm).
class StudyFieldOption {
  final String value;
  final String label;

  const StudyFieldOption(this.value, this.label);

  static const List<StudyFieldOption> all = [
    StudyFieldOption('say', 'Sayısal'),
    StudyFieldOption('ea', 'Eşit Ağırlık'),
    StudyFieldOption('soz', 'Sözel'),
  ];

  static String labelOf(String? value) {
    if (value == null) return '-';
    return all.firstWhere(
      (e) => e.value == value,
      orElse: () => StudyFieldOption(value, value),
    ).label;
  }
}
