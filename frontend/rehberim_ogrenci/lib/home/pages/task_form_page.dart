import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_dialog.dart';
import '../../common/widgets/app_dropdown.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../common/widgets/app_text_field.dart';
import '../../data/models/program_model.dart';
import '../../data/models/subject_model.dart';
import '../../data/models/task_model.dart';
import '../../data/models/task_type_model.dart';
import '../controllers/task_controller.dart';
import '../controllers/weekly_program_controller.dart';

/// Görev oluşturma/düzenleme ekranı.
///
/// [task] verilmezse yeni görev oluşturma modunda çalışır; verilirse mevcut
/// değerler önceden doldurulmuş şekilde düzenleme modunda açılır — iki akış
/// da aynı formu paylaşır, yalnızca başlık ve gönderilen istek (create/update)
/// değişir.
///
/// Program ve gün, çağrıldığı yerden (ör. ana ekranda o an görüntülenen
/// program/gün, ya da düzenlenen görevin kendi programı/günü) varsayılan
/// olarak gelir; oluşturma modunda kullanıcı dropdown'lardan değiştirebilir.
/// Düzenleme modunda program sabittir (backend görevin programını
/// değiştirmeyi desteklemiyor) ama gün, ders, metod, başlık, açıklama ve
/// saat/süre bilgileri düzenlenebilir. Program "saatli" ise başlangıç saati
/// ve süre zorunludur, "saatsiz" ise bu alanlar hiç gösterilmez ve sunucuya
/// gönderilmez.
class TaskFormPage extends StatefulWidget {
  const TaskFormPage({
    super.key,
    required this.initialProgram,
    required this.initialDate,
    this.task,
  });

  final ProgramModel initialProgram;
  final DateTime initialDate;

  /// Düzenlenecek mevcut görev. `null` ise yeni görev oluşturulur.
  final TaskModel? task;

  bool get isEditing => task != null;

  @override
  State<TaskFormPage> createState() => _TaskFormPageState();
}

class _TaskFormPageState extends State<TaskFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _durationController = TextEditingController();

  late ProgramModel _selectedProgram;
  late DateTime _selectedDate;
  SubjectModel? _selectedSubject;
  TaskTypeModel? _selectedTaskType;
  TimeOfDay? _selectedStartTime;

  bool _isDirty = false;
  bool _bypassPopConfirmation = false;

  bool get _isEditing => widget.isEditing;

  @override
  void initState() {
    super.initState();
    _selectedProgram = widget.initialProgram;

    final task = widget.task;
    if (task != null) {
      _titleController.text = task.title;
      _descriptionController.text = task.description ?? '';
      _durationController.text = task.durationMinutes?.toString() ?? '';
      _selectedStartTime = _parseStartTime(task.startTime);
      _selectedDate = _programDays.firstWhere(
        (day) => task.date != null && _isSameDay(day, task.date!),
        orElse: () => _programDays.first,
      );
    } else {
      _selectedDate = _programDays.firstWhere(
        (day) => _isSameDay(day, widget.initialDate),
        orElse: () => _programDays.first,
      );
    }

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final weeklyController = context.read<WeeklyProgramController>();
      if (weeklyController.programs.isEmpty) {
        weeklyController.loadPrograms();
      }
      final taskController = context.read<TaskController>();
      if (taskController.subjects.isEmpty || taskController.taskTypes.isEmpty) {
        taskController.loadReferenceData();
      }
    });

    // Prefill sırasında henüz dirty sayılmasın diye listener'lar en sonda
    // eklenir.
    _titleController.addListener(_markDirty);
    _descriptionController.addListener(_markDirty);
    _durationController.addListener(_markDirty);
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _durationController.dispose();
    super.dispose();
  }

  void _markDirty() {
    if (!_isDirty) {
      setState(() => _isDirty = true);
    }
  }

  List<DateTime> get _programDays {
    final start = _selectedProgram.startDate;
    if (start == null) return [widget.initialDate];
    return List.generate(7, (i) => start.add(Duration(days: i)));
  }

  bool get _isTimed => _selectedProgram.scheduleType == ScheduleType.timed;

  /// Görevin ders/metodu, referans listeleri (subjects/taskTypes) yüklendikten
  /// sonra id eşleşmesiyle bulunur — dropdown değeri, items listesindeki
  /// nesneyle aynı örnek (instance) olmalıdır.
  void _syncSelectedReferences(TaskController taskController) {
    final task = widget.task;
    if (task == null) return;

    if (_selectedSubject == null && task.subject != null) {
      for (final subject in taskController.subjects) {
        if (subject.id == task.subject) {
          _selectedSubject = subject;
          break;
        }
      }
    }
    if (_selectedTaskType == null && task.taskType != null) {
      for (final taskType in taskController.taskTypes) {
        if (taskType.id == task.taskType) {
          _selectedTaskType = taskType;
          break;
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final weeklyController = context.watch<WeeklyProgramController>();
    final taskController = context.watch<TaskController>();
    _syncSelectedReferences(taskController);

    // Seçili program her zaman listenin bir parçası olsun (henüz `programs`
    // yüklenmemiş olsa bile dropdown boş kalmasın).
    final programs = <ProgramModel>[
      _selectedProgram,
      ...weeklyController.programs.where((p) => p.id != _selectedProgram.id),
    ];

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
          message: 'Bu ekrandan çıkarsan girdiğin bilgiler kaydedilmeyecek. Yine de çıkmak istiyor musun?',
          confirmLabel: 'Çık',
          cancelLabel: 'Vazgeç',
          isDestructive: true,
        );
        if (shouldPop == true && context.mounted) {
          Navigator.of(context).pop(result);
        }
      },
      child: Scaffold(
        appBar: AppBar(title: Text(_isEditing ? 'Görevi Düzenle' : 'Görev Ekle')),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  AppDropdown<ProgramModel>(
                    label: 'Program',
                    value: _selectedProgram,
                    items: programs,
                    itemLabel: (p) => '${_formatDate(p.startDate)} - ${_formatDate(p.endDate)}',
                    enabled: !_isEditing,
                    onChanged: (program) {
                      if (program == null || program.id == _selectedProgram.id) return;
                      setState(() {
                        _selectedProgram = program;
                        _isDirty = true;
                        final days = _programDays;
                        if (!days.any((d) => _isSameDay(d, _selectedDate))) {
                          _selectedDate = days.first;
                        }
                        if (!_isTimed) {
                          _selectedStartTime = null;
                          _durationController.clear();
                        }
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  AppDropdown<DateTime>(
                    label: 'Gün',
                    value: _selectedDate,
                    items: _programDays,
                    itemLabel: _formatDate,
                    onChanged: (date) {
                      if (date == null) return;
                      setState(() {
                        _selectedDate = date;
                        _isDirty = true;
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  AppDropdown<SubjectModel>(
                    label: 'Ders',
                    hint: 'Ders seç (opsiyonel)',
                    value: _selectedSubject,
                    items: taskController.subjects,
                    itemLabel: (s) => s.displayName,
                    onChanged: (subject) => setState(() {
                      _selectedSubject = subject;
                      _isDirty = true;
                    }),
                  ),
                  const SizedBox(height: 16),
                  AppDropdown<TaskTypeModel>(
                    label: 'Çalışma Metodu',
                    hint: 'Metod seç (opsiyonel)',
                    value: _selectedTaskType,
                    items: taskController.taskTypes,
                    itemLabel: (t) => t.displayName,
                    onChanged: (taskType) => setState(() {
                      _selectedTaskType = taskType;
                      _isDirty = true;
                    }),
                  ),
                  const SizedBox(height: 16),
                  AppTextField(
                    controller: _titleController,
                    label: 'Başlık',
                    hint: 'Ör. Türev Konu Tekrarı',
                    textCapitalization: TextCapitalization.sentences,
                    validator: (value) => (value == null || value.trim().isEmpty) ? 'Başlık gerekli.' : null,
                  ),
                  const SizedBox(height: 16),
                  AppTextField(
                    controller: _descriptionController,
                    label: 'Açıklama',
                    hint: 'Opsiyonel',
                    maxLines: 3,
                    textCapitalization: TextCapitalization.sentences,
                  ),
                  if (_isTimed) ...[
                    const SizedBox(height: 16),
                    _buildStartTimeField(),
                    const SizedBox(height: 16),
                    AppTextField(
                      controller: _durationController,
                      label: 'Süre (dakika)',
                      hint: 'Ör. 45',
                      keyboardType: TextInputType.number,
                      validator: (value) {
                        if (!_isTimed) return null;
                        final minutes = int.tryParse(value ?? '');
                        if (minutes == null || minutes <= 0) {
                          return 'Geçerli bir süre girin.';
                        }
                        return null;
                      },
                    ),
                  ],
                  const SizedBox(height: 28),
                  AppButton(
                    label: _isEditing ? 'Değişiklikleri Kaydet' : 'Görevi Kaydet',
                    isLoading: taskController.isSubmitting,
                    onPressed: taskController.isSubmitting ? null : _submit,
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

  Widget _buildStartTimeField() {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () async {
        final picked = await showTimePicker(
          context: context,
          initialTime: _selectedStartTime ?? const TimeOfDay(hour: 9, minute: 0),
        );
        if (picked != null) {
          setState(() {
            _selectedStartTime = picked;
            _isDirty = true;
          });
        }
      },
      child: InputDecorator(
        decoration: const InputDecoration(labelText: 'Başlangıç Saati'),
        child: Text(
          _selectedStartTime != null ? _selectedStartTime!.format(context) : 'Saat seç',
          style: _selectedStartTime != null
              ? AppTextStyles.bodyLarge
              : AppTextStyles.bodyLarge.copyWith(color: AppColors.textDisabled),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (_selectedProgram.id == null) return;
    if (_isTimed && _selectedStartTime == null) {
      AppSnackbar.showError(context, 'Saatli program için başlangıç saati seçmelisin.');
      return;
    }
    if (!_formKey.currentState!.validate()) return;

    final taskController = context.read<TaskController>();
    final success = _isEditing
        ? await taskController.updateTask(
            taskId: widget.task!.id!,
            title: _titleController.text.trim(),
            date: _selectedDate,
            subjectId: _selectedSubject?.id,
            taskTypeId: _selectedTaskType?.id,
            description: _descriptionController.text.trim().isEmpty ? null : _descriptionController.text.trim(),
            startTime: _isTimed ? _formatTimeOfDay(_selectedStartTime!) : null,
            durationMinutes: _isTimed ? int.tryParse(_durationController.text) : null,
          )
        : await taskController.createTask(
            programId: _selectedProgram.id!,
            title: _titleController.text.trim(),
            date: _selectedDate,
            scheduleType: _selectedProgram.scheduleType,
            subjectId: _selectedSubject?.id,
            taskTypeId: _selectedTaskType?.id,
            description: _descriptionController.text.trim().isEmpty ? null : _descriptionController.text.trim(),
            startTime: _isTimed ? _formatTimeOfDay(_selectedStartTime!) : null,
            durationMinutes: _isTimed ? int.tryParse(_durationController.text) : null,
            // `order` bilinçli olarak gönderilmiyor: backend (TaskSerializer.create)
            // order verilmezse görevi günün sonuna otomatik ekliyor. Belirli bir
            // pozisyon gönderilseydi backend o pozisyondaki ve sonrasındaki
            // görevleri otomatik olarak bir kaydırıyor (0-based sıralama).
          );

    if (!mounted) return;

    if (success) {
      _bypassPopConfirmation = true;
      Navigator.of(context).pop(true);
    } else {
      AppSnackbar.showError(
        context,
        taskController.errorMessage ?? (_isEditing ? 'Görev güncellenirken bir hata oluştu.' : 'Görev eklenirken bir hata oluştu.'),
      );
    }
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

  String _formatTimeOfDay(TimeOfDay time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}:00';
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  String _formatDate(DateTime? date) {
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
}
