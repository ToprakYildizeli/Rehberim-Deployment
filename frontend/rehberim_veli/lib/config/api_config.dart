import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform;

/// Backend (Django) bağlantı ayarları.
///
/// Kontrat: Rehberim-Backend/docs/auth-contract.md
/// Base URL (dev): http://127.0.0.1:8000/api/
///
/// Platform notu: Android emülatörü ana makinenin `127.0.0.1`'ine ulaşamaz;
/// host loopback için `10.0.2.2` kullanılır. iOS simülatörü, masaüstü ve web
/// doğrudan `127.0.0.1` kullanır.
///
/// Override: derlerken `--dart-define=API_BASE_URL=https://...` vererek
/// (örn. gerçek cihaz veya prod) bu değerleri geçersiz kılabilirsiniz.
class ApiConfig {
  static const String _override = String.fromEnvironment('API_BASE_URL');

  /// API kök adresi, örn. `http://127.0.0.1:8000/api`
  static String get baseUrl {
    if (_override.isNotEmpty) return _override;
    return '$_host/api';
  }

  static String get _host {
    if (kIsWeb) return 'http://127.0.0.1:8000';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000'; // Android emülatör → host makine
    }
    return 'http://127.0.0.1:8000'; // iOS sim / macOS / Windows / Linux
  }
}
