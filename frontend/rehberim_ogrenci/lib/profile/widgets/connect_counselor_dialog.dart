import 'package:flutter/material.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/utils/validators.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_error_text.dart';
import '../../common/widgets/app_text_field.dart';
import '../controllers/profile_controller.dart';

/// Koç davet kodu girilerek bağlanmayı sağlayan pop-up.
///
/// Kullanım: `showConnectCounselorDialog(context, profileController)`.
/// Bağlantı başarılı olursa `true` döndürülerek kapanır.
Future<bool?> showConnectCounselorDialog(
  BuildContext context,
  ProfileController profileController,
) {
  return showDialog<bool>(
    context: context,
    builder: (ctx) => _ConnectCounselorDialogContent(profileController: profileController),
  );
}

class _ConnectCounselorDialogContent extends StatefulWidget {
  final ProfileController profileController;

  const _ConnectCounselorDialogContent({required this.profileController});

  @override
  State<_ConnectCounselorDialogContent> createState() => _ConnectCounselorDialogContentState();
}

class _ConnectCounselorDialogContentState extends State<_ConnectCounselorDialogContent> {
  final _formKey = GlobalKey<FormState>();
  final _codeController = TextEditingController();

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final success = await widget.profileController.connectCounselor(_codeController.text.trim());
    if (success && mounted) {
      Navigator.of(context).pop(true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.profileController,
      builder: (context, _) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
          title: const Text('Koça Bağlan'),
          content: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Koçunun sana verdiği davet kodunu gir.',
                  style: AppTextStyles.bodyMedium,
                ),
                const SizedBox(height: 16),
                AppErrorText(message: widget.profileController.connectCounselorError),
                AppTextField(
                  controller: _codeController,
                  label: 'Koç Davet Kodu',
                  prefixIcon: Icons.badge_outlined,
                  textCapitalization: TextCapitalization.characters,
                  validator: (v) => Validators.required(v, message: 'Davet kodu zorunludur'),
                ),
              ],
            ),
          ),
          actionsPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          actions: [
            Row(
              children: [
                Expanded(
                  child: AppButton(
                    label: 'Vazgeç',
                    variant: AppButtonVariant.outlined,
                    onPressed: widget.profileController.isConnectingCounselor
                        ? null
                        : () => Navigator.of(context).pop(false),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: AppButton(
                    label: 'Bağlan',
                    isLoading: widget.profileController.isConnectingCounselor,
                    onPressed: _submit,
                  ),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}
