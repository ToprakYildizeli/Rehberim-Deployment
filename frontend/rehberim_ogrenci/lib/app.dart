import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'auth/controllers/auth_controller.dart';
import 'calendar/controllers/calendar_controller.dart';
import 'common/constants/app_constants.dart';
import 'common/theme/app_theme.dart';
import 'data/repositories/auth_repository.dart';
import 'data/repositories/calendar_repository.dart';
import 'data/repositories/exam_repository.dart';
import 'data/repositories/goal_repository.dart';
import 'data/repositories/routine_repository.dart';
import 'data/repositories/task_repository.dart';
import 'data/repositories/weekly_program_repository.dart';
import 'data/services/api_client.dart';
import 'data/services/token_storage_service.dart';
import 'goals/controllers/goal_controller.dart';
import 'home/controllers/task_controller.dart';
import 'home/controllers/weekly_program_controller.dart';
import 'navigation/auth_gate.dart';
import 'practice_exams/controllers/exam_controller.dart';
import 'routines/controllers/routine_controller.dart';

/// Uygulamanın kök widget'ı. Bağımlılıkları (API client, repository,
/// controller) kurar ve bunları [Provider] aracılığıyla widget ağacına sağlar.
class SinavMentorApp extends StatefulWidget {
  const SinavMentorApp({super.key});

  @override
  State<SinavMentorApp> createState() => _SinavMentorAppState();
}

class _SinavMentorAppState extends State<SinavMentorApp> {
  final GlobalKey<NavigatorState> _navigatorKey = GlobalKey<NavigatorState>();

  late final TokenStorageService _tokenStorage;
  late final ApiClient _apiClient;
  late final AuthRepository _authRepository;
  late final AuthController _authController;
  late final WeeklyProgramRepository _weeklyProgramRepository;
  late final WeeklyProgramController _weeklyProgramController;
  late final TaskRepository _taskRepository;
  late final TaskController _taskController;
  late final ExamRepository _examRepository;
  late final ExamController _examController;
  late final GoalRepository _goalRepository;
  late final GoalController _goalController;
  late final CalendarRepository _calendarRepository;
  late final CalendarController _calendarController;
  late final RoutineRepository _routineRepository;
  late final RoutineController _routineController;

  @override
  void initState() {
    super.initState();

    _tokenStorage = TokenStorageService();
    _apiClient = ApiClient(tokenStorage: _tokenStorage);
    _authRepository = AuthRepository(apiClient: _apiClient, tokenStorage: _tokenStorage);
    _authController = AuthController(
      authRepository: _authRepository,
      tokenStorage: _tokenStorage,
    );
    _weeklyProgramRepository = WeeklyProgramRepository(apiClient: _apiClient);
    _weeklyProgramController = WeeklyProgramController(repository: _weeklyProgramRepository);
    _taskRepository = TaskRepository(apiClient: _apiClient);
    _taskController = TaskController(repository: _taskRepository);
    _examRepository = ExamRepository(apiClient: _apiClient);
    _examController = ExamController(repository: _examRepository);
    _goalRepository = GoalRepository(apiClient: _apiClient);
    _goalController = GoalController(repository: _goalRepository);
    _calendarRepository = CalendarRepository(apiClient: _apiClient);
    _calendarController = CalendarController(repository: _calendarRepository);
    _routineRepository = RoutineRepository(apiClient: _apiClient);
    _routineController = RoutineController(repository: _routineRepository);

    // Refresh token da geçersiz olduğunda kullanıcıyı otomatik olarak
    // giriş ekranına yönlendirmek için ApiClient <-> AuthController bağlanır.
    _apiClient.onSessionExpired = _authController.handleSessionExpired;

    // AuthGate, kimlik durumuna göre Login/MainNav arasında `home` widget'ını
    // değiştiriyor; ama kullanıcı bir alt sayfaya push edilmişse (ör. Görev
    // Ekle) o sayfa Navigator'ın en üstünde kalıp AuthGate'in altında gizli
    // kalır. Oturum kapanınca (zorla ya da manuel logout) kök route'a dönüp
    // LoginPage'in gerçekten görünmesini garantiliyoruz.
    _authController.addListener(_handleAuthStatusChanged);

    // Uygulama açılışında kayıtlı oturum olup olmadığını kontrol et.
    _authController.checkInitialAuthStatus();
  }

  void _handleAuthStatusChanged() {
    if (_authController.status == AuthStatus.unauthenticated) {
      _navigatorKey.currentState?.popUntil((route) => route.isFirst);
      // Controller'lar uygulama ömrü boyunca yaşıyor; oturum kapanınca
      // temizlenmezlerse bir sonraki kullanıcı önceki hesabın programını,
      // denemelerini, hedeflerini görüyor.
      _weeklyProgramController.reset();
      _taskController.reset();
      _examController.reset();
      _goalController.reset();
      _calendarController.reset();
      _routineController.reset();
    }
  }

  @override
  void dispose() {
    _authController.removeListener(_handleAuthStatusChanged);
    _weeklyProgramController.dispose();
    _taskController.dispose();
    _examController.dispose();
    _goalController.dispose();
    _calendarController.dispose();
    _routineController.dispose();
    _authController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthController>.value(value: _authController),
        ChangeNotifierProvider<WeeklyProgramController>.value(value: _weeklyProgramController),
        ChangeNotifierProvider<TaskController>.value(value: _taskController),
        ChangeNotifierProvider<ExamController>.value(value: _examController),
        ChangeNotifierProvider<GoalController>.value(value: _goalController),
        ChangeNotifierProvider<CalendarController>.value(value: _calendarController),
        ChangeNotifierProvider<RoutineController>.value(value: _routineController),
      ],
      child: MaterialApp(
        navigatorKey: _navigatorKey,
        title: AppConstants.appName,
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        home: const AuthGate(),
      ),
    );
  }
}
