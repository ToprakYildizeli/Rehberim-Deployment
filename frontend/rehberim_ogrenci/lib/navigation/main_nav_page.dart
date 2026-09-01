import 'package:flutter/material.dart';
import '../calendar/pages/calendar_page.dart';
import '../home/pages/home_page.dart';
import '../library/pages/library_page.dart';
import '../practice_exams/pages/practice_exams_page.dart';
import '../profile/pages/profile_page.dart';

/// Uygulamanın 5 ana sekmesini barındıran alt navigasyon ekranı:
/// Ana Sayfa, Kitaplık, Denemeler, Kazanımlar, Profil.
///
/// Sekmeler arası geçişte durum kaybını önlemek için [IndexedStack] kullanılır.
class MainNavPage extends StatefulWidget {
  static const routeName = '/home';

  const MainNavPage({super.key});

  @override
  State<MainNavPage> createState() => _MainNavPageState();
}

class _MainNavPageState extends State<MainNavPage> {
  int _selectedIndex = 0;

  static const List<Widget> _pages = [
    HomePage(),
    LibraryPage(),
    PracticeExamsPage(),
    CalendarPage(),
    ProfilePage(),
  ];

  void _onItemTapped(int index) {
    setState(() => _selectedIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _pages,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home_rounded),
            label: 'Ana Sayfa',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.menu_book_outlined),
            activeIcon: Icon(Icons.menu_book_rounded),
            label: 'Kitaplık',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.fact_check_outlined),
            activeIcon: Icon(Icons.fact_check_rounded),
            label: 'Denemeler',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.calendar_today_outlined),
            activeIcon: Icon(Icons.calendar_today_rounded),
            label: 'Takvim',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            activeIcon: Icon(Icons.person_rounded),
            label: 'Profil',
          ),
        ],
      ),
    );
  }
}
