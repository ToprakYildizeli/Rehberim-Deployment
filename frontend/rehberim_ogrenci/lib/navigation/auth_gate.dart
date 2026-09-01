import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../auth/controllers/auth_controller.dart';
import '../auth/pages/login_page.dart';
import '../common/pages/splash_page.dart';
import 'main_nav_page.dart';

/// Uygulama kök widget'ı: [AuthController.status] durumuna göre
/// Splash / Giriş / Ana Navigasyon ekranları arasında geçiş yapar.
class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final status = context.watch<AuthController>().status;

    switch (status) {
      case AuthStatus.unknown:
        return const SplashPage();
      case AuthStatus.authenticated:
        return const MainNavPage();
      case AuthStatus.unauthenticated:
      case AuthStatus.authenticating:
        return const LoginPage();
    }
  }
}
