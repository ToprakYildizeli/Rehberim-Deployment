import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../../common/constants/app_constants.dart';
import 'api_exception.dart';
import 'token_storage_service.dart';

/// Uygulamanın tüm HTTP isteklerinin geçtiği tek Dio örneğini sarmalar.
///
/// Sorumlulukları:
/// - Her isteğe (gerekliyse) `Authorization: Bearer <access>` header'ı ekler.
/// - 401 (Unauthorized) alındığında `refresh` token ile yeni bir `access`
///   token'ı almayı dener ve orijinal isteği bir kez tekrar eder.
/// - Refresh de başarısız olursa, kayıtlı token'ları temizler ve
///   [onSessionExpired] callback'ini tetikleyerek üst katmanın (AuthController)
///   kullanıcıyı giriş ekranına yönlendirmesini sağlar.
class ApiClient {
  late final Dio dio;
  final TokenStorageService tokenStorage;

  /// Refresh token da geçersiz olduğunda çağrılır (oturum sonlandırma).
  void Function()? onSessionExpired;

  bool _isRefreshing = false;
  final List<void Function()> _pendingRetries = [];

  ApiClient({required this.tokenStorage}) {
    final baseUrl = dotenv.env[AppConstants.envApiBaseUrl] ?? 'http://127.0.0.1:8000/api/';

    dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        contentType: 'application/json',
        headers: {'Accept': 'application/json'},
      ),
    );

    dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          if (!options.extra.containsKey('skipAuth')) {
            final token = await tokenStorage.getAccessToken();
            if (token != null && token.isNotEmpty) {
              options.headers['Authorization'] = 'Bearer $token';
            }
          }
          handler.next(options);
        },
        onError: (DioException error, handler) async {
          final isAuthEndpoint = error.requestOptions.path.contains('/auth/login') ||
              error.requestOptions.path.contains('/auth/register') ||
              error.requestOptions.path.contains('/auth/refresh');

          if (error.response?.statusCode == 401 && !isAuthEndpoint) {
            try {
              final retryResponse = await _handleUnauthorized(error.requestOptions);
              return handler.resolve(retryResponse);
            } catch (_) {
              // Refresh başarısız oldu, orijinal hatayı ilet.
            }
          }
          handler.next(error);
        },
      ),
    );
  }

  Future<Response> _handleUnauthorized(RequestOptions failedRequest) async {
    final refreshToken = await tokenStorage.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      _forceLogout();
      throw ApiException('Oturum süresi doldu, lütfen tekrar giriş yapın.', statusCode: 401);
    }

    if (!_isRefreshing) {
      _isRefreshing = true;
      try {
        final response = await dio.post(
          '/auth/refresh/',
          data: {'refresh': refreshToken},
          options: Options(extra: {'skipAuth': true}),
        );
        final newAccess = response.data['access']?.toString();
        if (newAccess == null || newAccess.isEmpty) {
          throw ApiException('Oturum yenilenemedi.');
        }
        await tokenStorage.saveAccessToken(newAccess);
        _isRefreshing = false;
        for (final retry in _pendingRetries) {
          retry();
        }
        _pendingRetries.clear();
      } catch (e) {
        _isRefreshing = false;
        _pendingRetries.clear();
        await tokenStorage.clear();
        _forceLogout();
        rethrow;
      }
    } else {
      // Başka bir istek zaten refresh yapıyor; tamamlanmasını bekle.
      await Future.doWhile(() async {
        await Future.delayed(const Duration(milliseconds: 100));
        return _isRefreshing;
      });
    }

    final newAccess = await tokenStorage.getAccessToken();
    failedRequest.headers['Authorization'] = 'Bearer $newAccess';
    return dio.fetch(failedRequest);
  }

  void _forceLogout() {
    if (onSessionExpired != null) {
      onSessionExpired!();
    }
  }

  /// Dio'dan gelen ham hatayı, UI'da doğrudan gösterilebilecek bir
  /// [ApiException]'a dönüştürür. Backend'in alan bazlı hata formatı
  /// (`{"username": ["..."]}`) destekli şekilde parse edilir.
  ApiException mapError(Object error) {
    if (error is ApiException) return error;

    if (error is DioException) {
      if (error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.receiveTimeout ||
          error.type == DioExceptionType.sendTimeout ||
          error.type == DioExceptionType.connectionError) {
        return const ApiException(
          'Sunucuya ulaşılamıyor. İnternet bağlantınızı kontrol edin.',
          isNetworkError: true,
        );
      }

      final statusCode = error.response?.statusCode;
      final data = error.response?.data;

      if (data is Map) {
        final Map<String, List<String>> fieldErrors = {};
        String? generalMessage;

        data.forEach((key, value) {
          List<String> messages = [];
          if (value is List) {
            messages = value.map((e) => e.toString()).toList();
          } else if (value is String) {
            messages = [value];
          }
          if (messages.isEmpty) return;

          if (key == 'detail' || key == 'message' || key == 'non_field_errors' || key == 'code') {
            generalMessage = messages.first;
          } else {
            fieldErrors[key] = messages;
          }
        });

        return ApiException(
          generalMessage ?? _defaultMessageFor(statusCode),
          statusCode: statusCode,
          fieldErrors: fieldErrors.isEmpty ? null : fieldErrors,
        );
      }

      return ApiException(_defaultMessageFor(statusCode), statusCode: statusCode);
    }

    return ApiException('Beklenmeyen bir hata oluştu: $error');
  }

  String _defaultMessageFor(int? statusCode) {
    switch (statusCode) {
      case 400:
        return 'Girdiğiniz bilgileri kontrol edip tekrar deneyin.';
      case 401:
        return 'Kullanıcı adı veya şifre hatalı.';
      case 403:
        return 'Bu işlem için yetkiniz yok.';
      case 404:
        return 'İstenen kaynak bulunamadı.';
      case 500:
        return 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.';
      default:
        return 'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.';
    }
  }
}
