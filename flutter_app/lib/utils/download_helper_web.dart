// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

Future<String?> downloadFile(String content, String filename) async {
  final blob = html.Blob([content], 'application/json');
  final url = html.Url.createObjectUrlFromBlob(blob);
  final anchor = html.AnchorElement(href: url)
    ..setAttribute('download', filename);
  html.document.body?.append(anchor);
  anchor.click();
  anchor.remove();
  html.Url.revokeObjectUrl(url);
  return null;
}
