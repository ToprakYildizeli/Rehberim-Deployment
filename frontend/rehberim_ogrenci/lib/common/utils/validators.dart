/// Form alanları için ortak doğrulama fonksiyonları.
abstract class Validators {
  Validators._();

  static String? required(String? value, {String message = 'Bu alan zorunludur'}) {
    if (value == null || value.trim().isEmpty) {
      return message;
    }
    return null;
  }

  static String? username(String? value) {
    final requiredError = required(value, message: 'Kullanıcı adı zorunludur');
    if (requiredError != null) return requiredError;
    if (value!.trim().length < 3) {
      return 'Kullanıcı adı en az 3 karakter olmalıdır';
    }
    final validPattern = RegExp(r'^[a-zA-Z0-9_.]+$');
    if (!validPattern.hasMatch(value.trim())) {
      return 'Kullanıcı adı yalnızca harf, rakam, nokta ve alt çizgi içerebilir';
    }
    return null;
  }

  static String? email(String? value) {
    final requiredError = required(value, message: 'E-posta zorunludur');
    if (requiredError != null) return requiredError;
    final emailPattern = RegExp(r'^[\w\.\-]+@([\w\-]+\.)+[\w\-]{2,4}$');
    if (!emailPattern.hasMatch(value!.trim())) {
      return 'Geçerli bir e-posta adresi giriniz';
    }
    return null;
  }

  static String? password(
    String? value, {
    String? username,
    String? firstName,
    String? lastName,
  }) {
    final requiredError = required(value, message: 'Şifre zorunludur');
    if (requiredError != null) return requiredError;

    final password = value!.trim();
    if (password.length < 8) {
      return 'Şifre en az 8 karakter olmalıdır';
    }

    if (_isNumericPassword(password)) {
      return 'Şifre sadece rakamlardan oluşamaz';
    }

    if (_isCommonPassword(password)) {
      return 'Şifre çok yaygın bir şifre olamaz';
    }

    if (_isSimilarToUserAttributes(
      password,
      username: username,
      firstName: firstName,
      lastName: lastName,
    )) {
      return 'Şifre kullanıcı bilgilerine benzer olamaz';
    }

    return null;
  }

  static String? confirmPassword(String? value, String original) {
    final requiredError = required(value, message: 'Şifre tekrarı zorunludur');
    if (requiredError != null) return requiredError;
    if (value != original) {
      return 'Şifreler eşleşmiyor';
    }
    return null;
  }

  static String? name(String? value, {String message = 'Bu alan zorunludur'}) {
    return required(value, message: message);
  }

  static bool _isNumericPassword(String password) {
    return RegExp(r'^\d+$').hasMatch(password);
  }

  static bool _isCommonPassword(String password) {
    final normalized = password.toLowerCase();
    const commonPasswords = <String>{
      'password',
      'password123',
      'password123!',
      'qwerty',
      'qwerty123',
      'letmein',
      'admin',
      'welcome',
      'passw0rd',
      'secret',
      'abcd1234',
      'test1234',
      '12345678',
      '123456789',
    };

    return commonPasswords.contains(normalized);
  }

  static bool _isSimilarToUserAttributes(
    String password, {
    String? username,
    String? firstName,
    String? lastName,
  }) {
    final normalizedPassword = password.toLowerCase();
    final attributes = <String?>[
      username?.trim(),
      firstName?.trim(),
      lastName?.trim(),
    ].whereType<String>().map((value) => value.toLowerCase()).where((value) => value.isNotEmpty).toList();

    for (final attribute in attributes) {
      final normalizedAttribute = attribute.replaceAll(RegExp(r'[^a-z0-9]'), '');
      if (normalizedAttribute.length < 4) {
        continue;
      }

      if (normalizedPassword.contains(normalizedAttribute)) {
        return true;
      }
    }

    return false;
  }
}
