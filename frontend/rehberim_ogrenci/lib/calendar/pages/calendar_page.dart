import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../common/theme/app_colors.dart';
import '../../common/theme/app_text_styles.dart';
import '../../common/widgets/app_button.dart';
import '../../common/widgets/app_loading_indicator.dart';
import '../../common/widgets/app_snackbar.dart';
import '../../common/widgets/empty_state_widget.dart';
import '../../data/models/calendar_event_model.dart';
import '../../data/models/goal_model.dart';
import '../../goals/controllers/goal_controller.dart';
import '../../goals/pages/goal_detail_page.dart';
import '../../goals/pages/goal_form_page.dart';
import '../controllers/calendar_controller.dart';

/// Takvim sekmesi: öğrencinin hedeflerini ve rehberinin takvim etkinliklerini
/// bir arada gösterir (Denemeler sekmesiyle aynı düzen). "Hedefler" ve
/// "Buluşmalar" iki ayrı bölüm halinde listelenir (bkz. Profil sayfasındaki
/// "Hesap" başlığı ile aynı stil); hiçbiri yoksa boş durum mesajı, en altta
/// her zaman "Hedef Ekle" butonu bulunur.
///
/// Takvim etkinlikleri salt-okunurdur (bkz. `CalendarRepository`) — kartlara
/// dokunma etkileşimi yoktur, yalnızca görüntülenir.
class CalendarPage extends StatefulWidget {
  const CalendarPage({super.key});

  @override
  State<CalendarPage> createState() => _CalendarPageState();
}

class _CalendarPageState extends State<CalendarPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GoalController>().loadGoals();
      context.read<CalendarController>().loadEvents();
    });
  }

  @override
  Widget build(BuildContext context) {
    final goalController = context.watch<GoalController>();
    final calendarController = context.watch<CalendarController>();

    final goals = _sortedGoals(goalController.goals);
    final events = _sortedEvents(calendarController.events);
    final hasContent = goals.isNotEmpty || events.isNotEmpty;

    final isLoading = (goalController.isLoading || calendarController.isLoading) && !hasContent;

    return Scaffold(
      appBar: AppBar(title: const Text('Takvim')),
      body: SafeArea(
        child: isLoading
            ? const AppLoadingIndicator(message: 'Hedefler ve etkinlikler yükleniyor...')
            : Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
                child: Column(
                  children: [
                    Expanded(
                      child: hasContent
                          ? ListView(
                              children: [
                                Text('Hedefler', style: AppTextStyles.h3),
                                const SizedBox(height: 12),
                                if (goals.isEmpty)
                                  _SectionEmptyMessage(message: 'Henüz eklenmiş bir hedefin yok.')
                                else
                                  ...goals.map(
                                    (goal) => Padding(
                                      padding: const EdgeInsets.only(bottom: 10),
                                      child: _GoalCard(
                                        goal: goal,
                                        onTap: () => _openGoalDetail(goal),
                                      ),
                                    ),
                                  ),
                                const SizedBox(height: 28),
                                Text('Buluşmalar', style: AppTextStyles.h3),
                                const SizedBox(height: 12),
                                if (events.isEmpty)
                                  _SectionEmptyMessage(message: 'Planlanmış bir buluşman bulunmuyor.')
                                else
                                  ...events.map(
                                    (event) => Padding(
                                      padding: const EdgeInsets.only(bottom: 10),
                                      child: _CalendarEventCard(event: event),
                                    ),
                                  ),
                              ],
                            )
                          : const EmptyStateWidget(
                              icon: Icons.calendar_today_outlined,
                              title: 'Henüz hedef veya etkinlik yok',
                              message: 'Şu an için eklenmiş bir hedefin veya takvim '
                                  'etkinliğin bulunmuyor.',
                            ),
                    ),
                    const SizedBox(height: 16),
                    AppButton(
                      label: 'Hedef Ekle',
                      icon: Icons.add_circle_outline,
                      width: double.infinity,
                      onPressed: _handleAddGoal,
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  /// Tamamlanmamış hedefler önce, tamamlananlar en altta gösterilir; her iki
  /// grup da kendi içinde aynı kurala göre sıralanır: tarihi olanlar tarihe
  /// göre artan sırada en başta, tarihsizler en sonda (girildikleri sırayla).
  List<GoalModel> _sortedGoals(List<GoalModel> goals) {
    final incomplete = goals.where((goal) => !goal.isAchieved).toList();
    final complete = goals.where((goal) => goal.isAchieved).toList();
    return [..._sortByDate(incomplete), ..._sortByDate(complete)];
  }

  List<GoalModel> _sortByDate(List<GoalModel> goals) {
    final withDate = goals.where((goal) => goal.targetDate != null).toList()
      ..sort((a, b) => a.targetDate!.compareTo(b.targetDate!));
    final withoutDate = goals.where((goal) => goal.targetDate == null).toList();
    return [...withDate, ...withoutDate];
  }

  /// Geçmemiş etkinlikler önce, geçmiş olanlar en altta gösterilir; her iki
  /// grup da kendi içinde backend'den gelen sırayı (tarih/saat artan) korur.
  List<CalendarEventModel> _sortedEvents(List<CalendarEventModel> events) {
    final upcoming = <CalendarEventModel>[];
    final past = <CalendarEventModel>[];
    for (final event in events) {
      (isEventPast(event) ? past : upcoming).add(event);
    }
    return [...upcoming, ...past];
  }

  Future<void> _handleAddGoal() async {
    final created = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const GoalFormPage()),
    );

    if (created != true || !mounted) return;

    AppSnackbar.showSuccess(context, 'Hedef başarıyla eklendi.');
    await context.read<GoalController>().loadGoals();
  }

  Future<void> _openGoalDetail(GoalModel goal) async {
    // Detay sayfası düzenleme/silme yapılırsa `true` ile döner; bu durumda
    // listeyi güncel verilerle yeniden yüklüyoruz.
    final changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => GoalDetailPage(goal: goal)),
    );

    if (changed != true || !mounted) return;
    AppSnackbar.showSuccess(context, 'İşlem başarıyla tamamlandı.');
    await context.read<GoalController>().loadGoals();
  }
}

class _SectionEmptyMessage extends StatelessWidget {
  const _SectionEmptyMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Text(
      message,
      style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
    );
  }
}

class _GoalCard extends StatelessWidget {
  const _GoalCard({required this.goal, required this.onTap});

  final GoalModel goal;
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
                  Row(
                    children: [
                      if (goal.isAchieved) ...[
                        const Icon(Icons.check_circle_rounded, size: 18, color: AppColors.success),
                        const SizedBox(width: 6),
                      ],
                      Expanded(child: Text(goalTitle(goal), style: AppTextStyles.bodyLarge)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    goal.goalType.label,
                    style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                  ),
                  if (goal.targetDate != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      formatCalendarDate(goal.targetDate),
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

class _CalendarEventCard extends StatelessWidget {
  const _CalendarEventCard({required this.event});

  final CalendarEventModel event;

  @override
  Widget build(BuildContext context) {
    final isPast = isEventPast(event);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(event.title?.trim().isNotEmpty == true ? event.title!.trim() : 'Buluşma', style: AppTextStyles.bodyLarge),
                const SizedBox(height: 6),
                Text(
                  formatCalendarDate(event.date),
                  style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                ),
                if (event.isAllDay)
                  Text(
                    'Tüm gün',
                    style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                  )
                else if (event.startTime != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    event.endTime != null
                        ? '${formatCalendarTime(event.startTime)} - ${formatCalendarTime(event.endTime)}'
                        : formatCalendarTime(event.startTime),
                    style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                  ),
                ],
              ],
            ),
          ),
          if (isPast) ...[
            const SizedBox(width: 12),
            const _PastEventBadge(),
          ],
        ],
      ),
    );
  }
}

class _PastEventBadge extends StatelessWidget {
  const _PastEventBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.history_rounded, size: 14, color: AppColors.textSecondary),
          const SizedBox(width: 4),
          Text(
            'Geçti',
            style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary),
          ),
        ],
      ),
    );
  }
}

/// Bir hedefin başlığı boşsa backend'in ürettiği etikete, o da yoksa hedef
/// türüne düşer. Kart ve (ileride eklenecek) detay görünümü aynı mantığı
/// paylaşabilir.
String goalTitle(GoalModel goal) {
  if (goal.title?.trim().isNotEmpty == true) return goal.title!.trim();
  if (goal.label?.trim().isNotEmpty == true) return goal.label!.trim();
  return goal.goalType.label;
}

String formatCalendarDate(DateTime? date) {
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

/// Backend saatleri "HH:MM:SS" biçiminde döner; gösterimde saniye kısmı
/// atılır.
String formatCalendarTime(String? time) {
  if (time == null || time.length < 5) return time ?? '-';
  return time.substring(0, 5);
}

/// Bir etkinliğin geçmişte kalıp kalmadığını belirler:
/// - Bitiş saati varsa, o saat (tarihiyle birlikte) şu andan önceyse geçmiştir.
/// - Bitiş saati yoksa (saatsiz ya da yalnızca başlangıç saatli etkinlik),
///   günün kendisi bugünden önceyse geçmiş sayılır.
bool isEventPast(CalendarEventModel event) {
  final date = event.date;
  if (date == null) return false;

  final now = DateTime.now();
  final endDateTime = _combineDateAndTime(date, event.endTime);
  if (endDateTime != null) return endDateTime.isBefore(now);

  final today = DateTime(now.year, now.month, now.day);
  final eventDay = DateTime(date.year, date.month, date.day);
  return eventDay.isBefore(today);
}

DateTime? _combineDateAndTime(DateTime date, String? time) {
  if (time == null) return null;
  final parts = time.split(':');
  if (parts.length < 2) return null;
  final hour = int.tryParse(parts[0]);
  final minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) return null;
  return DateTime(date.year, date.month, date.day, hour, minute);
}
