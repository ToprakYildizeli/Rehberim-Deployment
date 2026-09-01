import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_dialog.dart';
import '../../common/widgets/app_loading_indicator.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../common/widgets/app_text_field.dart';
import '../../common/widgets/empty_state_widget.dart';
import '../../data/models/program_model.dart';
import '../../data/models/task_model.dart';
import '../controllers/task_controller.dart';
import '../controllers/weekly_program_controller.dart';
import './task_form_page.dart';
import './weekly_calendar_view.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  DateTime? _selectedDate;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<WeeklyProgramController>().loadCurrentProgram();
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<WeeklyProgramController>();
    final program = controller.currentProgram;
    final selectedDate = _selectedDate ?? _initialDateForProgram(program);
    final tasksForDay = _tasksForDay(program?.tasks ?? const [], selectedDate, program?.scheduleType ?? ScheduleType.untimed);
    final pendingTasks = tasksForDay.where((task) => !task.isCompleted).toList();
    final completedTasks = tasksForDay.where((task) => task.isCompleted).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Haftalık Program'),
      ),
      body: SafeArea(
        child: controller.isLoading && program == null
            ? const AppLoadingIndicator(message: 'Program yükleniyor...')
            : program == null
                ? const EmptyStateWidget(
                    icon: Icons.event_note_outlined,
                    title: 'Henüz program yok',
                    message: 'Şu an için görünür bir haftalık program bulunmuyor.',
                  )
                : SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildWeekBar(program, selectedDate),
                        const SizedBox(height: 20),
                        Text(
                          _formatDate(selectedDate),
                          style: AppTextStyles.h3,
                        ),
                        const SizedBox(height: 12),
                        if (pendingTasks.isEmpty && completedTasks.isEmpty)
                          const EmptyStateWidget(
                            icon: Icons.check_circle_outline,
                            title: 'Bu gün için görev yok',
                            message: 'Seçilen güne ait görev bulunmuyor.',
                          )
                        else ...[
                          if (pendingTasks.isNotEmpty) ...[
                            _buildTaskSection('Bekleyen Görevler', pendingTasks, isCompleted: false),
                            const SizedBox(height: 16),
                          ],
                          if (completedTasks.isNotEmpty)
                            _buildTaskSection('Tamamlanan Görevler', completedTasks, isCompleted: true),
                        ],
                        const SizedBox(height: 20),
                        _buildActionButtons(program, selectedDate),
                      ],
                    ),
                  ),
      ),
    );
  }

  Widget _buildWeekBar(ProgramModel program, DateTime selectedDate) {
    final days = List.generate(7, (index) {
      final date = program.startDate!.add(Duration(days: index));
      return date;
    });

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: days.map((day) {
          final isToday = _isSameDay(day, selectedDate);
          final allCompleted = _areAllTasksCompleted(program.tasks, day);

          return Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 3),
              child: InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: () => setState(() => _selectedDate = day),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  decoration: BoxDecoration(
                    color: isToday ? AppColors.primary : AppColors.primaryLight.withValues(alpha: 0.35),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      Text(
                        _dayLabel(day),
                        style: AppTextStyles.caption.copyWith(
                          color: isToday ? Colors.white : AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        day.day.toString(),
                        style: AppTextStyles.h3.copyWith(
                          color: isToday ? Colors.white : AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 6),
                      if (allCompleted)
                        const Icon(Icons.check_circle, size: 16, color: AppColors.success)
                      else
                        const SizedBox(height: 16),
                    ],
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

Widget _buildActionButtons(ProgramModel program, DateTime selectedDate) {
  return Column(
    children: [
      Row(
        children: [
          Expanded(
            child: AppButton(
              label: 'Düzenle',
              icon: Icons.edit_calendar_outlined,
              variant: AppButtonVariant.secondary,
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => WeeklyCalendarView(program: program),
                  ),
                );
              },
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: AppButton(
              label: 'Görev Ekle',
              icon: Icons.add_task_outlined,
              variant: AppButtonVariant.outlined,
              onPressed: () => _openTaskForm(program: program, selectedDate: selectedDate),
            ),
          ),
        ],
      ),
      const SizedBox(height: 12),
      AppButton(
        label: 'Diğer Haftalar',
        icon: Icons.calendar_month_outlined,
        variant: AppButtonVariant.text,
        onPressed: () => _showOtherWeeksSheet(),
      ),
    ],
  );
}

Future<void> _openTaskForm({required ProgramModel program, required DateTime selectedDate, TaskModel? task}) async {
  final weeklyController = context.read<WeeklyProgramController>();

  final saved = await Navigator.of(context).push<bool>(
    MaterialPageRoute(
      builder: (_) => TaskFormPage(initialProgram: program, initialDate: selectedDate, task: task),
    ),
  );

  if (saved != true || !mounted) return;

  AppSnackbar.showSuccess(context, task == null ? 'Görev başarıyla eklendi.' : 'Görev güncellendi.');
  if (weeklyController.currentProgram?.id != null) {
    await weeklyController.loadProgramDetails(weeklyController.currentProgram!.id!);
  } else {
    await weeklyController.loadCurrentProgram();
  }
}

Future<void> _showOtherWeeksSheet() async {
  final controller = context.read<WeeklyProgramController>();
  await controller.loadPrograms();
  if (!mounted) return;
  if (controller.programs.isEmpty) return;

  final program = controller.currentProgram;

  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
    ),
    builder: (sheetContext) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Diğer Haftalar', style: AppTextStyles.h3),
              const SizedBox(height: 16),
              Flexible(
                child: ListView.separated(
                  shrinkWrap: true,
                  itemCount: controller.programs.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (_, index) {
                    final item = controller.programs[index];
                    final isCurrent = item.id == program?.id;
                    return InkWell(
                      onTap: () async {
                        Navigator.pop(sheetContext);
                        await controller.selectProgram(item.id!);
                        if (!mounted) return;
                        setState(() {
                          _selectedDate = _initialDateForProgram(controller.currentProgram);
                        });
                      },
                      borderRadius: BorderRadius.circular(16),
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: isCurrent ? AppColors.primaryLight : AppColors.surface,
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
                                    '${_formatDate(item.startDate)} - ${_formatDate(item.endDate)}',
                                    style: AppTextStyles.bodyLarge,
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    item.scheduleType == ScheduleType.timed ? 'Saatli' : 'Saatsiz',
                                    style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                                  ),
                                ],
                              ),
                            ),
                            if (isCurrent)
                              const Icon(Icons.check_circle, color: AppColors.primary),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      );
    },
  );
}

  Widget _buildTaskSection(String title, List<TaskModel> tasks, {required bool isCompleted}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              isCompleted ? Icons.check_circle_rounded : Icons.pending_actions_outlined,
              color: isCompleted ? AppColors.success : AppColors.warning,
              size: 18,
            ),
            const SizedBox(width: 8),
            Text(title, style: AppTextStyles.h3),
          ],
        ),
        const SizedBox(height: 10),
        ...tasks.map((task) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: _TaskCard(task: task, onTap: () => _showTaskCompletionDialog(task)),
            )),
      ],
    );
  }

  Future<void> _showTaskCompletionDialog(TaskModel task) async {
    final taskController = context.read<TaskController>();
    final weeklyController = context.read<WeeklyProgramController>();

    if (task.id == null) {
      AppSnackbar.showError(context, 'Görev henüz kaydedilmedi, lütfen tekrar deneyin.');
      return;
    }

    final result = await showDialog<_TaskDialogResult>(
      context: context,
      builder: (dialogContext) => _TaskCompletionDialog(task: task),
    );

    if (result == null || !mounted) return;

    if (result.isEdit) {
      final program = weeklyController.currentProgram;
      if (program == null) return;
      await _openTaskForm(program: program, selectedDate: task.date ?? DateTime.now(), task: task);
      return;
    }

    if (result.isDelete) {
      final confirmed = await AppDialog.confirm(
        context,
        title: 'Görevi Sil',
        message: 'Bu görevi silmek istediğine emin misin? Bu işlem geri alınamaz.',
        confirmLabel: 'Sil',
        cancelLabel: 'Vazgeç',
        isDestructive: true,
      );
      if (confirmed != true || !mounted) return;

      final deleted = await taskController.deleteTask(task.id!);
      if (!mounted) return;

      if (!deleted) {
        AppSnackbar.showError(
          context,
          taskController.errorMessage ?? 'Görev silinirken bir hata oluştu.',
        );
        return;
      }

      AppSnackbar.showSuccess(context, 'Görev silindi.');
      if (weeklyController.currentProgram?.id != null) {
        await weeklyController.loadProgramDetails(weeklyController.currentProgram!.id!);
      } else {
        await weeklyController.loadCurrentProgram();
      }
      return;
    }

    final bool success;
    if (result.markIncomplete) {
      success = await taskController.toggleCompletion(task.id!, false);
    } else {
      success = await taskController.toggleCompletion(
        task.id!,
        true,
        description: result.description?.trim().isNotEmpty == true ? result.description!.trim() : null,
      );
    }

    if (!mounted) return;

    if (!success) {
      AppSnackbar.showError(
        context,
        taskController.errorMessage ?? 'Görev güncellenirken bir hata oluştu.',
      );
      return;
    }

    AppSnackbar.showSuccess(
      context,
      result.markIncomplete ? 'Görev tamamlanmadı olarak işaretlendi.' : 'Görev tamamlandı olarak işaretlendi.',
    );

    // Task, sunucuda program üzerinden döndüğü için görüntülenen programı
    // güncel görev durumlarıyla yeniden yüklüyoruz.
    if (weeklyController.currentProgram?.id != null) {
      await weeklyController.loadProgramDetails(weeklyController.currentProgram!.id!);
    } else {
      await weeklyController.loadCurrentProgram();
    }
  }

  List<TaskModel> _tasksForDay(List<TaskModel> tasks, DateTime selectedDate, ScheduleType scheduleType) {
    final filtered = tasks.where((task) => task.date != null && _isSameDay(task.date!, selectedDate)).toList();
    filtered.sort((a, b) => compareTasksForDisplay(a, b, scheduleType));
    return filtered;
  }

  bool _areAllTasksCompleted(List<TaskModel> tasks, DateTime date) {
    final dayTasks = tasks.where((task) => task.date != null && _isSameDay(task.date!, date)).toList();
    if (dayTasks.isEmpty) return false;
    return dayTasks.every((task) => task.isCompleted);
  }

  DateTime _initialDateForProgram(ProgramModel? program) {
    if (program?.startDate != null) {
      final today = DateTime.now();
      if (program!.startDate!.isBefore(today) && program.endDate!.isAfter(today)) {
        return today;
      }
      return program.startDate!;
    }
    return DateTime.now();
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  String _dayLabel(DateTime date) {
    const labels = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];
    return labels[date.weekday - 1];
  }

  String _formatDate(DateTime? date) {
    if (date == null) return '-';

    const monthNames = [
      'Ocak',
      'Şubat',
      'Mart',
      'Nisan',
      ' Mayıs',
      'Haziran',
      'Temmuz',
      'Ağustos',
      'Eylül',
      'Ekim',
      'Kasım',
      'Aralık',
    ];

    final monthName = monthNames[date.month - 1];
    return '${date.day} $monthName ${date.year}';
  }
}

/// Bir görevin ders ve çalışma türü etiketini oluşturur. Kart ve tamamlama
/// diyaloğu aynı biçimi paylaşır.
String taskSubjectTypeLabel(TaskModel task) {
  return '${task.subjectLabel ?? 'Belirsiz Ders'} - ${task.taskTypeName ?? 'Belirsiz Çalışma'}';
}

/// Saatli görevler için "09:00 • 45 dk" biçiminde bir etiket döner; saatsiz
/// görevlerde veya saat bilgisi yoksa null döner.
String? taskTimeLabel(TaskModel task) {
  if (task.scheduleType != ScheduleType.timed) return null;
  final startTime = task.startTime;
  if (startTime == null || startTime.length < 5) return null;

  final time = startTime.substring(0, 5);
  final duration = task.durationMinutes;
  return duration != null ? '$time • $duration dk' : time;
}

class _TaskCard extends StatelessWidget {
  const _TaskCard({required this.task, required this.onTap});

  final TaskModel task;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final timeLabel = taskTimeLabel(task);

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
                  Text(task.title, style: AppTextStyles.bodyLarge),
                  const SizedBox(height: 6),
                  Text(
                    taskSubjectTypeLabel(task),
                    style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                  ),
                  if (timeLabel != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      timeLabel,
                      style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                    ),
                  ],
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

enum _TaskDialogAction { complete, markIncomplete, delete, edit }

class _TaskDialogResult {
  const _TaskDialogResult.complete(this.description) : action = _TaskDialogAction.complete;
  const _TaskDialogResult.markIncomplete()
      : description = null,
        action = _TaskDialogAction.markIncomplete;
  const _TaskDialogResult.delete()
      : description = null,
        action = _TaskDialogAction.delete;
  const _TaskDialogResult.edit()
      : description = null,
        action = _TaskDialogAction.edit;

  final String? description;
  final _TaskDialogAction action;

  bool get markIncomplete => action == _TaskDialogAction.markIncomplete;
  bool get isDelete => action == _TaskDialogAction.delete;
  bool get isEdit => action == _TaskDialogAction.edit;
}

class _TaskCompletionDialog extends StatefulWidget {
  const _TaskCompletionDialog({required this.task});

  final TaskModel task;

  @override
  State<_TaskCompletionDialog> createState() => _TaskCompletionDialogState();
}

class _TaskCompletionDialogState extends State<_TaskCompletionDialog> {
  late final TextEditingController _controller;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.task.description ?? '');
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _pop(_TaskDialogResult? result) {
    FocusScope.of(context).unfocus();
    setState(() => _isSubmitting = true);
    Navigator.of(context).pop(result);
  }

  @override
  Widget build(BuildContext context) {
    final isCompleted = widget.task.isCompleted;
    final subject = taskSubjectTypeLabel(widget.task);
    final timeLabel = taskTimeLabel(widget.task);

    return AlertDialog(
      title: Row(
        children: [
          Expanded(child: Text(widget.task.title)),
          IconButton(
            onPressed: _isSubmitting ? null : () => _pop(const _TaskDialogResult.edit()),
            icon: const Icon(Icons.edit_outlined),
            tooltip: 'Görevi Düzenle',
          ),
          IconButton(
            onPressed: _isSubmitting ? null : () => _pop(const _TaskDialogResult.delete()),
            icon: const Icon(Icons.delete_outline),
            color: AppColors.error,
            tooltip: 'Görevi Sil',
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              subject,
              style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary, fontWeight: FontWeight.bold),
            ),
            if (timeLabel != null) ...[
              const SizedBox(height: 2),
              Text(
                timeLabel,
                style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
              ),
            ],
            const SizedBox(height: 6),
            Text(
              isCompleted
                  ? 'Notu güncelleyebilir veya bu görevi tamamlanmadı olarak işaretleyebilirsiniz.'
                  : 'Bu görevi tamamlamak için kısa bir not ekleyebilirsiniz.',
              style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _controller,
              label: 'Not',
              hint: 'Ör. 20 soru çözüldü',
              maxLines: 3,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isSubmitting ? null : () => _pop(null),
          child: const Text('İptal'),
        ),
        if (isCompleted)
          TextButton(
            onPressed: _isSubmitting
                ? null
                : () => _pop(const _TaskDialogResult.markIncomplete()),
            style: TextButton.styleFrom(foregroundColor: AppColors.warning),
            child: const Text('Tamamlanmadı Yap'),
          ),
        AppButton(
          label: isCompleted ? 'Kaydet' : 'Tamamla',
          isLoading: _isSubmitting,
          onPressed: _isSubmitting
              ? null
              : () => _pop(_TaskDialogResult.complete(_controller.text)),
        ),
      ],
    );
  }
}