import 'package:dio/dio.dart';
import '../models/auth_response_model.dart';
import '../models/user_model.dart';
import '../services/api_client.dart';
import '../services/token_storage_service.dart';

/// Kimlik doğrulama ve kullanıcı profili ile ilgili tüm API çağrılarını
/// tek bir noktadan yönetir.
class AuthRepository {
  final ApiClient _apiClient;
  final TokenStorageService _tokenStorage;

  AuthRepository({required this._apiClient, required this._tokenStorage});

  /// Öğrenci olarak kayıt olur.
  Future<void> registerStudent({
    required String username,
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String grade,
    String? studyField,
    String? counselorCode,
  }) async {
    try {
      final Map<String, dynamic> payload = {
        'username': username,
        'email': email,
        'password': password,
        'first_name': firstName,
        'last_name': lastName,
        'grade': grade,
      };

      if (studyField != null && studyField.isNotEmpty) {
        payload['study_field'] = studyField;
      }
      if (counselorCode != null && counselorCode.trim().isNotEmpty) {
        payload['counselor_code'] = counselorCode.trim();
      }

      await _apiClient.dio.post(
        '/auth/register/student/',
        data: payload,
        options: Options(extra: {'skipAuth': true}),
      );
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  /// Kullanıcı adı ve şifre ile giriş yapar, token'ları güvenli depoya kaydeder.
  Future<AuthResponseModel> login({required String username, required String password}) async {
    try {
      final response = await _apiClient.dio.post(
        '/auth/login/',
        data: {'username': username, 'password': password},
        options: Options(extra: {'skipAuth': true}),
      );

      final authResponse = AuthResponseModel.fromJson(Map<String, dynamic>.from(response.data));
      await _tokenStorage.saveTokens(access: authResponse.access, refresh: authResponse.refresh);
      return authResponse;
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  /// Mevcut oturumu sonlandırır: refresh token'ı sunucuda blacklist'e alır
  /// ve yerel token'ları temizler.
  Future<void> logout() async {
    final refreshToken = await _tokenStorage.getRefreshToken();
    try {
      if (refreshToken != null && refreshToken.isNotEmpty) {
        await _apiClient.dio.post('/auth/logout/', data: {'refresh': refreshToken});
      }
    } catch (_) {
      // Sunucu tarafı loglanamasa bile yerel oturumu kapatmaya devam ediyoruz.
    } finally {
      await _tokenStorage.clear();
    }
  }

  /// Giriş yapmış kullanıcının profil bilgilerini getirir
  /// (sınıf, alan ve varsa bağlı danışman dahil).
  Future<UserModel> getMe() async {
    try {
      final response = await _apiClient.dio.get('/auth/me/');
      return UserModel.fromJson(Map<String, dynamic>.from(response.data));
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }

  /// Koç davet kodu ile mevcut öğrenciyi bir danışmana bağlar.
  Future<UserModel> connectCounselor(String counselorCode) async {
    try {
      final response = await _apiClient.dio.post(
        '/students/connect-counselor/',
        data: {'code': counselorCode.trim()},
      );
      // Backend güncel kullanıcıyı döndürmezse, /auth/me/ ile tazeliyoruz.
      if (response.data is Map && (response.data as Map).containsKey('username')) {
        return UserModel.fromJson(Map<String, dynamic>.from(response.data));
      }
      return await getMe();
    } catch (e) {
      throw _apiClient.mapError(e);
    }
  }
}
