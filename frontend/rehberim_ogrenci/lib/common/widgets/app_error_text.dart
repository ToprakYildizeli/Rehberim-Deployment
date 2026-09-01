import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_text_styles.dart';

/// Formların üstünde / API hatalarını göstermek için kullanılan
/// standart hata metni kutusu. [message] null veya boşsa hiçbir şey render etmez.
class AppErrorText extends StatelessWidget {
  final String? message;
  final EdgeInsetsGeometry? margin;

  const AppErrorText({super.key, required this.message, this.margin});

  @override
  Widget build(BuildContext context) {
    if (message == null || message!.trim().isEmpty) {
      return const SizedBox.shrink();
    }
    return Container(
      width: double.infinity,
      margin: margin ?? const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.error.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.error.withValues(alpha: 0.25)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, color: AppColors.error, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message!,
              style: AppTextStyles.errorText,
            ),
          ),
        ],
      ),
    );
  }
}
