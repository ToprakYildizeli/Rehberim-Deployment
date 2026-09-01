import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_text_styles.dart';
import '../widgets/app_button.dart';

/// İnternet bağlantısı olmadığında veya sunucuya ulaşılamadığında
/// gösterilen ortak sayfa.
class NetworkErrorPage extends StatelessWidget {
  final VoidCallback? onRetry;

  const NetworkErrorPage({super.key, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppColors.warning.withValues(alpha: 0.12),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.wifi_off_rounded, size: 44, color: AppColors.warning),
                ),
                const SizedBox(height: 20),
                Text('Bağlantı Sorunu', style: AppTextStyles.h2, textAlign: TextAlign.center),
                const SizedBox(height: 8),
                Text(
                  'Sunucuya ulaşılamıyor. Lütfen internet bağlantınızı kontrol edip tekrar deneyin.',
                  style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                  textAlign: TextAlign.center,
                ),
                if (onRetry != null) ...[
                  const SizedBox(height: 24),
                  AppButton(label: 'Tekrar Dene', onPressed: onRetry, width: 200),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
