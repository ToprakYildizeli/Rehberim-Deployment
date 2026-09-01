import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_dialog.dart';
import '../../common/widgets/app_error_text.dart';
import '../../common/widgets/app_loading_indicator.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../data/models/routine_model.dart';
import '../controllers/routine_controller.dart';
import 'routine_form_page.dart';

/// Öğrencinin rutinlerini listeler.
///
/// Rutin, haftanın günlerine göre kurulan tekrarlayan bir plandır. Yalnızca
/// biri "otomatik" olabilir; koçun açtığı her yeni haftaya o rutinin görevleri
/// kendiliğinden düşer.
class RoutinesPage extends StatefulWidget {
  const RoutinesPage({super.key});

  @override
  State<RoutinesPage> createState() => _RoutinesPageState();
}

class _RoutinesPageState extends State<RoutinesPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<RoutineController>().loadRoutines();
    });
  }

  Future<void> _openForm({RoutineModel? routine}) async {
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => RoutineFormPage(routine: routine)),
    );
    if (saved == true && mounted) {
      AppSnackbar.showSuccess(context, routine == null ? 'Rutin oluşturuldu.' : 'Rutin güncellendi.');
    }
  }

  Future<void> _toggleAuto(RoutineModel routine, bool value) async {
    final controller = context.read<RoutineController>();
    final ok = await controller.setAutoApply(routine, value);
    if (!mounted) return;
    if (ok) {
      AppSnackbar.showSuccess(
        context,
        value ? 'Rutin açıldı. Koçun açtığı yeni haftadan itibaren uygulanacak.' : 'Rutin kapatıldı.',
      );
    } else {
      AppSnackbar.showError(context, controller.errorMessage ?? 'Rutin güncellenemedi.');
    }
  }

  Future<void> _delete(RoutineModel routine) async {
    final confirmed = await AppDialog.confirm(
      context,
      title: 'Rutin silinsin mi?',
      message: '"${routine.name}" kalıcı olarak silinecek. Daha önce haftalarına '
          'eklenmiş görevler olduğu gibi kalır.',
      confirmLabel: 'Sil',
      cancelLabel: 'Vazgeç',
      isDestructive: true,
    );
    if (confirmed != true || !mounted) return;
    final controller = context.read<RoutineController>();
    final ok = await controller.deleteRoutine(routine);
    if (!mounted) return;
    if (ok) {
      AppSnackbar.showSuccess(context, 'Rutin silindi.');
    } else {
      AppSnackbar.showError(context, controller.errorMessage ?? 'Rutin silinemedi.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<RoutineController>();

    return Scaffold(
      appBar: AppBar(title: const Text('Rutinlerim')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(),
        icon: const Icon(Icons.add),
        label: const Text('Rutin Ekle'),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: controller.loadRoutines,
          child: _buildBody(controller),
        ),
      ),
    );
  }

  Widget _buildBody(RoutineController controller) {
    if (controller.isLoading && controller.routines.isEmpty) {
      return const AppLoadingIndicator();
    }
    if (controller.errorMessage != null && controller.routines.isEmpty) {
      return ListView(
        padding: const EdgeInsets.all(20),
        children: [AppErrorText(message: controller.errorMessage!)],
      );
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 96),
      children: [
        const _RoutineExplainer(),
        const SizedBox(height: 20),
        if (controller.routines.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 32),
            child: Text(
              'Henüz rutin kurmadın. Her hafta tekrarlayan çalışmalarını buraya '
              'ekleyerek zaman kazanabilirsin.',
              textAlign: TextAlign.center,
              style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
            ),
          )
        else
          ...controller.routines.map(
            (r) => _RoutineCard(
              routine: r,
              busy: controller.isSubmitting,
              onEdit: () => _openForm(routine: r),
              onToggle: (v) => _toggleAuto(r, v),
              onDelete: () => _delete(r),
            ),
          ),
      ],
    );
  }
}

/// Rutinin ne zaman devreye girdiğini açıklar — koç haftayı açmadan görev
/// oluşmadığı için bu bilgi olmazsa ekran yanıltıcı olur.
class _RoutineExplainer extends StatelessWidget {
  const _RoutineExplainer();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.primaryLight,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.repeat_rounded, size: 18, color: AppColors.primaryDark),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'Rutin, haftanın günlerine göre kurduğun tekrarlayan plandır. '
              'Aynı anda yalnızca bir rutin açık olabilir; koçun sana yeni bir '
              'hafta açtığında görevleri o haftaya kendiliğinden eklenir.',
              style: AppTextStyles.bodyMedium.copyWith(color: AppColors.primaryDark),
            ),
          ),
        ],
      ),
    );
  }
}

class _RoutineCard extends StatelessWidget {
  const _RoutineCard({
    required this.routine,
    required this.busy,
    required this.onEdit,
    required this.onToggle,
    required this.onDelete,
  });

  final RoutineModel routine;
  final bool busy;
  final VoidCallback onEdit;
  final ValueChanged<bool> onToggle;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final hours = routine.totalMinutes / 60;
    final dayCount = routine.tasks.map((t) => t.weekday).toSet().length;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 8, 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    routine.name.isEmpty ? 'Adsız rutin' : routine.name,
                    style: AppTextStyles.bodyLarge.copyWith(fontWeight: FontWeight.w600),
                  ),
                ),
                IconButton(
                  onPressed: busy ? null : onEdit,
                  icon: const Icon(Icons.edit_outlined, size: 20),
                  tooltip: 'Düzenle',
                ),
                IconButton(
                  onPressed: busy ? null : onDelete,
                  icon: const Icon(Icons.delete_outline, size: 20, color: AppColors.error),
                  tooltip: 'Sil',
                ),
              ],
            ),
            Text(
              '${routine.tasks.length} görev · $dayCount gün · '
              '${hours.toStringAsFixed(hours % 1 == 0 ? 0 : 1)} saat',
              style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 6),
            SwitchListTile.adaptive(
              value: routine.autoApply,
              onChanged: busy ? null : onToggle,
              contentPadding: EdgeInsets.zero,
              title: Text(
                routine.autoApply ? 'Açık' : 'Kapalı',
                style: AppTextStyles.bodyMedium.copyWith(
                  fontWeight: FontWeight.w600,
                  color: routine.autoApply ? AppColors.success : AppColors.textSecondary,
                ),
              ),
              subtitle: Text(
                routine.autoApply
                    ? 'Yeni haftalarına otomatik ekleniyor'
                    : 'Şu an hiçbir haftaya eklenmiyor',
                style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
