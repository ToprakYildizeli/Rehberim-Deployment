import 'package:flutter/foundation.dart';
import '../../data/models/user_model.dart';
import '../../data/repositories/auth_repository.dart';
import '../../data/services/api_exception.dart';
import '../../data/services/token_storage_service.dart';

enum AuthStatus { unknown, authenticating, authenticated, unauthenticated }

/// Uygulamanın kimlik doğrulama durumunu ve giriş yapmış kullanıcı
/// bilgisini yöneten merkezi controller.
///
/// - Uygulama açılışında [checkInitialAuthStatus] ile mevcut oturum kontrol edilir.
/// - Login/Register/Logout akışları burada yönetilir.
/// - Profil sayfası, danışmana bağlanma işlemini de bu controller üzerinden yapar.
class AuthController extends ChangeNotifier {
  final AuthRepository _authRepository;
  final TokenStorageService _tokenStorage;

  AuthController({
    required this._authRepository,
    required this._tokenStorage,
  });

  AuthStatus _status = AuthStatus.unknown;
  UserModel? _currentUser;
  bool _isSubmitting = false;
  String? _errorMessage;
  ApiException? _lastError;

  AuthStatus get status => _status;
  UserModel? get currentUser => _currentUser;
  bool get isSubmitting => _isSubmitting;
  String? get errorMessage => _errorMessage;
  ApiException? get lastError => _lastError;
  bool get isAuthenticated => _status == AuthStatus.authenticated;

  /// Uygulama açılışında çağrılır: kayıtlı bir token varsa profil bilgisini
  /// çekmeyi dener; başarısız olursa oturumu kapatılmış sayar.
  Future<void> checkInitialAuthStatus() async {
    final hasTokens = await _tokenStorage.hasTokens();
    if (!hasTokens) {
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }

    try {
      final user = await _authRepository.getMe();
      _currentUser = user;
      _status = AuthStatus.authenticated;
    } catch (_) {
      await _tokenStorage.clear();
      _status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  /// [ApiClient.onSessionExpired] tarafından tetiklenir: refresh token da
  /// geçersiz olduğunda kullanıcıyı zorla çıkışa yönlendirir.
  void handleSessionExpired() {
    _currentUser = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }

  Future<bool> login({required String username, required String password}) async {
    _setSubmitting(true, clearError: true);
    try {
      final authResponse = await _authRepository.login(username: username, password: password);
      _currentUser = authResponse.user;
      _status = AuthStatus.authenticated;
      _setSubmitting(false);
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      _setSubmitting(false);
      return false;
    }
  }

  /// Öğrenci kaydı yapar ve ardından aynı bilgilerle otomatik giriş dener.
  ///
  /// Register endpoint'i token döndürmediği için, kayıt başarılı olduktan
  /// hemen sonra [login] çağrılarak kullanıcı deneyimi kesintisiz sürdürülür.
  Future<bool> registerStudent({
    required String username,
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String grade,
    String? studyField,
    String? counselorCode,
  }) async {
    _setSubmitting(true, clearError: true);
    try {
      await _authRepository.registerStudent(
        username: username,
        email: email,
        password: password,
        firstName: firstName,
        lastName: lastName,
        grade: grade,
        studyField: studyField,
        counselorCode: counselorCode,
      );

      // Kayıt sonrası otomatik giriş.
      final authResponse = await _authRepository.login(username: username, password: password);
      _currentUser = authResponse.user;
      _status = AuthStatus.authenticated;
      _setSubmitting(false);
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      _setSubmitting(false);
      return false;
    }
  }

  Future<void> logout() async {
    _setSubmitting(true, clearError: true);
    await _authRepository.logout();
    _currentUser = null;
    _status = AuthStatus.unauthenticated;
    _setSubmitting(false);
  }

  /// Kullanıcı profilini sunucudan tazeler (ör. profil sayfasında pull-to-refresh).
  Future<void> refreshCurrentUser() async {
    try {
      final user = await _authRepository.getMe();
      _currentUser = user;
      notifyListeners();
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      notifyListeners();
    }
  }

  /// Davet kodu ile danışmana bağlanır ve kullanıcı bilgisini günceller.
  Future<bool> connectCounselor(String counselorCode) async {
    _setSubmitting(true, clearError: true);
    try {
      final updatedUser = await _authRepository.connectCounselor(counselorCode);
      _currentUser = updatedUser;
      _setSubmitting(false);
      return true;
    } on ApiException catch (e) {
      _lastError = e;
      _errorMessage = e.message;
      _setSubmitting(false);
      return false;
    }
  }

  void clearError() {
    _errorMessage = null;
    _lastError = null;
    notifyListeners();
  }

  void _setSubmitting(bool value, {bool clearError = false}) {
    _isSubmitting = value;
    if (clearError) {
      _errorMessage = null;
      _lastError = null;
    }
    notifyListeners();
  }
}
