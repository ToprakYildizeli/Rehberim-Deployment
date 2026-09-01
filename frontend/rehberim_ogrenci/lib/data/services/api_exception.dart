/// API çağrılarından fırlatılan, kullanıcıya gösterilebilir hata mesajı
/// taşıyan özel exception sınıfı.
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  /// Sunucudan gelen alan bazlı hatalar (ör. {"username": ["Bu kullanıcı adı kullanılıyor"]})
  final Map<String, List<String>>? fieldErrors;

  /// Bağlantı hatası (internet yok / sunucuya ulaşılamadı) olup olmadığı.
  final bool isNetworkError;

  const ApiException(
    this.message, {
    this.statusCode,
    this.fieldErrors,
    this.isNetworkError = false,
  });

  /// Belirli bir alana ait ilk hata mesajını döner (ör. formda alan altına basmak için).
  String? errorFor(String field) {
    final errors = fieldErrors?[field];
    if (errors == null || errors.isEmpty) return null;
    return errors.first;
  }

  @override
  String toString() => message;
}
