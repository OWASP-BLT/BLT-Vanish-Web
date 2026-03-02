import 'dart:io';

import 'package:path_provider/path_provider.dart';

Future<String?> downloadFile(String content, String filename) async {
  final directory = await getApplicationDocumentsDirectory();
  final file = File('${directory.path}/$filename');
  await file.writeAsString(content);
  return file.path;
}
