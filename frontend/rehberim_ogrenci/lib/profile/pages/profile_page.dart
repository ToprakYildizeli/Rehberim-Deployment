import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../auth/controllers/auth_controller.dart';
import '../../common/constants/app_constants.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_dialog.dart';
import '../../common/widgets/app_loading_indicator.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../routines/pages/routines_page.dart';
import '../controllers/profile_controller.dart';
import '../widgets/connect_counselor_dialog.dart';
import '../widgets/counselor_card.dart';
import '../widgets/profile_info_card.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  late final ProfileController _profileController;

  @override
  void initState() {
    super.initState();
    final authController = context.read<AuthController>();
    _profileController = ProfileController(authController: authController);
  }

  @override
  void dispose() {
    _profileController.dispose();
    super.dispose();
  }

  Future<void> _onConnectPressed() async {
    _profileController.clearConnectError();
    await showConnectCounselorDialog(context, _profileController);
    if (mounted && _profileController.authController.currentUser?.hasCounselor == true) {
      AppSnackbar.showSuccess(context, 'Koça başarıyla bağlandın.');
    }
  }

  Future<void> _onLogoutPressed() async {
    final confirmed = await AppDialog.confirm(
      context,
      title: 'Çıkış Yap',
      message: 'Hesabından çıkış yapmak istediğine emin misin?',
      confirmLabel: 'Çıkış Yap',
      cancelLabel: 'Vazgeç',
      isDestructive: true,
    );
    if (confirmed == true) {
      await _profileController.logout();
      if (!mounted) return;
      AppSnackbar.showSuccess(context, 'Çıkış yapıldı.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _profileController,
      builder: (context, _) {
        final user = _profileController.authController.currentUser;

        return Scaffold(
          appBar: AppBar(title: const Text('Profil')),
          body: SafeArea(
            child: user == null
                ? const AppLoadingIndicator()
                : RefreshIndicator(
                    onRefresh: _profileController.refreshProfile,
                    child: ListView(
                      padding: const EdgeInsets.all(AppConstants.screenPadding),
                      children: [
                        ProfileInfoCard(user: user),
                        const SizedBox(height: 16),
                        CounselorCard(
                          counselor: user.counselor,
                          onConnectPressed: _onConnectPressed,
                        ),
                        const SizedBox(height: 32),
                        Text('Çalışma', style: AppTextStyles.h3),
                        const SizedBox(height: 12),
                        Card(
                          child: ListTile(
                            leading: const Icon(Icons.repeat_rounded, color: AppColors.primary),
                            title: const Text(
                              'Rutinlerim',
                              style: TextStyle(fontWeight: FontWeight.w600),
                            ),
                            subtitle: const Text('Her hafta tekrarlayan çalışma planın'),
                            trailing: const Icon(Icons.chevron_right_rounded),
                            onTap: () => Navigator.of(context).push(
                              MaterialPageRoute(builder: (_) => const RoutinesPage()),
                            ),
                          ),
                        ),
                        const SizedBox(height: 32),
                        Text('Hesap', style: AppTextStyles.h3),
                        const SizedBox(height: 12),
                        Card(
                          child: ListTile(
                            leading: const Icon(Icons.logout_rounded, color: AppColors.error),
                            title: const Text(
                              'Çıkış Yap',
                              style: TextStyle(color: AppColors.error, fontWeight: FontWeight.w600),
                            ),
                            onTap: _profileController.authController.isSubmitting
                                ? null
                                : _onLogoutPressed,
                          ),
                        ),
                        const SizedBox(height: 24),
                      ],
                    ),
                  ),
          ),
        );
      },
    );
  }
}
