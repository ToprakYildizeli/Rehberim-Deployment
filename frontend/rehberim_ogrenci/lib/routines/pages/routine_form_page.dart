import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_dialog.dart';
import '../../common/widgets/app_dropdown.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../common/widgets/app_text_field.dart';
import '../../data/models/routine_model.dart';
import '../../data/models/subject_model.dart';
import '../../data/models/task_type_model.dart';
import '../controllers/routine_controller.dart';

/// Rutin oluşturma/düzenleme ekranı.
///
/// [routine] verilmezse yeni rutin kurulur. Görevler haftanın gününe göre
/// eklenir (tarih yok); saatli rutinde başlangıç saati ve süre zorunludur.
class RoutineFormPage extends StatefulWidget {
  const RoutineFormPage({super.key, this.routine});

  final RoutineModel? routine;

  bool get isEditing => routine != null;

  @override
  State<RoutineFormPage> createState() => _RoutineFormPageState();
}

class _RoutineFormPageState extends State<RoutineFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();

  late bool _timed;
  late List<RoutineTaskModel> _tasks;
  bool _isDirty = false;
  bool _bypassPopConfirmation = false;

  @override
  void initState() {
    super.initState();
    final routine = widget.routine;
    _nameController.text = routine?.name ?? '';
    _timed = (routine?.scheduleType ?? 'timed') == 'timed';
    _tasks = List<RoutineTaskModel>.from(routine?.tasks ?? const []);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<RoutineController>().loadReferenceData();
    });

    _nameController.addListener(_markDirty);
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  void _markDirty() {
    if (!_isDirty) setState(() => _isDirty = true);
  }

  Future<void> _addTask() async {
    final controller = context.read<RoutineController>();
    final task = await showModalBottomSheet<RoutineTaskModel>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _TaskSheet(
        timed: _timed,
        subjects: controller.subjects,
        taskTypes: controller.taskTypes,
      ),
    );
    if (task != null) {
      setState(() {
        _tasks.add(task);
        _isDirty = true;
      });
    }
  }

  void _removeTask(int index) {
    setState(() {
      _tasks.removeAt(index);
      _isDirty = true;
    });
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_tasks.isEmpty) {
      AppSnackbar.showError(context, 'Rutine en az bir görev ekle.');
      return;
    }

    final controller = context.read<RoutineController>();
    final draft = RoutineModel(
      id: widget.routine?.id,
      name: _nameController.text.trim(),
      scheduleType: _timed ? 'timed' : 'untimed',
      // Yeni rutin doğrudan açık gelir; düzenlemede mevcut durum korunur.
      autoApply: widget.routine?.autoApply ?? true,
      tasks: _tasks,
    );

    final ok = await controller.saveRoutine(draft);
    if (!mounted) return;
    if (ok) {
      _bypassPopConfirmation = true;
      Navigator.of(context).pop(true);
    } else {
      AppSnackbar.showError(context, controller.errorMessage ?? 'Rutin kaydedilemedi.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<RoutineController>();

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        if (_bypassPopConfirmation || !_isDirty) {
          Navigator.of(context).pop(result);
          return;
        }
        final shouldPop = await AppDialog.confirm(
          context,
          title: 'Değişiklikler kaydedilmedi',
          message: 'Bu ekrandan çıkarsan girdiğin bilgiler kaydedilmeyecek. '
              'Yine de çıkmak istiyor musun?',
          confirmLabel: 'Çık',
          cancelLabel: 'Vazgeç',
          isDestructive: true,
        );
        if (shouldPop == true && context.mounted) {
          Navigator.of(context).pop(result);
        }
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text(widget.isEditing ? 'Rutini Düzenle' : 'Rutin Ekle'),
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  AppTextField(
                    controller: _nameController,
                    label: 'Rutin adı',
                    hint: 'Ör. Hafta içi akşam çalışması',
                    textCapitalization: TextCapitalization.sentences,
                    validator: (v) =>
                        (v == null || v.trim().isEmpty) ? 'Rutin adı gerekli.' : null,
                  ),
                  const SizedBox(height: 16),
                  SwitchListTile.adaptive(
                    value: _timed,
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Saatli rutin'),
                    subtitle: Text(
                      _timed
                          ? 'Her görev için başlangıç saati ve süre girilir'
                          : 'Görevler yalnızca güne atanır, saat yok',
                      style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                    ),
                    onChanged: (v) => setState(() {
                      _timed = v;
                      // Tip değişince saat/süre alanları anlamsızlaşır.
                      _tasks = _tasks
                          .map((t) => RoutineTaskModel(
                                id: t.id,
                                subject: t.subject,
                                subjectLabel: t.subjectLabel,
                                taskType: t.taskType,
                                taskTypeName: t.taskTypeName,
                                title: t.title,
                                weekday: t.weekday,
                                startTime: v ? t.startTime : null,
                                durationMinutes: v ? t.durationMinutes : null,
                                order: t.order,
                              ))
                          .toList();
                      _isDirty = true;
                    }),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(child: Text('Görevler', style: AppTextStyles.h3)),
                      TextButton.icon(
                        onPressed: controller.subjects.isEmpty ? null : _addTask,
                        icon: const Icon(Icons.add, size: 18),
                        label: const Text('Ekle'),
                      ),
                    ],
                  ),
                  if (_tasks.isEmpty)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 20),
                      child: Text(
                        'Henüz görev eklemedin.',
                        style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                      ),
                    )
                  else
                    ..._buildTasksByDay(),
                  const SizedBox(height: 28),
                  AppButton(
                    label: widget.isEditing ? 'Değişiklikleri Kaydet' : 'Rutini Kaydet',
                    isLoading: controller.isSubmitting,
                    onPressed: controller.isSubmitting ? null : _submit,
                    width: double.infinity,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// Görevleri güne göre gruplayıp sırayla gösterir — rutinin haftalık şekli
  /// düz bir listeden çok daha okunur oluyor.
  List<Widget> _buildTasksByDay() {
    final widgets = <Widget>[];
    for (var day = 0; day < kWeekdayNames.length; day++) {
      final indexed = <MapEntry<int, RoutineTaskModel>>[];
      for (var i = 0; i < _tasks.length; i++) {
        if (_tasks[i].weekday == day) indexed.add(MapEntry(i, _tasks[i]));
      }
      if (indexed.isEmpty) continue;
      indexed.sort((a, b) => (a.value.startTime ?? '').compareTo(b.value.startTime ?? ''));

      widgets.add(Padding(
        padding: const EdgeInsets.only(top: 12, bottom: 4),
        child: Text(
          kWeekdayNames[day],
          style: AppTextStyles.bodyMedium.copyWith(
            fontWeight: FontWeight.w700,
            color: AppColors.textSecondary,
          ),
        ),
      ));
      for (final entry in indexed) {
        final t = entry.value;
        final details = [
          if (t.displayTime.isNotEmpty) t.displayTime,
          if (t.durationMinutes != null) '${t.durationMinutes} dk',
          if (t.taskTypeName != null) t.taskTypeName!,
        ].join(' · ');
        widgets.add(Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            title: Text(t.title.isNotEmpty ? t.title : (t.subjectLabel ?? 'Görev')),
            subtitle: Text(
              [if (t.subjectLabel != null) t.subjectLabel!, if (details.isNotEmpty) details]
                  .join(' — '),
            ),
            trailing: IconButton(
              icon: const Icon(Icons.close, size: 18),
              onPressed: () => _removeTask(entry.key),
              tooltip: 'Kaldır',
            ),
          ),
        ));
      }
    }
    return widgets;
  }
}

/// Rutine tek bir görev ekleme alt sayfası.
class _TaskSheet extends StatefulWidget {
  const _TaskSheet({
    required this.timed,
    required this.subjects,
    required this.taskTypes,
  });

  final bool timed;
  final List<SubjectModel> subjects;
  final List<TaskTypeModel> taskTypes;

  @override
  State<_TaskSheet> createState() => _TaskSheetState();
}

class _TaskSheetState extends State<_TaskSheet> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _durationController = TextEditingController(text: '60');

  int _weekday = 0;
  SubjectModel? _subject;
  TaskTypeModel? _taskType;
  TimeOfDay _startTime = const TimeOfDay(hour: 9, minute: 0);

  @override
  void dispose() {
    _titleController.dispose();
    _durationController.dispose();
    super.dispose();
  }

  String _two(int n) => n.toString().padLeft(2, '0');

  void _save() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.of(context).pop(RoutineTaskModel(
      subject: _subject?.id,
      subjectLabel: _subject?.displayName,
      taskType: _taskType?.id,
      taskTypeName: _taskType?.displayName,
      title: _titleController.text.trim(),
      weekday: _weekday,
      startTime: widget.timed ? '${_two(_startTime.hour)}:${_two(_startTime.minute)}' : null,
      durationMinutes:
          widget.timed ? int.tryParse(_durationController.text.trim()) : null,
      order: 0,
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Görev Ekle', style: AppTextStyles.h3),
              const SizedBox(height: 16),
              AppDropdown<int>(
                label: 'Gün',
                value: _weekday,
                items: List<int>.generate(kWeekdayNames.length, (i) => i),
                itemLabel: weekdayName,
                onChanged: (v) => setState(() => _weekday = v ?? 0),
              ),
              const SizedBox(height: 14),
              AppDropdown<SubjectModel>(
                label: 'Ders',
                hint: 'Ders seç',
                value: _subject,
                items: widget.subjects,
                itemLabel: (s) => s.displayName,
                validator: (v) => v == null ? 'Ders gerekli.' : null,
                onChanged: (v) => setState(() => _subject = v),
              ),
              const SizedBox(height: 14),
              AppDropdown<TaskTypeModel>(
                label: 'Çalışma Metodu',
                hint: 'Metod seç',
                value: _taskType,
                items: widget.taskTypes,
                itemLabel: (t) => t.displayName,
                onChanged: (v) => setState(() => _taskType = v),
              ),
              const SizedBox(height: 14),
              AppTextField(
                controller: _titleController,
                label: 'Başlık (opsiyonel)',
                hint: 'Ör. Türev Konu Tekrarı',
                textCapitalization: TextCapitalization.sentences,
              ),
              if (widget.timed) ...[
                const SizedBox(height: 14),
                InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () async {
                    final picked =
                        await showTimePicker(context: context, initialTime: _startTime);
                    if (picked != null) setState(() => _startTime = picked);
                  },
                  child: InputDecorator(
                    decoration: const InputDecoration(labelText: 'Başlangıç saati'),
                    child: Text('${_two(_startTime.hour)}:${_two(_startTime.minute)}',
                        style: AppTextStyles.bodyLarge),
                  ),
                ),
                const SizedBox(height: 14),
                AppTextField(
                  controller: _durationController,
                  label: 'Süre (dakika)',
                  keyboardType: TextInputType.number,
                  validator: (v) {
                    final parsed = int.tryParse((v ?? '').trim());
                    if (parsed == null) return 'Süreyi dakika olarak gir.';
                    if (parsed <= 0) return 'Süre pozitif olmalı.';
                    return null;
                  },
                ),
              ],
              const SizedBox(height: 22),
              AppButton(label: 'Ekle', onPressed: _save, width: double.infinity),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}
