/// Downloads [content] as a file named [filename].
/// On web, triggers a browser download and returns null.
/// On other platforms, saves to the application documents directory and
/// returns the full path of the saved file.
export 'download_helper_io.dart'
    if (dart.library.html) 'download_helper_web.dart';
