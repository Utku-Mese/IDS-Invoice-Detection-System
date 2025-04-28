import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'features/invoice_scan/presentation/screens/invoice_scan_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IDS - Invoice Detection System',
      theme: AppTheme.lightTheme,
      home: const InvoiceScanScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
