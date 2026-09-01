import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_dialog.dart';
import '../../common/widgets/app_dropdown.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../common/widgets/app_text_field.dart';
import '../../data/models/exam_model.dart';
import '../../data/models/subject_model.dart';
import '../../data/models/subject_net_model.dart';
import '../controllers/exam_controller.dart';
import 'practice_exams_page.dart' show formatExamDate, formatNet;

/// Deneme sonucu oluşturma/düzenleme ekranı.
///
/// [exam] verilmezse yeni deneme oluşturma modunda çalışır; verilirse mevcut
/// değerler önceden doldurulmuş şekilde düzenleme modunda açılır — iki akış
/// da aynı formu paylaşır, yalnızca başlık ve gönderilen istek (create/update)
/// değişir.
///
/// Sınav türü (TYT/AYT) seçildikten sonra o türe ait dersler (ör. "TYT ..."
/// önekli dersler) listelenir ve her biri için **doğru** ve **yanlış** alanı
/// gösterilir. Net (`doğru - yanlış/4`) ve boş (`soru sayısı - doğru - yanlış`)
/// sunucuda hesaplanır; burada yalnızca önizleme olarak gösterilir. İkisi de boş
/// bırakılan dersler sunucuya gönderilmez.
class ExamFormPage extends StatefulWidget {
  const ExamFormPage({super.key, this.exam});

  /// Düzenlenecek mevcut deneme. `null` ise yeni deneme oluşturulur.
  final ExamModel? exam;

  bool get isEditing => exam != null;

  @override
  State<ExamFormPage> createState() => _ExamFormPageState();
}

class _ExamFormPageState extends State<ExamFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();

  ExamType? _selectedExamType;
  DateTime? _selectedDate;

  /// Ders id'sine göre doğru/yanlış giriş kontrolcüleri. Sınav türü
  /// değiştiğinde o türe ait olmayanlar temizlenir.
  final Map<int, TextEditingController> _correctControllers = {};
  final Map<int, TextEditingController> _wrongControllers = {};

  bool _isDirty = false;
  bool _bypassPopConfirmation = false;

  bool get _isEditing => widget.isEditing;

  @override
  void initState() {
    super.initState();

    final exam = widget.exam;
    if (exam != null) {
      _titleController.text = exam.name ?? '';
      _selectedExamType = exam.examType;
      _selectedDate = exam.examDate;
      for (final subjectNet in exam.subjectNets) {
        final subjectId = subjectNet.subject;
        if (subjectId == null) continue;
        _correctControllers[subjectId] = TextEditingController(text: '${subjectNet.correct}');
        _wrongControllers[subjectId] = TextEditingController(text: '${subjectNet.wrong}');
      }
    }

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final examController = context.read<ExamController>();
      if (examController.subjects.isEmpty) {
        examController.loadReferenceData();
      }
    });

    // Prefill sırasında henüz dirty sayılmasın diye listener'lar en sonda
    // eklenir.
    _titleController.addListener(_markDirty);
    for (final controller in [..._correctControllers.values, ..._wrongControllers.values]) {
      controller.addListener(_markDirty);
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    for (final controller in [..._correctControllers.values, ..._wrongControllers.values]) {
      controller.dispose();
    }
    super.dispose();
  }

  void _markDirty() {
    if (!_isDirty) {
      setState(() => _isDirty = true);
    }
  }

  List<SubjectModel> _subjectsForType(ExamType type, List<SubjectModel> all) {
    return all.where((subject) => subject.category?.toLowerCase() == type.apiValue).toList();
  }

  void _syncNetControllers(List<SubjectModel> subjects) {
    final currentIds = subjects.map((s) => s.id).whereType<int>().toSet();

    for (final map in [_correctControllers, _wrongControllers]) {
      map.removeWhere((id, controller) {
        if (currentIds.contains(id)) return false;
        controller.dispose();
        return true;
      });
      for (final id in currentIds) {
        map.putIfAbsent(id, () => TextEditingController()..addListener(_markDirty));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final examController = context.watch<ExamController>();
    final subjectsForType =
        _selectedExamType != null ? _subjectsForType(_selectedExamType!, examController.subjects) : const <SubjectModel>[];
    _syncNetControllers(subjectsForType);

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
        appBar: AppBar(title: Text(_isEditing ? 'Denemeyi Düzenle' : 'Deneme Ekle')),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  AppDropdown<ExamType>(
                    label: 'Sınav Türü',
                    hint: 'TYT veya AYT seç',
                    value: _selectedExamType,
                    items: const [ExamType.tyt, ExamType.ayt],
                    itemLabel: (type) => type.label,
                    validator: (value) => value == null ? 'Sınav türü gerekli.' : null,
                    onChanged: (type) {
                      if (type == null) return;
                      setState(() {
                        _selectedExamType = type;
                        _isDirty = true;
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  _buildDateField(),
                  const SizedBox(height: 16),
                  AppTextField(
                    controller: _titleController,
                    label: 'Başlık',
                    hint: 'Ör. 3D Yayınları TYT Genel Deneme 5',
                    textCapitalization: TextCapitalization.sentences,
                    validator: (value) => (value == null || value.trim().isEmpty) ? 'Başlık gerekli.' : null,
                  ),
                  if (_selectedExamType != null) ...[
                    const SizedBox(height: 24),
                    Text('Ders Sonuçları', style: AppTextStyles.h3),
                    const SizedBox(height: 4),
                    Text(
                      'İstediğin dersler için doğru ve yanlış sayısını gir; net otomatik '
                      'hesaplanır. Boş bıraktığın dersler kaydedilmez.',
                      style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 12),
                    if (examController.isLoading && subjectsForType.isEmpty)
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 12),
                        child: Center(child: CircularProgressIndicator()),
                      )
                    else if (subjectsForType.isEmpty)
                      Text(
                        'Bu sınav türü için tanımlı ders bulunamadı.',
                        style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                      )
                    else
                      ..._buildNetFields(subjectsForType),
                  ],
                  const SizedBox(height: 28),
                  AppButton(
                    label: _isEditing ? 'Değişiklikleri Kaydet' : 'Denemeyi Kaydet',
                    isLoading: examController.isSubmitting,
                    onPressed: examController.isSubmitting ? null : _submit,
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

  List<Widget> _buildNetFields(List<SubjectModel> subjects) {
    final fields = <Widget>[];
    for (final subject in subjects) {
      final id = subject.id;
      if (id == null) continue;
      fields.add(
        Padding(
          padding: const EdgeInsets.only(bottom: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(child: Text(subject.displayName, style: AppTextStyles.bodyLarge)),
                  Text(
                    _summaryFor(subject),
                    style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: AppTextField(
                      controller: _correctControllers[id]!,
                      label: 'Doğru',
                      keyboardType: TextInputType.number,
                      onChanged: (_) => setState(() {}),
                      validator: (value) => _validateCount(value, subject, isCorrect: true),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: AppTextField(
                      controller: _wrongControllers[id]!,
                      label: 'Yanlış',
                      keyboardType: TextInputType.number,
                      onChanged: (_) => setState(() {}),
                      validator: (value) => _validateCount(value, subject, isCorrect: false),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    }
    return fields;
  }

  /// Girilen sayıyı okur. Boş ya da geçersizse `null` döner.
  int? _readCount(TextEditingController? controller) {
    final raw = controller?.text.trim() ?? '';
    if (raw.isEmpty) return null;
    return int.tryParse(raw);
  }

  /// Ders satırının sağındaki önizleme: "net 32.5 · boş 6".
  /// Sunucunun hesabının aynısı — kaydetmeden ne olacağını gösterir.
  String _summaryFor(SubjectModel subject) {
    final correct = _readCount(_correctControllers[subject.id]);
    final wrong = _readCount(_wrongControllers[subject.id]);
    if (correct == null && wrong == null) return '';
    final net = (correct ?? 0) - (wrong ?? 0) / 4;
    final buffer = StringBuffer('net ${formatNet(net)}');
    if (subject.questionCount > 0) {
      final blank = subject.questionCount - (correct ?? 0) - (wrong ?? 0);
      if (blank >= 0) buffer.write(' · boş $blank');
    }
    return buffer.toString();
  }

  /// Doğru/yanlış alanının doğrulaması. Sunucudaki kuralın aynısını önden
  /// uygular: negatif olamaz ve doğru+yanlış dersin soru sayısını aşamaz.
  String? _validateCount(String? value, SubjectModel subject, {required bool isCorrect}) {
    final raw = value?.trim() ?? '';
    if (raw.isNotEmpty) {
      final parsed = int.tryParse(raw);
      if (parsed == null) return 'Tam sayı girin.';
      if (parsed < 0) return 'Negatif olamaz.';
    }

    final correct = _readCount(_correctControllers[subject.id]) ?? 0;
    final wrong = _readCount(_wrongControllers[subject.id]) ?? 0;
    final limit = subject.questionCount;
    if (limit > 0 && correct + wrong > limit) {
      return isCorrect ? 'Doğru + yanlış en fazla $limit olabilir.' : 'En fazla $limit soru var.';
    }
    return null;
  }

  Widget _buildDateField() {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () async {
        final now = DateTime.now();
        final picked = await showDatePicker(
          context: context,
          initialDate: _selectedDate ?? now,
          firstDate: DateTime(now.year - 3),
          lastDate: DateTime(now.year + 1),
        );
        if (picked != null) {
          setState(() {
            _selectedDate = picked;
            _isDirty = true;
          });
        }
      },
      child: InputDecorator(
        decoration: const InputDecoration(labelText: 'Tarih'),
        child: Text(
          _selectedDate != null ? formatExamDate(_selectedDate) : 'Tarih seç',
          style: _selectedDate != null
              ? AppTextStyles.bodyLarge
              : AppTextStyles.bodyLarge.copyWith(color: AppColors.textDisabled),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (_selectedDate == null) {
      AppSnackbar.showError(context, 'Lütfen deneme tarihini seç.');
      return;
    }
    if (!_formKey.currentState!.validate()) return;

    // Doğru ve yanlışın ikisi de boş bırakılan dersler gönderilmez; biri
    // doluysa diğeri 0 sayılır.
    final subjectNets = <SubjectNetModel>[];
    for (final subjectId in _correctControllers.keys) {
      final correct = _readCount(_correctControllers[subjectId]);
      final wrong = _readCount(_wrongControllers[subjectId]);
      if (correct == null && wrong == null) continue;
      subjectNets.add(SubjectNetModel(
        subject: subjectId,
        correct: correct ?? 0,
        wrong: wrong ?? 0,
      ));
    }

    final examController = context.read<ExamController>();
    final success = _isEditing
        ? await examController.updateExam(
            examId: widget.exam!.id!,
            examDate: _selectedDate!,
            examType: _selectedExamType!,
            name: _titleController.text.trim(),
            subjectNets: subjectNets,
          )
        : await examController.createExam(
            examDate: _selectedDate!,
            subjectNets: subjectNets,
            examType: _selectedExamType!,
            name: _titleController.text.trim(),
          );

    if (!mounted) return;

    if (success) {
      _bypassPopConfirmation = true;
      Navigator.of(context).pop(true);
    } else {
      AppSnackbar.showError(
        context,
        examController.errorMessage ?? (_isEditing ? 'Deneme güncellenirken bir hata oluştu.' : 'Deneme eklenirken bir hata oluştu.'),
      );
    }
  }
}
