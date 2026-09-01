import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../common/constants/app_constants.dart';

/// JWT `access` / `refresh` token'larının cihazda güvenli şekilde
/// saklanmasından sorumludur.
///
/// **Okuma hataları yutulur.** Depolama çözülemediğinde (web'de WebCrypto
/// `OperationError`'ı: şifreleme anahtarı ile kayıtlı veri uyuşmazsa okuma
/// patlar; mobilde keystore sıfırlanması benzer sonucu verir) bu hata tüm
/// uygulamayı düşürürdü: açılışta `hasTokens()` fırlatınca ekran boş kalıyor,
/// istek araya girerken fırlatınca istek `Authorization` başlığı olmadan
/// gidiyordu. Böyle bir durumda tek doğru davranış **oturumu yok saymaktır** —
/// bozuk kayıt silinir, kullanıcı giriş ekranına düşer.
class TokenStorageService {
  final FlutterSecureStorage _storage;

  TokenStorageService({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  Future<void> saveTokens({required String access, required String refresh}) async {
    await Future.wait([
      _storage.write(key: AppConstants.accessTokenKey, value: access),
      _storage.write(key: AppConstants.refreshTokenKey, value: refresh),
    ]);
  }

  Future<void> saveAccessToken(String access) async {
    await _storage.write(key: AppConstants.accessTokenKey, value: access);
  }

  Future<String?> getAccessToken() => _readOrDiscard(AppConstants.accessTokenKey);

  Future<String?> getRefreshToken() => _readOrDiscard(AppConstants.refreshTokenKey);

  /// Okur; çözülemezse bozuk kaydı temizleyip `null` döner.
  Future<String?> _readOrDiscard(String key) async {
    try {
      return await _storage.read(key: key);
    } catch (e) {
      debugPrint('TokenStorage: "$key" okunamadı ($e) — kayıt siliniyor, oturum kapalı sayılıyor.');
      try {
        await _storage.delete(key: key);
      } catch (_) {
        // Silme de başarısızsa yapacak bir şey yok; null dönmek yeterli.
      }
      return null;
    }
  }

  Future<void> clear() async {
    await Future.wait([
      _deleteQuietly(AppConstants.accessTokenKey),
      _deleteQuietly(AppConstants.refreshTokenKey),
    ]);
  }

  Future<void> _deleteQuietly(String key) async {
    try {
      await _storage.delete(key: key);
    } catch (e) {
      debugPrint('TokenStorage: "$key" silinemedi ($e).');
    }
  }

  Future<bool> hasTokens() async {
    final access = await getAccessToken();
    return access != null && access.isNotEmpty;
  }
}
