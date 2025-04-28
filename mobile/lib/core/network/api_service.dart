import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'dart:io';
import 'package:mime/mime.dart';
import 'package:http_parser/http_parser.dart'; // MediaType için

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api/v1';
  final Dio _dio;

  ApiService() : _dio = Dio() {
    _dio.options.baseUrl = baseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 5);
    _dio.options.receiveTimeout = const Duration(seconds: 3);

    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
      ));
    }
  }

  Future<Map<String, dynamic>> extractInvoiceData(File imageFile) async {
    try {
      String fileName = imageFile.path.split('/').last;

      // Dosyanın MIME türünü belirle (varsayılan olarak 'image/jpeg' ayarlandı)
      String? mimeType = lookupMimeType(imageFile.path) ?? 'image/jpeg';

      if (!(mimeType == 'image/jpeg' ||
          mimeType == 'image/png' ||
          mimeType == 'image/jpg')) {
        throw Exception(
            'Geçersiz dosya formatı! Sadece JPG, JPEG veya PNG desteklenmektedir.');
      }

      FormData formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          imageFile.path,
          filename: fileName,
          contentType:
              MediaType.parse(mimeType), // `http_parser` kütüphanesi ile
        ),
      });

      final response = await _dio.post(
        '/ocr/extract',
        data: formData,
        options: Options(
          headers: {
            'Content-Type': mimeType, // Doğru MIME türü ekleniyor
          },
        ),
      );

      return response.data;
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(e.response?.data['error'] ?? 'API hatası oluştu');
      } else {
        throw Exception('Bağlantı hatası: ${e.message}');
      }
    } catch (e) {
      throw Exception('Beklenmeyen bir hata oluştu: $e');
    }
  }
}
