import 'package:flutter/material.dart';

/// Uygulama genelinde kullanılan renk paleti.
/// Tüm renkler tek bir yerden yönetilir, böylece marka rengi
/// değiştirilmek istendiğinde sadece bu dosya güncellenir.
abstract class AppColors {
  AppColors._();

  static const Color primary = Color(0xFF2F5DFF);
  static const Color primaryDark = Color(0xFF1E3FCC);
  static const Color primaryLight = Color(0xFFE7ECFF);

  static const Color secondary = Color(0xFFFFA726);

  static const Color success = Color(0xFF2ECC71);
  static const Color warning = Color(0xFFF5A623);
  static const Color error = Color(0xFFE74C3C);
  static const Color info = Color(0xFF3498DB);

  static const Color background = Color(0xFFF7F8FC);
  static const Color surface = Color(0xFFFFFFFF);

  static const Color textPrimary = Color(0xFF1A1C2C);
  static const Color textSecondary = Color(0xFF6B7080);
  static const Color textDisabled = Color(0xFFB0B3C1);

  static const Color border = Color(0xFFE3E5EE);
  static const Color divider = Color(0xFFEDEEF3);

  static const Color shimmerBase = Color(0xFFE9E9EC);
  static const Color shimmerHighlight = Color(0xFFF5F5F7);
}
