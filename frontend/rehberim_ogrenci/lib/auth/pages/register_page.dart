import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/constants/app_constants.dart';
import '../../common/theme/app_colors.dart';
import '../../common/utils/validators.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_error_text.dart';
import '../../common/widgets/app_text_field.dart';
import '../controllers/auth_controller.dart';
import '../widgets/auth_header.dart';

class RegisterPage extends StatefulWidget {
  static const routeName = '/register';

  const RegisterPage({super.key});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _formKey = GlobalKey<FormState>();

  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _counselorCodeController = TextEditingController();

  String? _selectedGrade;
  String? _selectedStudyField;

  bool get _studyFieldRequired =>
      _selectedGrade != null && GradeOption.requiresStudyField(_selectedGrade!);

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _usernameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _counselorCodeController.dispose();
    super.dispose();
  }

  Future<void> _submit(AuthController authController) async {
    FocusScope.of(context).unfocus();

    if (!_formKey.currentState!.validate()) return;

    if (_selectedGrade == null) {
      _showFieldError('Lütfen sınıfını seç.');
      return;
    }
    if (_studyFieldRequired && _selectedStudyField == null) {
      _showFieldError('11, 12. sınıf ve mezun öğrenciler için alan seçimi zorunludur.');
      return;
    }

    final success = await authController.registerStudent(
      username: _usernameController.text.trim(),
      email: _emailController.text.trim(),
      password: _passwordController.text,
      firstName: _firstNameController.text.trim(),
      lastName: _lastNameController.text.trim(),
      grade: _selectedGrade!,
      studyField: _studyFieldRequired ? _selectedStudyField : null,
      counselorCode:
          _counselorCodeController.text.trim().isEmpty ? null : _counselorCodeController.text.trim(),
    );

    if (success && mounted) {
      // Kayıt + otomatik giriş başarılı; MaterialApp seviyesindeki
      // AuthController dinleyicisi kullanıcıyı ana navigasyona yönlendirecek.
      Navigator.of(context).popUntil((route) => route.isFirst);
    }
  }

  void _showFieldError(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message), backgroundColor: AppColors.error));
  }

  @override
  Widget build(BuildContext context) {
    final authController = context.watch<AuthController>();

    return Scaffold(
      appBar: AppBar(title: const Text('Kayıt Ol')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppConstants.screenPadding),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const AuthHeader(
                  title: 'Hesap Oluştur',
                  subtitle: 'Sınav hazırlık yolculuğuna hemen başla.',
                ),
                const SizedBox(height: 28),
                AppErrorText(message: authController.errorMessage),
                Row(
                  children: [
                    Expanded(
                      child: AppTextField(
                        controller: _firstNameController,
                        label: 'Ad',
                        textCapitalization: TextCapitalization.words,
                        textInputAction: TextInputAction.next,
                        validator: (v) => Validators.name(v, message: 'Ad zorunludur'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: AppTextField(
                        controller: _lastNameController,
                        label: 'Soyad',
                        textCapitalization: TextCapitalization.words,
                        textInputAction: TextInputAction.next,
                        validator: (v) => Validators.name(v, message: 'Soyad zorunludur'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                AppTextField(
                  controller: _usernameController,
                  label: 'Kullanıcı Adı',
                  prefixIcon: Icons.person_outline,
                  textInputAction: TextInputAction.next,
                  validator: Validators.username,
                ),
                const SizedBox(height: 16),
                AppTextField(
                  controller: _emailController,
                  label: 'E-posta',
                  prefixIcon: Icons.email_outlined,
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  validator: Validators.email,
                ),
                const SizedBox(height: 16),
                AppTextField(
                  controller: _passwordController,
                  label: 'Şifre',
                  prefixIcon: Icons.lock_outline,
                  obscureText: true,
                  textInputAction: TextInputAction.next,
                  validator: (value) => Validators.password(
                    value,
                    username: _usernameController.text,
                    firstName: _firstNameController.text,
                    lastName: _lastNameController.text,
                  ),
                ),
                const SizedBox(height: 16),
                AppTextField(
                  controller: _confirmPasswordController,
                  label: 'Şifre (Tekrar)',
                  prefixIcon: Icons.lock_outline,
                  obscureText: true,
                  textInputAction: TextInputAction.next,
                  validator: (v) => Validators.confirmPassword(v, _passwordController.text),
                ),
                const SizedBox(height: 20),
                DropdownButtonFormField<String>(
                  initialValue: _selectedGrade,
                  decoration: const InputDecoration(labelText: 'Sınıf'),
                  items: GradeOption.all
                      .map((g) => DropdownMenuItem(value: g.value, child: Text(g.label)))
                      .toList(),
                  onChanged: (value) {
                    setState(() {
                      _selectedGrade = value;
                      // Sınıf 9/10 seçilirse alan seçimi tamamen gizlenir/sıfırlanır.
                      if (value != null && !GradeOption.requiresStudyField(value)) {
                        _selectedStudyField = null;
                      }
                    });
                  },
                  validator: (value) => value == null ? 'Sınıf seçimi zorunludur' : null,
                ),
                if (_studyFieldRequired) ...[
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    initialValue: _selectedStudyField,
                    decoration: const InputDecoration(labelText: 'Alan'),
                    items: StudyFieldOption.all
                        .map((f) => DropdownMenuItem(value: f.value, child: Text(f.label)))
                        .toList(),
                    onChanged: (value) => setState(() => _selectedStudyField = value),
                    validator: (value) =>
                        (_studyFieldRequired && value == null) ? 'Alan seçimi zorunludur' : null,
                  ),
                ],
                const SizedBox(height: 16),
                AppTextField(
                  controller: _counselorCodeController,
                  label: 'Koç Davet Kodu (Opsiyonel)',
                  hint: 'Varsa danışmanının davet kodunu gir',
                  prefixIcon: Icons.badge_outlined,
                  textInputAction: TextInputAction.done,
                  textCapitalization: TextCapitalization.characters,
                ),
                const SizedBox(height: 28),
                AppButton(
                  label: 'Kayıt Ol',
                  isLoading: authController.isSubmitting,
                  onPressed: () => _submit(authController),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('Zaten hesabın var mı?'),
                    TextButton(
                      onPressed: authController.isSubmitting
                          ? null
                          : () {
                              authController.clearError();
                              Navigator.of(context).pop();
                            },
                      child: const Text('Giriş Yap'),
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
