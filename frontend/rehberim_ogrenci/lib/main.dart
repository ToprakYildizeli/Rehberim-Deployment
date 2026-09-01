import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // API taban adresi gibi ortam değişkenlerini .env dosyasından yükle.
  await dotenv.load(fileName: '.env');

  runApp(const SinavMentorApp());
}
