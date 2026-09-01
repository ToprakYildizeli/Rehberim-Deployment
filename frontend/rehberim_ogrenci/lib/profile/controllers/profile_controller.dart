import 'package:flutter/foundation.dart';
import '../../auth/controllers/auth_controller.dart';

/// Profil sayfasına özgü ekran durumunu (yenileme, danışmana bağlanma)
/// yönetir. Kullanıcı/oturum verisinin tek doğruluk kaynağı [AuthController]
/// olduğundan, bu controller onu sarmalayarak sayfaya özgü mantığı taşır.
class ProfileController extends ChangeNotifier {
  final AuthController authController;

  ProfileController({required this.authController});

  bool _isRefreshing = false;
  bool get isRefreshing => _isRefreshing;

  bool _isConnectingCounselor = false;
  bool get isConnectingCounselor => _isConnectingCounselor;

  String? _connectCounselorError;
  String? get connectCounselorError => _connectCounselorError;

  Future<void> refreshProfile() async {
    _isRefreshing = true;
    notifyListeners();
    await authController.refreshCurrentUser();
    _isRefreshing = false;
    notifyListeners();
  }

  /// Koç davet kodu ile bağlanmayı dener. Başarılı olursa `true` döner.
  Future<bool> connectCounselor(String code) async {
    _isConnectingCounselor = true;
    _connectCounselorError = null;
    notifyListeners();

    final success = await authController.connectCounselor(code);

    _isConnectingCounselor = false;
    if (!success) {
      _connectCounselorError = authController.errorMessage ?? 'Koça bağlanılamadı.';
    }
    notifyListeners();
    return success;
  }

  void clearConnectError() {
    _connectCounselorError = null;
    notifyListeners();
  }

  Future<void> logout() => authController.logout();
}
