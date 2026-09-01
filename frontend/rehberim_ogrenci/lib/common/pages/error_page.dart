import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_text_styles.dart';
import '../widgets/app_button.dart';

/// Beklenmeyen bir hata oluştuğunda gösterilen genel hata sayfası.
/// [onRetry] verilirse "Tekrar Dene" butonu gösterilir.
class ErrorPage extends StatelessWidget {
  final String? message;
  final VoidCallback? onRetry;

  const ErrorPage({super.key, this.message, this.onRetry});

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
                    color: AppColors.error.withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.error_outline, size: 44, color: AppColors.error),
                ),
                const SizedBox(height: 20),
                Text('Bir şeyler ters gitti', style: AppTextStyles.h2, textAlign: TextAlign.center),
                const SizedBox(height: 8),
                Text(
                  message ?? 'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.',
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
