class Invoice {
  final int? id;
  final String? companyName;
  final DateTime? date;
  final double? totalAmount;
  final String? taxNumber;
  final String? rawText;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  Invoice({
    this.id,
    this.companyName,
    this.date,
    this.totalAmount,
    this.taxNumber,
    this.rawText,
    this.createdAt,
    this.updatedAt,
  });

  factory Invoice.fromJson(Map<String, dynamic> json) {
    return Invoice(
      id: json['id'] as int?,
      companyName: json['company_name'] as String?,
      date: json['date'] != null ? DateTime.parse(json['date']) : null,
      totalAmount: json['total_amount'] != null
          ? (json['total_amount'] as num).toDouble()
          : null,
      taxNumber: json['tax_number'] as String?,
      rawText: json['raw_text'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'company_name': companyName,
      'date': date?.toIso8601String(),
      'total_amount': totalAmount,
      'tax_number': taxNumber,
      'raw_text': rawText,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}
