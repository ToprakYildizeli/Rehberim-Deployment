import 'package:flutter_test/flutter_test.dart';
import 'package:rehberim_ogrenci/data/models/program_model.dart';
import 'package:rehberim_ogrenci/data/models/student_summary_model.dart';
import 'package:rehberim_ogrenci/data/repositories/weekly_program_repository.dart';
import 'package:rehberim_ogrenci/data/services/api_exception.dart';
import 'package:rehberim_ogrenci/home/controllers/weekly_program_controller.dart';

/// Repository'nin sahtesi. `implements` kullanıyoruz ki gerçek ApiClient
/// kurmak (ve dotenv yüklemek) gerekmesin.
class _FakeRepository implements WeeklyProgramRepository {
  _FakeRepository({this.current});

  ProgramModel? current;
  ApiException? throwOnCurrent;
  List<ProgramModel> programs = const [];

  @override
  Future<ProgramModel> getCurrentProgram() async {
    final err = throwOnCurrent;
    if (err != null) throw err;
    return current!;
  }

  @override
  Future<List<ProgramModel>> getPrograms() async => programs;

  @override
  Future<ProgramModel> getProgram(int id) async => current!;

  @override
  Future<List<StudentSummaryModel>> getStudents() async => const [];

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

ProgramModel _program(int id) => ProgramModel(
      id: id,
      scheduleType: ScheduleType.timed,
      startDate: DateTime(2026, 8, 17),
      endDate: DateTime(2026, 8, 23),
    );

void main() {
  group('WeeklyProgramController', () {
    test('aktif program yoksa (404) önceki programı bellekte bırakmaz', () async {
      // Regresyon: hesap değiştirildiğinde önceki kullanıcının programı
      // ekranda kalıyordu — 404 yakalanıyor ama _currentProgram
      // sıfırlanmıyordu.
      final repo = _FakeRepository(current: _program(1));
      final controller = WeeklyProgramController(repository: repo);

      await controller.loadCurrentProgram();
      expect(controller.currentProgram?.id, 1);

      repo.throwOnCurrent =
          ApiException('Aktif program bulunamadı.', statusCode: 404);
      await controller.loadCurrentProgram();

      expect(controller.currentProgram, isNull,
          reason: 'Sunucu program yok dediğinde eski program temizlenmeli');
      expect(controller.errorMessage, isNotNull);
    });

    test('reset() bellekteki her şeyi temizler', () async {
      final repo = _FakeRepository(current: _program(2));
      repo.programs = [_program(2), _program(3)];
      final controller = WeeklyProgramController(repository: repo);

      await controller.loadCurrentProgram();
      await controller.loadPrograms();
      expect(controller.currentProgram, isNotNull);
      expect(controller.programs, hasLength(2));

      controller.reset();

      expect(controller.currentProgram, isNull);
      expect(controller.programs, isEmpty);
      expect(controller.errorMessage, isNull);
      expect(controller.isLoading, isFalse);
    });
  });
}
