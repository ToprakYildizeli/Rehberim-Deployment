import 'package:flutter/material.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../data/models/counselor_model.dart';

/// Öğrencinin bağlı olduğu danışmanı gösterir; bağlı değilse
/// davet kodu ile bağlanma çağrısı (call-to-action) sunar.
class CounselorCard extends StatelessWidget {
  final CounselorModel? counselor;
  final VoidCallback onConnectPressed;

  const CounselorCard({super.key, required this.counselor, required this.onConnectPressed});

  @override
  Widget build(BuildContext context) {
    if (counselor != null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: AppColors.success.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(Icons.verified_user_rounded, color: AppColors.success),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Koçun', style: AppTextStyles.bodySmall),
                    const SizedBox(height: 2),
                    Text(counselor!.name, style: AppTextStyles.h3),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 52,
                  height: 52,
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: const Icon(Icons.person_search_rounded, color: AppColors.primary),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Bağlı Koç Yok', style: AppTextStyles.h3),
                      const SizedBox(height: 2),
                      Text(
                        'Davet kodunla bir danışmana bağlanabilirsin.',
                        style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            AppButton(
              label: 'Koça Bağlan',
              variant: AppButtonVariant.secondary,
              icon: Icons.badge_outlined,
              onPressed: onConnectPressed,
            ),
          ],
        ),
      ),
    );
  }
}
