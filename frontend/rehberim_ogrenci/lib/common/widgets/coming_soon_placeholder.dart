import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_text_styles.dart';

/// Henüz geliştirilmemiş sekmeler/sayfalar için kullanılan ortak
/// "yakında" yer tutucusu. Böylece boş sayfalar bile marka standardına uyar.
class ComingSoonPlaceholder extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;

  const ComingSoonPlaceholder({
    super.key,
    required this.icon,
    required this.title,
    this.message = 'Bu bölüm üzerinde çalışıyoruz. Çok yakında burada olacak!',
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: const BoxDecoration(
                color: AppColors.primaryLight,
                shape: BoxShape.circle,
              ),
              child: Icon(icon, size: 48, color: AppColors.primary),
            ),
            const SizedBox(height: 24),
            Text(title, style: AppTextStyles.h2, textAlign: TextAlign.center),
            const SizedBox(height: 8),
            Text(
              message,
              style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
