import 'counselor_model.dart';

/// Uygulamadaki (öğrenci) kullanıcıyı temsil eder.
///
/// Backend, profil alanlarını (`grade`, `study_field`, `counselor`) bazen
/// `profile` anahtarı altında iç içe, bazen de kullanıcı objesinin
/// doğrudan içinde döndürebilir. Bu yüzden [fromJson] her iki durumu da
/// destekleyecek şekilde yazılmıştır.
class UserModel {
  final int? id;
  final String username;
  final String email;
  final String? firstName;
  final String? lastName;
  final String? grade;
  final String? studyField;
  final CounselorModel? counselor;

  const UserModel({
    this.id,
    required this.username,
    required this.email,
    this.firstName,
    this.lastName,
    this.grade,
    this.studyField,
    this.counselor,
  });

  String get fullName {
    final name = [firstName, lastName].where((e) => e != null && e.trim().isNotEmpty).join(' ');
    return name.isNotEmpty ? name : username;
  }

  bool get hasCounselor => counselor != null;

  factory UserModel.fromJson(Map<String, dynamic> json) {
    // Profil bilgisi ayrı bir "profile" objesinde gelmiş olabilir.
    final Map<String, dynamic> profile = (json['profile'] is Map)
        ? Map<String, dynamic>.from(json['profile'] as Map)
        : json;

    final dynamic counselorJson = profile['counselor'] ?? json['counselor'];

    return UserModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}'),
      username: json['username']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      firstName: json['first_name']?.toString(),
      lastName: json['last_name']?.toString(),
      grade: profile['grade']?.toString(),
      studyField: profile['study_field']?.toString(),
      counselor: (counselorJson is Map)
          ? CounselorModel.fromJson(Map<String, dynamic>.from(counselorJson))
          : null,
    );
  }

  UserModel copyWith({CounselorModel? counselor}) {
    return UserModel(
      id: id,
      username: username,
      email: email,
      firstName: firstName,
      lastName: lastName,
      grade: grade,
      studyField: studyField,
      counselor: counselor ?? this.counselor,
    );
  }
}
