import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_dialog.dart';
import '../../common/widgets/app_dropdown.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../common/widgets/app_text_field.dart';
import '../../data/models/goal_model.dart';
import '../../data/models/subject_model.dart';
import '../controllers/goal_controller.dart';

/// Hedef oluşturma/düzenleme ekranı.
///
/// [goal] verilmezse yeni hedef oluşturma modunda çalışır; verilirse mevcut
/// değerler önceden doldurulmuş şekilde düzenleme modunda açılır — iki akış
/// da aynı formu paylaşır, yalnızca başlık ve gönderilen istek (create/update)
/// değişir.
///
/// Hedef türü "Deneme Neti" seçildiğinde sınav türü (TYT/AYT), ders ve hedef
/// net alanları da istenir; diğer türlerde yalnızca başlık/açıklama/tarih
/// yeterlidir. "Ulaşıldı" anahtarı yalnızca düzenleme modunda gösterilir.
class GoalFormPage extends StatefulWidget {
  const GoalFormPage({super.key, this.goal});

  /// Düzenlenecek mevcut hedef. `null` ise yeni hedef oluşturulur.
  final GoalModel? goal;

  bool get isEditing => goal != null;

  @override
  State<GoalFormPage> createState() => _GoalFormPageState();
}

class _GoalFormPageState extends State<GoalFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _targetNetController = TextEditingController();

  GoalType? _selectedGoalType;
  DateTime? _selectedTargetDate;
  ExamScope? _selectedExamScope;
  int? _selectedSubjectId;
  bool _isAchieved = false;

  bool _isDirty = false;
  bool _bypassPopConfirmation = false;

  bool get _isEditing => widget.isEditing;

  @override
  void initState() {
    super.initState();

    final goal = widget.goal;
    if (goal != null) {
      _selectedGoalType = goal.goalType;
      _titleController.text = goal.title ?? '';
      _descriptionController.text = goal.description ?? '';
      _selectedTargetDate = goal.targetDate;
      _isAchieved = goal.isAchieved;
      if (goal.goalType == GoalType.denemeNeti) {
        _selectedExamScope = goal.examScope == ExamScope.none ? null : goal.examScope;
        _selectedSubjectId = goal.subjectId;
        _targetNetController.text = goal.targetNet != null ? _formatNetInput(goal.targetNet!) : '';
      }
    }

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final goalController = context.read<GoalController>();
      if (goalController.subjects.isEmpty) {
        goalController.loadReferenceData();
      }
    });

    _titleController.addListener(_markDirty);
    _descriptionController.addListener(_markDirty);
    _targetNetController.addListener(_markDirty);
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _targetNetController.dispose();
    super.dispose();
  }

  void _markDirty() {
    if (!_isDirty) {
      setState(() => _isDirty = true);
    }
  }

  List<SubjectModel> _subjectsForScope(ExamScope scope, List<SubjectModel> all) {
    return all.where((subject) => subject.category?.toLowerCase() == scope.apiValue).toList();
  }

  @override
  Widget build(BuildContext context) {
    final goalController = context.watch<GoalController>();
    final isDenemeNeti = _selectedGoalType == GoalType.denemeNeti;
    final subjectsForScope =
        isDenemeNeti && _selectedExamScope != null ? _subjectsForScope(_selectedExamScope!, goalController.subjects) : const <SubjectModel>[];
    // Seçili ders, id üzerinden anlık listeden türetilir; referans veri henüz
    // yüklenmediyse (ör. formu düzenleme modunda ilk açtığımızda) `null`
    // görünür ve liste geldiğinde otomatik olarak eşleşir.
    SubjectModel? selectedSubject;
    if (_selectedSubjectId != null) {
      for (final subject in subjectsForScope) {
        if (subject.id == _selectedSubjectId) {
          selectedSubject = subject;
          break;
        }
      }
    }

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
        appBar: AppBar(title: Text(_isEditing ? 'Hedefi Düzenle' : 'Hedef Ekle')),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  AppDropdown<GoalType>(
                    label: 'Hedef Türü',
                    hint: 'Bir hedef türü seç',
                    value: _selectedGoalType,
                    items: GoalType.values,
                    itemLabel: (type) => type.label,
                    validator: (value) => value == null ? 'Hedef türü gerekli.' : null,
                    onChanged: (type) {
                      if (type == null) return;
                      setState(() {
                        _selectedGoalType = type;
                        _isDirty = true;
                        if (type != GoalType.denemeNeti) {
                          _selectedExamScope = null;
                          _selectedSubjectId = null;
                          _targetNetController.clear();
                        }
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  _buildDateField(),
                  const SizedBox(height: 16),
                  AppTextField(
                    controller: _titleController,
                    label: 'Başlık',
                    hint: 'Ör. Paragraf sorularını hızlandır',
                    textCapitalization: TextCapitalization.sentences,
                    validator: (value) {
                      if (isDenemeNeti) return null;
                      return (value == null || value.trim().isEmpty) ? 'Başlık gerekli.' : null;
                    },
                  ),
                  const SizedBox(height: 16),
                  AppTextField(
                    controller: _descriptionController,
                    label: 'Açıklama',
                    hint: 'Opsiyonel açıklama ekle',
                    maxLines: 3,
                    textCapitalization: TextCapitalization.sentences,
                  ),
                  if (isDenemeNeti) ...[
                    const SizedBox(height: 24),
                    Text('Deneme Neti Detayları', style: AppTextStyles.h3),
                    const SizedBox(height: 12),
                    AppDropdown<ExamScope>(
                      label: 'Sınav Türü',
                      hint: 'TYT veya AYT seç',
                      value: _selectedExamScope,
                      items: const [ExamScope.tyt, ExamScope.ayt],
                      itemLabel: (scope) => scope.label,
                      validator: (value) => value == null ? 'Sınav türü gerekli.' : null,
                      onChanged: (scope) {
                        if (scope == null) return;
                        setState(() {
                          _selectedExamScope = scope;
                          _selectedSubjectId = null;
                          _isDirty = true;
                        });
                      },
                    ),
                    const SizedBox(height: 16),
                    if (_selectedExamScope != null)
                      AppDropdown<SubjectModel?>(
                        label: 'Ders',
                        hint: 'Toplam net (tüm dersler) için boş bırak',
                        value: selectedSubject,
                        items: <SubjectModel?>[null, ...subjectsForScope],
                        itemLabel: (subject) => subject?.displayName ?? 'Toplam (tüm dersler)',
                        onChanged: (subject) {
                          setState(() {
                            _selectedSubjectId = subject?.id;
                            _isDirty = true;
                          });
                        },
                      ),
                    const SizedBox(height: 16),
                    AppTextField(
                      controller: _targetNetController,
                      label: 'Hedef Net',
                      hint: 'Ör. 32.5',
                      keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                      validator: (value) {
                        if (!isDenemeNeti) return null;
                        if (value == null || value.trim().isEmpty) return 'Hedef net gerekli.';
                        final net = double.tryParse(value.trim().replaceAll(',', '.'));
                        if (net == null) return 'Geçerli bir sayı girin.';
                        if (net < 0) return 'Net negatif olamaz.';
                        return null;
                      },
                    ),
                  ],
                  if (_isEditing) ...[
                    const SizedBox(height: 24),
                    _buildAchievedSwitch(),
                  ],
                  const SizedBox(height: 28),
                  AppButton(
                    label: _isEditing ? 'Değişiklikleri Kaydet' : 'Hedefi Kaydet',
                    isLoading: goalController.isSubmitting,
                    onPressed: goalController.isSubmitting ? null : _submit,
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

  Widget _buildAchievedSwitch() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: SwitchListTile.adaptive(
        contentPadding: EdgeInsets.zero,
        title: const Text('Ulaşıldı olarak işaretle'),
        activeThumbColor: AppColors.primary,
        value: _isAchieved,
        onChanged: (value) {
          setState(() {
            _isAchieved = value;
            _isDirty = true;
          });
        },
      ),
    );
  }

  Widget _buildDateField() {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () async {
        final now = DateTime.now();
        final picked = await showDatePicker(
          context: context,
          initialDate: _selectedTargetDate ?? now,
          firstDate: DateTime(now.year - 1),
          lastDate: DateTime(now.year + 5),
        );
        if (picked != null) {
          setState(() {
            _selectedTargetDate = picked;
            _isDirty = true;
          });
        }
      },
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: 'Hedef Tarihi (opsiyonel)',
          suffixIcon: _selectedTargetDate != null
              ? IconButton(
                  icon: const Icon(Icons.clear, size: 20),
                  onPressed: () => setState(() {
                    _selectedTargetDate = null;
                    _isDirty = true;
                  }),
                )
              : null,
        ),
        child: Text(
          _selectedTargetDate != null ? _formatDate(_selectedTargetDate) : 'Tarih seç',
          style: _selectedTargetDate != null
              ? AppTextStyles.bodyLarge
              : AppTextStyles.bodyLarge.copyWith(color: AppColors.textDisabled),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final goalType = _selectedGoalType!;
    final isDenemeNeti = goalType == GoalType.denemeNeti;
    final targetNet = isDenemeNeti ? double.tryParse(_targetNetController.text.trim().replaceAll(',', '.')) : null;

    final goalController = context.read<GoalController>();
    final success = _isEditing
        ? await goalController.updateGoal(
            goalId: widget.goal!.id!,
            goalType: goalType,
            title: _titleController.text.trim(),
            description: _descriptionController.text.trim(),
            targetDate: _selectedTargetDate,
            isAchieved: _isAchieved,
            examScope: isDenemeNeti ? _selectedExamScope : ExamScope.none,
            subjectId: isDenemeNeti ? _selectedSubjectId : null,
            targetNet: targetNet,
          )
        : await goalController.createGoal(
            goalType: goalType,
            title: _titleController.text.trim(),
            description: _descriptionController.text.trim(),
            targetDate: _selectedTargetDate,
            examScope: isDenemeNeti ? _selectedExamScope ?? ExamScope.none : ExamScope.none,
            subjectId: isDenemeNeti ? _selectedSubjectId : null,
            targetNet: targetNet,
          );

    if (!mounted) return;

    if (success) {
      _bypassPopConfirmation = true;
      Navigator.of(context).pop(true);
    } else {
      AppSnackbar.showError(
        context,
        goalController.errorMessage ?? (_isEditing ? 'Hedef güncellenirken bir hata oluştu.' : 'Hedef eklenirken bir hata oluştu.'),
      );
    }
  }

  String _formatNetInput(double net) {
    return net == net.roundToDouble() ? net.toStringAsFixed(0) : net.toString();
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
