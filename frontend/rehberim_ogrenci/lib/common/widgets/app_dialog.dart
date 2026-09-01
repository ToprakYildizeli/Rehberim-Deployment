import 'package:flutter/material.dart';
import 'app_button.dart';

/// Uygulama genelinde kullanılan onay / bilgi pop-up'ları.
abstract class AppDialog {
  AppDialog._();

  /// Basit bir onay diyaloğu gösterir. Kullanıcı onaylarsa `true`, iptal ederse
  /// `false` veya `null` döner.
  static Future<bool?> confirm(
    BuildContext context, {
    required String title,
    required String message,
    String confirmLabel = 'Onayla',
    String cancelLabel = 'Vazgeç',
    bool isDestructive = false,
  }) {
    return showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: Text(title),
        content: Text(message),
        actionsPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        actions: [
          // AlertDialog.actions bir Row/Flex değil, `OverflowBar` ile
          // döşenir — `Expanded` kullanabilmek için kendi Row'umuzu sarmamız
          // gerekiyor (aksi halde "Incorrect use of ParentDataWidget" hatası
          // alınır).
          Row(
            children: [
              Expanded(
                child: AppButton(
                  label: cancelLabel,
                  variant: AppButtonVariant.outlined,
                  onPressed: () => Navigator.of(ctx).pop(false),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: AppButton(
                  label: confirmLabel,
                  variant: AppButtonVariant.primary,
                  onPressed: () => Navigator.of(ctx).pop(true),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Tek butonlu bilgilendirme diyaloğu (ör. hata/başarı mesajları için).
  static Future<void> info(
    BuildContext context, {
    required String title,
    required String message,
    String buttonLabel = 'Tamam',
  }) {
    return showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: Text(title),
        content: Text(message),
        actionsPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        actions: [
          SizedBox(
            width: double.infinity,
            child: AppButton(
              label: buttonLabel,
              onPressed: () => Navigator.of(ctx).pop(),
            ),
          ),
        ],
      ),
    );
  }

  /// Özel içerikli bir bottom-sheet / pop-up göstermek için genel sarmalayıcı.
  static Future<T?> showCustom<T>(BuildContext context, {required Widget child}) {
    return showDialog<T>(
      context: context,
      builder: (ctx) => Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        insetPadding: const EdgeInsets.symmetric(horizontal: 24),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: child,
        ),
      ),
    );
  }
}
