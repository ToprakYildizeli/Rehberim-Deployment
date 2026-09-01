import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_dialog.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../data/models/exam_model.dart';
import '../../data/models/subject_net_model.dart';
import '../controllers/exam_controller.dart';
import 'exam_form_page.dart';
import 'practice_exams_page.dart' show examTitle, formatExamDate, formatNet;

/// Bir deneme sonucunun detayını gösterir: sınav türü, başlık, tarih, toplam
/// net ve ders bazlı netler. Düzenle/Sil aksiyonları buradan başlatılır;
/// ikisi de başarılı olduğunda bu sayfa `true` ile kapanır ki liste sayfası
/// güncel veriyle yeniden yüklensin.
class ExamDetailPage extends StatelessWidget {
  const ExamDetailPage({super.key, required this.exam});

  final ExamModel exam;

  @override
  Widget build(BuildContext context) {
    final examController = context.watch<ExamController>();

    return Scaffold(
      appBar: AppBar(title: const Text('Deneme Detayı')),
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
                      const SizedBox(height: 24),
                      Text('Ders Netleri', style: AppTextStyles.h3),
                      const SizedBox(height: 12),
                      if (exam.subjectNets.isEmpty)
                        Text(
                          'Bu deneme için ders bazlı net girilmemiş.',
                          style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                        )
                      else
                        ..._buildSubjectNetRows(),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              _buildActionButtons(context, examController),
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
                  exam.examType.label,
                  style: AppTextStyles.caption.copyWith(color: AppColors.primary, fontWeight: FontWeight.bold),
                ),
              ),
              const Spacer(),
              Text(
                formatExamDate(exam.examDate),
                style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(examTitle(exam), style: AppTextStyles.h3),
          const SizedBox(height: 8),
          Text(
            '${formatNet(exam.totalNet)} net',
            style: AppTextStyles.bodyLarge.copyWith(color: AppColors.primary, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildSubjectNetRows() {
    return exam.subjectNets
        .map(
          (subjectNet) => Padding(
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
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          subjectNet.subjectLabel ?? 'Bilinmeyen Ders',
                          style: AppTextStyles.bodyLarge,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          _breakdown(subjectNet),
                          style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                        ),
                      ],
                    ),
                  ),
                  Text(
                    '${formatNet(subjectNet.net)} net',
                    style: AppTextStyles.bodyLarge.copyWith(color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
          ),
        )
        .toList();
  }

  /// "12 doğru · 4 yanlış · 6 boş" — boş yalnızca sunucu hesaplayabildiyse
  /// (dersin soru sayısı biliniyorsa) gösterilir.
  String _breakdown(SubjectNetModel subjectNet) {
    final parts = ['${subjectNet.correct} doğru', '${subjectNet.wrong} yanlış'];
    if (subjectNet.blank != null) parts.add('${subjectNet.blank} boş');
    return parts.join(' · ');
  }

  Widget _buildActionButtons(BuildContext context, ExamController examController) {
    return Row(
      children: [
        Expanded(
          child: AppButton(
            label: 'Düzenle',
            icon: Icons.edit_outlined,
            variant: AppButtonVariant.secondary,
            onPressed: examController.isSubmitting ? null : () => _handleEdit(context),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: AppButton(
            label: 'Sil',
            icon: Icons.delete_outline,
            variant: AppButtonVariant.outlined,
            isLoading: examController.isSubmitting,
            onPressed: examController.isSubmitting ? null : () => _handleDelete(context),
          ),
        ),
      ],
    );
  }

  Future<void> _handleEdit(BuildContext context) async {
    final updated = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => ExamFormPage(exam: exam)),
    );

    if (updated != true || !context.mounted) return;

    // Değişiklikleri yansıtmak için önceki (liste) sayfaya haber ver.
    Navigator.of(context).pop(true);
  }

  Future<void> _handleDelete(BuildContext context) async {
    final confirmed = await AppDialog.confirm(
      context,
      title: 'Denemeyi Sil',
      message: 'Bu denemeyi silmek istediğine emin misin? Bu işlem geri alınamaz.',
      confirmLabel: 'Sil',
      cancelLabel: 'Vazgeç',
      isDestructive: true,
    );
    if (confirmed != true || !context.mounted) return;

    final examController = context.read<ExamController>();
    if (exam.id == null) {
      AppSnackbar.showError(context, 'Deneme henüz kaydedilmemiş, tekrar deneyin.');
      return;
    }

    final success = await examController.deleteExam(exam.id!);
    if (!context.mounted) return;

    if (success) {
      Navigator.of(context).pop(true);
    } else {
      AppSnackbar.showError(
        context,
        examController.errorMessage ?? 'Deneme silinirken bir hata oluştu.',
      );
    }
  }
}
