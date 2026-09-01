import 'user_model.dart';

/// `/api/auth/login/` cevabını temsil eder.
class AuthResponseModel {
  final String access;
  final String refresh;
  final UserModel user;

  const AuthResponseModel({
    required this.access,
    required this.refresh,
    required this.user,
  });

  factory AuthResponseModel.fromJson(Map<String, dynamic> json) {
    return AuthResponseModel(
      access: json['access']?.toString() ?? '',
      refresh: json['refresh']?.toString() ?? '',
      user: UserModel.fromJson(Map<String, dynamic>.from(json['user'] as Map)),
    );
  }
}
