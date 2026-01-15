import 'dart:io';
import 'package:dart_frog/dart_frog.dart';
import 'package:google_generative_ai/google_generative_ai.dart';

Future<Response> onRequest(RequestContext context) async {
  if (context.request.method != HttpMethod.post) {
    return Response.json(
      statusCode: 405,
      body: {'error': 'Method not allowed'},
    );
  }

  final body = await context.request.json() as Map<String, dynamic>;
  final prompt = body['prompt'] as String?;

  if (prompt == null) {
    return Response.json(
      statusCode: 400,
      body: {'error': 'prompt is required'},
    );
  }

  final apiKey = Platform.environment['GEMINI_API_KEY'];
  if (apiKey == null || apiKey.isEmpty) {
    return Response.json(
      statusCode: 500,
      body: {
        'runtime': 'dart',
        'error': 'GEMINI_API_KEY not configured',
        'response': null,
      },
    );
  }

  try {
    final model = GenerativeModel(
      model: 'gemini-2.5-flash',  // ← FIXED
      apiKey: apiKey,
    );

    final content = [Content.text(prompt)];
    final response = await model.generateContent(content);

    return Response.json(
      body: {
        'runtime': 'dart',
        'model': 'gemini-2.5-flash',
        'response': response.text,
        'error': null,
      },
    );
  } catch (e) {
    return Response.json(
      statusCode: 500,
      body: {
        'runtime': 'dart',
        'error': e.toString(),
        'response': null,
      },
    );
  }
}
