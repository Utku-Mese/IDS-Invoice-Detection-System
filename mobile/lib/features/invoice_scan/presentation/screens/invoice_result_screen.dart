import 'package:flutter/material.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:share_plus/share_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:image_gallery_saver/image_gallery_saver.dart';
import 'dart:io';
import 'dart:convert';
import 'package:intl/intl.dart';
import '../../../../shared/models/invoice_model.dart';

class InvoiceResultScreen extends StatelessWidget {
  final Invoice invoice;
  final File? imageFile;

  const InvoiceResultScreen({
    Key? key,
    required this.invoice,
    this.imageFile,
  }) : super(key: key);

  Future<void> _showImageDialog(BuildContext context) async {
    if (imageFile == null) return;

    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        child: Stack(
          children: [
            InteractiveViewer(
              minScale: 0.5,
              maxScale: 4.0,
              child: Image.file(
                imageFile!,
                fit: BoxFit.contain,
              ),
            ),
            Positioned(
              top: 8,
              right: 8,
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.save_alt, color: Colors.white),
                    onPressed: () => _saveImage(context),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _saveImage(BuildContext context) async {
    if (imageFile == null) return;

    try {
      final result = await ImageGallerySaver.saveFile(imageFile!.path);
      if (result['isSuccess']) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Görsel başarıyla kaydedildi'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Görsel kaydedilemedi'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hata: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _exportAsPDF(BuildContext context) async {
    try {
      final pdf = pw.Document();

      // PDF içeriğini oluştur
      pdf.addPage(
        pw.MultiPage(
          build: (context) => [
            pw.Header(
              level: 0,
              child: pw.Text(
                'Fatura Detayları',
                style: pw.TextStyle(
                  fontSize: 24,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
            ),
            pw.SizedBox(height: 20),
            if (imageFile != null)
              pw.Image(
                pw.MemoryImage(imageFile!.readAsBytesSync()),
                width: 300,
                height: 200,
                fit: pw.BoxFit.contain,
              ),
            pw.SizedBox(height: 20),
            pw.Text('Firma Adı: ${invoice.companyName ?? "Bilinmiyor"}'),
            pw.Text(
                'Tarih: ${invoice.date != null ? DateFormat('dd/MM/yyyy').format(invoice.date!) : "Bilinmiyor"}'),
            pw.Text(
                'Toplam Tutar: ${invoice.totalAmount?.toStringAsFixed(2) ?? "0.00"} TL'),
            pw.Text('Vergi Numarası: ${invoice.taxNumber ?? "Bilinmiyor"}'),
            pw.SizedBox(height: 20),
            pw.Text(
              'Ham Metin:',
              style: pw.TextStyle(fontWeight: pw.FontWeight.bold),
            ),
            pw.Text(invoice.rawText ?? ""),
          ],
        ),
      );

      // PDF'i kaydet
      final output = await getTemporaryDirectory();
      final file = File(
          '${output.path}/invoice_${DateTime.now().millisecondsSinceEpoch}.pdf');
      await file.writeAsBytes(await pdf.save());

      // Paylaş
      await Share.shareXFiles([XFile(file.path)], text: 'Fatura Detayları');
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('PDF oluşturulurken hata oluştu: $e')),
      );
    }
  }

  Future<void> _exportAsJSON(BuildContext context) async {
    try {
      final jsonString = invoice.toJson().toString();
      final output = await getTemporaryDirectory();
      final file = File(
          '${output.path}/invoice_${DateTime.now().millisecondsSinceEpoch}.json');
      await file.writeAsString(jsonString);

      await Share.shareXFiles([XFile(file.path)],
          text: 'Fatura Detayları (JSON)');
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('JSON oluşturulurken hata oluştu: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fatura Sonuçları'),
        elevation: 0,
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'pdf') {
                _exportAsPDF(context);
              } else if (value == 'json') {
                _exportAsJSON(context);
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'pdf',
                child: Text('PDF Olarak Dışa Aktar'),
              ),
              const PopupMenuItem(
                value: 'json',
                child: Text('JSON Olarak Dışa Aktar'),
              ),
            ],
          ),
        ],
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Theme.of(context).colorScheme.primary.withOpacity(0.1),
              Theme.of(context).colorScheme.surface,
            ],
          ),
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (imageFile != null)
                GestureDetector(
                  onTap: () => _showImageDialog(context),
                  child: Stack(
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.file(
                          imageFile!,
                          height: 200,
                          width: double.infinity,
                          fit: BoxFit.cover,
                        ),
                      ),
                      Positioned(
                        top: 8,
                        right: 8,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.5),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Icon(
                            Icons.zoom_in,
                            color: Colors.white,
                            size: 20,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 24),
              _buildInfoCard(
                context,
                'Firma Bilgileri',
                [
                  _buildInfoRow(
                      'Firma Adı', invoice.companyName ?? "Bilinmiyor"),
                  _buildInfoRow(
                      'Vergi Numarası', invoice.taxNumber ?? "Bilinmiyor"),
                ],
              ),
              const SizedBox(height: 16),
              _buildInfoCard(
                context,
                'Fatura Detayları',
                [
                  _buildInfoRow(
                    'Tarih',
                    invoice.date != null
                        ? DateFormat('dd/MM/yyyy').format(invoice.date!)
                        : "Bilinmiyor",
                  ),
                  _buildInfoRow(
                    'Toplam Tutar',
                    '${invoice.totalAmount?.toStringAsFixed(2) ?? "0.00"} TL',
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _buildInfoCard(
                context,
                'Ham Metin',
                [
                  Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: Text(
                      invoice.rawText ?? "",
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoCard(
      BuildContext context, String title, List<Widget> children) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).colorScheme.primary,
                  ),
            ),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.grey,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
    );
  }
}
