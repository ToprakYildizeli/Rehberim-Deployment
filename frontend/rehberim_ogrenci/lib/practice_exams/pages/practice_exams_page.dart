import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_loading_indicator.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../common/widgets/empty_state_widget.dart';
import '../../data/models/exam_model.dart';
import '../controllers/exam_controller.dart';
import 'exam_detail_page.dart';
import 'exam_form_page.dart';

/// Denemeler sekmesi: öğrencinin girdiği deneme sonuçlarını kart listesi
/// olarak gösterir; hiç deneme yoksa boş durum mesajı gösterilir. Kartlara
/// dokununca detay sayfası açılır, en altta her zaman "Deneme Ekle" butonu
/// bulunur.
class PracticeExamsPage extends StatefulWidget {
  const PracticeExamsPage({super.key});

  @override
  State<PracticeExamsPage> createState() => _PracticeExamsPageState();
}

class _PracticeExamsPageState extends State<PracticeExamsPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ExamController>().loadExams();
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<ExamController>();
    final exams = controller.exams;
    final hasExams = exams.isNotEmpty;

    return Scaffold(
      appBar: AppBar(title: const Text('Denemeler')),
      body: SafeArea(
        child: controller.isLoading && !hasExams
            ? const AppLoadingIndicator(message: 'Denemeler yükleniyor...')
            : Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
                child: Column(
                  children: [
                    Expanded(
                      child: hasExams
                          ? ListView.separated(
                              itemCount: exams.length,
                              separatorBuilder: (_, _) => const SizedBox(height: 10),
                              itemBuilder: (_, index) => _ExamCard(
                                exam: exams[index],
                                onTap: () => _openExamDetail(exams[index]),
                              ),
                            )
                          : const EmptyStateWidget(
                              icon: Icons.fact_check_outlined,
                              title: 'Henüz deneme yok',
                              message: 'Şu an için girilmiş bir deneme sonucun bulunmuyor.',
                            ),
                    ),
                    const SizedBox(height: 16),
                    AppButton(
                      label: 'Deneme Ekle',
                      icon: Icons.add_circle_outline,
                      width: double.infinity,
                      onPressed: _handleAddExam,
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  Future<void> _handleAddExam() async {
    final created = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const ExamFormPage()),
    );

    if (created != true || !mounted) return;

    AppSnackbar.showSuccess(context, 'Deneme başarıyla eklendi.');
    await context.read<ExamController>().loadExams();
  }

  Future<void> _openExamDetail(ExamModel exam) async {
    // Detay sayfası düzenleme/silme yapılırsa `true` ile döner; bu durumda
    // listeyi güncel verilerle yeniden yüklüyoruz.
    final changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => ExamDetailPage(exam: exam)),
    );

    if (changed != true || !mounted) return;
    AppSnackbar.showSuccess(context, 'İşlem başarıyla tamamlandı.');
    await context.read<ExamController>().loadExams();
  }
}

class _ExamCard extends StatelessWidget {
  const _ExamCard({required this.exam, required this.onTap});

  final ExamModel exam;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
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
                  Text(examTitle(exam), style: AppTextStyles.bodyLarge),
                  const SizedBox(height: 6),
                  Text(
                    '${exam.examType.label} • ${formatExamDate(exam.examDate)} • ${formatNet(exam.totalNet)} net',
                    style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
            const Padding(
              padding: EdgeInsets.only(left: 12),
              child: Icon(Icons.arrow_forward_ios_rounded, size: 16, color: AppColors.primary),
            ),
          ],
        ),
      ),
    );
  }
}

/// Bir denemenin başlığı boşsa sınav türünden türetilmiş bir yedek etiket
/// gösterir. Kart ve detay sayfası aynı mantığı paylaşır.
String examTitle(ExamModel exam) {
  if (exam.name?.trim().isNotEmpty == true) return exam.name!.trim();
  return '${exam.examType.label} Deneme';
}

String formatExamDate(DateTime? date) {
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
