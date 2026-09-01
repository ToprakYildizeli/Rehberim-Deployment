import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_dialog.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../data/models/goal_model.dart';
import '../controllers/goal_controller.dart';
import 'goal_form_page.dart';

/// Bir hedefin detayını gösterir: tür, başlık, açıklama, tarih ve ulaşıldı
/// durumu; hedef türü "Deneme Neti" ise sınav türü, ders ve hedef net de
/// eklenir. Düzenle/Sil aksiyonları buradan başlatılır; ikisi de başarılı
/// olduğunda bu sayfa `true` ile kapanır ki takvim sayfası güncel veriyle
/// yeniden yüklensin.
class GoalDetailPage extends StatelessWidget {
  const GoalDetailPage({super.key, required this.goal});

  final GoalModel goal;

  @override
  Widget build(BuildContext context) {
    final goalController = context.watch<GoalController>();
    final isDenemeNeti = goal.goalType == GoalType.denemeNeti;

    return Scaffold(
      appBar: AppBar(title: const Text('Hedef Detayı')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildSummaryCard(),
                      if (isDenemeNeti) ...[
                        const SizedBox(height: 24),
                        Text('Deneme Neti Detayları', style: AppTextStyles.h3),
                        const SizedBox(height: 12),
                        ..._buildExamDetailRows(),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              _buildActionButtons(context, goalController),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSummaryCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  goal.goalType.label,
                  style: AppTextStyles.caption.copyWith(color: AppColors.primary, fontWeight: FontWeight.bold),
                ),
              ),
              const Spacer(),
              if (goal.targetDate != null)
                Text(
                  formatDate(goal.targetDate),
                  style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                ),
            ],
          ),
          const SizedBox(height: 12),
          Text(goalDisplayTitle(goal), style: AppTextStyles.h3),
          if (goal.description?.trim().isNotEmpty == true) ...[
            const SizedBox(height: 8),
            Text(
              goal.description!.trim(),
              style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
            ),
          ],
          const SizedBox(height: 12),
          Row(
            children: [
              Icon(
                goal.isAchieved ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded,
                size: 18,
                color: goal.isAchieved ? AppColors.success : AppColors.textDisabled,
              ),
              const SizedBox(width: 6),
              Text(
                goal.isAchieved ? 'Ulaşıldı' : 'Henüz ulaşılmadı',
                style: AppTextStyles.bodyMedium.copyWith(
                  color: goal.isAchieved ? AppColors.success : AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  List<Widget> _buildExamDetailRows() {
    final rows = <MapEntry<String, String>>[
      MapEntry('Sınav Türü', goal.examScope != ExamScope.none ? goal.examScope.label : '-'),
      MapEntry('Ders', goal.subjectLabel ?? 'Toplam (tüm dersler)'),
      MapEntry('Hedef Net', goal.targetNet != null ? formatNet(goal.targetNet!) : '-'),
    ];

    return rows
        .map(
          (entry) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  Expanded(child: Text(entry.key, style: AppTextStyles.bodyLarge)),
                  Text(
                    entry.value,
                    style: AppTextStyles.bodyLarge.copyWith(color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
          ),
        )
        .toList();
  }

  Widget _buildActionButtons(BuildContext context, GoalController goalController) {
    return Row(
      children: [
        Expanded(
          child: AppButton(
            label: 'Düzenle',
            icon: Icons.edit_outlined,
            variant: AppButtonVariant.secondary,
            onPressed: goalController.isSubmitting ? null : () => _handleEdit(context),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: AppButton(
            label: 'Sil',
            icon: Icons.delete_outline,
            variant: AppButtonVariant.outlined,
            isLoading: goalController.isSubmitting,
            onPressed: goalController.isSubmitting ? null : () => _handleDelete(context),
          ),
        ),
      ],
    );
  }

  Future<void> _handleEdit(BuildContext context) async {
    final updated = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => GoalFormPage(goal: goal)),
    );

    if (updated != true || !context.mounted) return;

    // Değişiklikleri yansıtmak için önceki (takvim) sayfaya haber ver.
    Navigator.of(context).pop(true);
  }

  Future<void> _handleDelete(BuildContext context) async {
    final confirmed = await AppDialog.confirm(
      context,
      title: 'Hedefi Sil',
      message: 'Bu hedefi silmek istediğine emin misin? Bu işlem geri alınamaz.',
      confirmLabel: 'Sil',
      cancelLabel: 'Vazgeç',
      isDestructive: true,
    );
    if (confirmed != true || !context.mounted) return;

    final goalController = context.read<GoalController>();
    if (goal.id == null) {
      AppSnackbar.showError(context, 'Hedef henüz kaydedilmemiş, tekrar deneyin.');
      return;
    }

    final success = await goalController.deleteGoal(goal.id!);
    if (!context.mounted) return;

    if (success) {
      Navigator.of(context).pop(true);
    } else {
      AppSnackbar.showError(
        context,
        goalController.errorMessage ?? 'Hedef silinirken bir hata oluştu.',
      );
    }
  }
}

/// Bir hedefin başlığı boşsa backend'in ürettiği etikete, o da yoksa hedef
/// türüne düşer. Kart ve detay sayfası aynı mantığı paylaşır.
String goalDisplayTitle(GoalModel goal) {
  if (goal.title?.trim().isNotEmpty == true) return goal.title!.trim();
  if (goal.label?.trim().isNotEmpty == true) return goal.label!.trim();
  return goal.goalType.label;
}

String formatDate(DateTime? date) {
  if (date == null) return '-';
  const monthNames = [
    'Ocak',
    'Şubat',
    'Mart',
    'Nisan',
    'Mayıs',
    'Haziran',
    'Temmuz',
    'Ağustos',
    'Eylül',
    'Ekim',
    'Kasım',
    'Aralık',
  ];
  return '${date.day} ${monthNames[date.month - 1]} ${date.year}';
}

/// Net değerini gereksiz ondalık basamak olmadan gösterir (ör. 24 yerine
/// 24.0, ama 24.5 olduğu gibi kalır).
String formatNet(double value) {
  return value == value.roundToDouble() ? value.toStringAsFixed(0) : value.toString();
}
