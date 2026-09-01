import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../common/widgets/app_text_field.dart';
import '../../data/models/program_model.dart';
import '../../data/models/task_model.dart';
import '../controllers/task_controller.dart';
import '../controllers/weekly_program_controller.dart';
import './task_form_page.dart';

/// Haftalık programın gün gün görev dökümü. Bir görev basılı tutulup başka bir
/// güne sürüklendiğinde, yeni saat/süre bilgisi bir dialog ile istenir;
/// kaydedilirse görev o güne, `order: 0` ile (günün başına) taşınır. Bir
/// göreve kısaca dokunulduğunda ise o görevin düzenleme sayfası açılır.
class WeeklyCalendarView extends StatefulWidget {
  const WeeklyCalendarView({super.key, required this.program});

  final ProgramModel program;

  @override
  State<WeeklyCalendarView> createState() => _WeeklyCalendarViewState();
}

class _WeeklyCalendarViewState extends State<WeeklyCalendarView> {
  final ScrollController _scrollController = ScrollController();
  final GlobalKey _scrollViewportKey = GlobalKey();
  Timer? _autoScrollTimer;
  int? _autoScrollDirection; // -1: yukarı, 1: aşağı

  static const double _autoScrollEdgeSize = 80;
  static const double _autoScrollStep = 14;

  @override
  void dispose() {
    _autoScrollTimer?.cancel();
    _scrollController.dispose();
    super.dispose();
  }

  /// Sürüklenen görev ekranın üst/alt kenarına yaklaştığında listeyi otomatik
  /// kaydırır; [SingleChildScrollView] kendiliğinden bunu yapmadığı için elle
  /// yönetiyoruz.
  void _handleDragUpdate(DragUpdateDetails details) {
    final renderBox = _scrollViewportKey.currentContext?.findRenderObject() as RenderBox?;
    if (renderBox == null || !_scrollController.hasClients) return;

    final local = renderBox.globalToLocal(details.globalPosition);
    final height = renderBox.size.height;

    int direction = 0;
    if (local.dy >= 0 && local.dy < _autoScrollEdgeSize) {
      direction = -1;
    } else if (local.dy <= height && local.dy > height - _autoScrollEdgeSize) {
      direction = 1;
    }

    if (direction == 0) {
      _stopAutoScroll();
      return;
    }

    if (_autoScrollDirection == direction) return; // zaten o yönde kayıyor

    _stopAutoScroll();
    _autoScrollDirection = direction;
    _autoScrollTimer = Timer.periodic(const Duration(milliseconds: 16), (_) {
      if (!_scrollController.hasClients) return;
      final target = (_scrollController.offset + direction * _autoScrollStep)
          .clamp(0.0, _scrollController.position.maxScrollExtent);
      _scrollController.jumpTo(target);
    });
  }

  void _stopAutoScroll() {
    _autoScrollTimer?.cancel();
    _autoScrollTimer = null;
    _autoScrollDirection = null;
  }

  @override
  Widget build(BuildContext context) {
    final weeklyController = context.watch<WeeklyProgramController>();
    // Sürükle-bırak sonrası taze veriyi göstermek için, mümkünse controller'ın
    // güncel programını kullan; yoksa bu sayfaya geçilirken verilen anlık
    // kopyaya düş.
    final program = weeklyController.currentProgram?.id == widget.program.id
        ? weeklyController.currentProgram!
        : widget.program;

    final days = List.generate(7, (index) => program.startDate!.add(Duration(days: index)));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Görevleri Düzenle'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          key: _scrollViewportKey,
          controller: _scrollController,
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Haftalık takvim', style: AppTextStyles.h3),
              const SizedBox(height: 12),
              Text(
                'Bir görevi basılı tutup başka bir güne sürükleyerek taşıyabilirsin.',
                style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
              ),
              const SizedBox(height: 16),
              ...days.map((day) => _buildDayCard(program, day)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDayCard(ProgramModel program, DateTime day) {
    final dayTasks = program.tasks.where((task) => task.date != null && _isSameDay(task.date!, day)).toList()
      ..sort((a, b) => compareTasksForDisplay(a, b, program.scheduleType));

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DragTarget<TaskModel>(
        onWillAcceptWithDetails: (details) => details.data.date == null || !_isSameDay(details.data.date!, day),
        onAcceptWithDetails: (details) => _handleTaskDropped(details.data, day, program),
        builder: (context, candidateData, rejectedData) {
          final isDropTarget = candidateData.isNotEmpty;
          return Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isDropTarget ? AppColors.primaryLight : AppColors.surface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isDropTarget ? AppColors.primary : AppColors.border,
                width: isDropTarget ? 2 : 1,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_formatDate(day), style: AppTextStyles.bodyLarge.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(height: 8),
                if (dayTasks.isEmpty)
                  Text(
                    'Bu güne ait görev yok',
                    style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                  )
                else
                  ...dayTasks.map((task) => _buildDraggableTask(task, program)),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildDraggableTask(TaskModel task, ProgramModel program) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: LongPressDraggable<TaskModel>(
        data: task,
        onDragUpdate: _handleDragUpdate,
        onDragEnd: (_) => _stopAutoScroll(),
        onDraggableCanceled: (_, _) => _stopAutoScroll(),
        feedback: Material(
          color: Colors.transparent,
          child: SizedBox(width: 220, child: _buildTaskChip(task, isDragging: true)),
        ),
        // Sürükleme sırasında da tam genişlik korunsun diye ekrandaki gerçek
        // genişliği elle veriyoruz (feedback kopyası ise sabit 220px'e sığar).
        childWhenDragging: Opacity(
          opacity: 0.35,
          child: SizedBox(width: double.infinity, child: _buildTaskChip(task)),
        ),
        // Basılı tutma sürüklemeyi başlatır; kısa dokunuş ise düzenleme
        // sayfasını açar. İkisi aynı GestureDetector zincirinde çakışmaz
        // çünkü LongPressDraggable kendi long-press tanıyıcısını kullanır.
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () => _openTaskEditPage(task, program),
          child: SizedBox(width: double.infinity, child: _buildTaskChip(task)),
        ),
      ),
    );
  }

  Future<void> _openTaskEditPage(TaskModel task, ProgramModel program) async {
    final weeklyController = context.read<WeeklyProgramController>();

    final updated = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => TaskFormPage(
          initialProgram: program,
          initialDate: task.date ?? DateTime.now(),
          task: task,
        ),
      ),
    );

    if (updated != true || !mounted) return;

    AppSnackbar.showSuccess(context, 'Görev güncellendi.');
    if (program.id != null) {
      await weeklyController.loadProgramDetails(program.id!);
    }
  }

  Widget _buildTaskChip(TaskModel task, {bool isDragging = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: isDragging ? AppColors.primary : AppColors.primaryLight,
        borderRadius: BorderRadius.circular(12),
        boxShadow: isDragging
            ? [BoxShadow(color: AppColors.textPrimary.withValues(alpha: 0.2), blurRadius: 10, offset: const Offset(0, 4))]
            : null,
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              task.title,
              overflow: TextOverflow.ellipsis,
              style: AppTextStyles.bodyMedium.copyWith(color: isDragging ? Colors.white : AppColors.primary),
            ),
          ),
          if (task.scheduleType == ScheduleType.timed) ...[
            const SizedBox(width: 8),
            Text(
              task.startTime?.substring(0, 5) ?? '-',
              style: AppTextStyles.bodySmall.copyWith(color: isDragging ? Colors.white70 : AppColors.textSecondary),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _handleTaskDropped(TaskModel task, DateTime targetDay, ProgramModel program) async {
    if (task.id == null) {
      AppSnackbar.showError(context, 'Görev henüz kaydedilmedi, lütfen tekrar deneyin.');
      return;
    }
    if (task.date != null && _isSameDay(task.date!, targetDay)) return;

    final isTimed = program.scheduleType == ScheduleType.timed;

    final result = await showDialog<_MoveTaskResult>(
      context: context,
      builder: (_) => _MoveTaskDialog(task: task, targetDay: targetDay, isTimed: isTimed),
    );

    if (result == null || !mounted) return;

    final taskController = context.read<TaskController>();
    final weeklyController = context.read<WeeklyProgramController>();

    final success = await taskController.updateTask(
      taskId: task.id!,
      date: targetDay,
      startTime: isTimed ? result.startTime : null,
      durationMinutes: isTimed ? result.durationMinutes : null,
      order: 0,
    );

    if (!mounted) return;

    if (!success) {
      AppSnackbar.showError(
        context,
        taskController.errorMessage ?? 'Görev taşınırken bir hata oluştu.',
      );
      return;
    }

    AppSnackbar.showSuccess(context, 'Görev taşındı.');
    if (program.id != null) {
      await weeklyController.loadProgramDetails(program.id!);
    }
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  String _formatDate(DateTime date) {
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
}

/// [_MoveTaskDialog]'un "Kaydet" sonucunda döndürdüğü değerler.
/// Saatsiz programlarda ikisi de null kalır.
class _MoveTaskResult {
  const _MoveTaskResult({this.startTime, this.durationMinutes});

  final String? startTime;
  final int? durationMinutes;
}

/// Bir görev başka bir güne bırakıldığında açılan, yeni saat/süre isteyen
/// onay dialog'u. "Vazgeç" iptal eder, "Kaydet" [_MoveTaskResult] döner.
class _MoveTaskDialog extends StatefulWidget {
  const _MoveTaskDialog({
    required this.task,
    required this.targetDay,
    required this.isTimed,
  });

  final TaskModel task;
  final DateTime targetDay;
  final bool isTimed;

  @override
  State<_MoveTaskDialog> createState() => _MoveTaskDialogState();
}

class _MoveTaskDialogState extends State<_MoveTaskDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _durationController;
  TimeOfDay? _selectedTime;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _selectedTime = _parseStartTime(widget.task.startTime) ?? const TimeOfDay(hour: 9, minute: 0);
    _durationController = TextEditingController(text: widget.task.durationMinutes?.toString() ?? '');
  }

  @override
  void dispose() {
    _durationController.dispose();
    super.dispose();
  }

  TimeOfDay? _parseStartTime(String? value) {
    if (value == null || value.isEmpty) return null;
    final parts = value.split(':');
    if (parts.length < 2) return null;
    final hour = int.tryParse(parts[0]);
    final minute = int.tryParse(parts[1]);
    if (hour == null || minute == null) return null;
    return TimeOfDay(hour: hour, minute: minute);
  }

  void _pop(_MoveTaskResult? result) {
    FocusScope.of(context).unfocus();
    setState(() => _isSubmitting = true);
    Navigator.of(context).pop(result);
  }

  void _submit() {
    if (!widget.isTimed) {
      _pop(const _MoveTaskResult());
      return;
    }
    if (!_formKey.currentState!.validate()) return;
    final time = _selectedTime!;
    _pop(
      _MoveTaskResult(
        startTime: '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}:00',
        durationMinutes: int.tryParse(_durationController.text),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('${widget.task.title} — ${_formatDate(widget.targetDay)}'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.isTimed
                    ? 'Görevi bu güne taşımak için yeni saat ve süreyi belirle.'
                    : 'Görev bu güne taşınacak.',
                style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
              ),
              if (widget.isTimed) ...[
                const SizedBox(height: 12),
                _buildStartTimeField(),
                const SizedBox(height: 16),
                AppTextField(
                  controller: _durationController,
                  label: 'Süre (dakika)',
                  hint: 'Ör. 45',
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    final minutes = int.tryParse(value ?? '');
                    if (minutes == null || minutes <= 0) return 'Geçerli bir süre girin.';
                    return null;
                  },
                ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isSubmitting ? null : () => _pop(null),
          child: const Text('Vazgeç'),
        ),
        AppButton(
          label: 'Kaydet',
          isLoading: _isSubmitting,
          onPressed: _isSubmitting ? null : _submit,
        ),
      ],
    );
  }

  Widget _buildStartTimeField() {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () async {
        final picked = await showTimePicker(
          context: context,
          initialTime: _selectedTime ?? const TimeOfDay(hour: 9, minute: 0),
        );
        if (picked != null) {
          setState(() => _selectedTime = picked);
        }
      },
      child: InputDecorator(
        decoration: const InputDecoration(labelText: 'Başlangıç Saati'),
        child: Text(_selectedTime!.format(context), style: AppTextStyles.bodyLarge),
      ),
    );
  }

  String _formatDate(DateTime date) {
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
}
