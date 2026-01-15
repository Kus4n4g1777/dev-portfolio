import 'dart:io';
import 'package:dart_frog/dart_frog.dart';

Response onRequest(RequestContext context) {
  return Response.json(
    body: {
      'service': 'Dart Runtime Service',
      'version': '1.0.0',
      'runtime': 'Dart VM',
    },
  );
}
