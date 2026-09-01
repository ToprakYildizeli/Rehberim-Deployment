import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/constants/app_constants.dart';
import '../../common/utils/validators.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_error_text.dart';
import '../../common/widgets/app_text_field.dart';
import '../../common/widgets/app_snackbar.dart';
import '../controllers/auth_controller.dart';
import '../widgets/auth_header.dart';
import 'register_page.dart';

class LoginPage extends StatefulWidget {
  static const routeName = '/login';

  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit(AuthController authController) async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) return;

    await authController.login(
      username: _usernameController.text.trim(),
      password: _passwordController.text,
    );

    if (!mounted) return;

    if (authController.isAuthenticated) {
      AppSnackbar.showSuccess(context, 'Hoşgeldin, ${authController.currentUser!.firstName}!');
    }
    // Navigasyon MaterialApp seviyesinde AuthController durumuna göre otomatik yapılır.
  }

  @override
  Widget build(BuildContext context) {
    final authController = context.watch<AuthController>();

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppConstants.screenPadding),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 24),
                const AuthHeader(
                  title: 'Tekrar Hoş Geldin',
                  subtitle: 'Sınav yolculuğuna kaldığın yerden devam et.',
                ),
                const SizedBox(height: 32),
                AppErrorText(message: authController.errorMessage),
                AppTextField(
                  controller: _usernameController,
                  label: 'Kullanıcı Adı',
                  prefixIcon: Icons.person_outline,
                  textInputAction: TextInputAction.next,
                  validator: Validators.required,
                ),
                const SizedBox(height: 16),
                AppTextField(
                  controller: _passwordController,
                  label: 'Şifre',
                  prefixIcon: Icons.lock_outline,
                  obscureText: true,
                  textInputAction: TextInputAction.done,
                  validator: (v) => Validators.required(v, message: 'Şifre zorunludur'),
                  onChanged: (_) {
                    if (authController.errorMessage != null) authController.clearError();
                  },
                ),
                const SizedBox(height: 28),
                AppButton(
                  label: 'Giriş Yap',
                  isLoading: authController.isSubmitting,
                  onPressed: () => _submit(authController),
                ),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('Hesabın yok mu?'),
                    TextButton(
                      onPressed: authController.isSubmitting
                          ? null
                          : () {
                              authController.clearError();
                              Navigator.of(context).push(
                                MaterialPageRoute(builder: (_) => const RegisterPage()),
                              );
                            },
                      child: const Text('Kayıt Ol'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
