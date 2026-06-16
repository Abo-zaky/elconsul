const { URL } = require('url');

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

function cleanupHeaders(headers) {
  const cleaned = { ...headers };
  delete cleaned['Content-Length'];
  delete cleaned['content-length'];
  delete cleaned['Content-Type'];
  delete cleaned['content-type'];
  return cleaned;
}

exports.handler = async function(event) {
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: CORS_HEADERS,
      body: ''
    };
  }

  const target = event.queryStringParameters && event.queryStringParameters.url;
  if (!target) {
    return {
      statusCode: 400,
      headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Missing target url parameter' })
    };
  }

  let parsed;
  try {
    parsed = new URL(target);
  } catch (err) {
    return {
      statusCode: 400,
      headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Invalid URL format: ' + err.message })
    };
  }

  const ALLOWED_HOSTNAMES = new Set(['script.google.com', 'script.googleusercontent.com']);
  if (!ALLOWED_HOSTNAMES.has(parsed.hostname)) {
    return {
      statusCode: 403,
      headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Access denied: target hostname not allowed' })
    };
  }

  let currentUrl = target;
  let method = (event.httpMethod || 'GET').toUpperCase();
  let requestBody = undefined;
  if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
    requestBody = event.body ? (event.isBase64Encoded ? Buffer.from(event.body, 'base64').toString('utf8') : event.body) : undefined;
  }

  const originalContentType = event.headers && (event.headers['content-type'] || event.headers['Content-Type']);
  const commonHeaders = {
    'User-Agent': 'NetlifyProxy/1.0',
    'Accept': '*/*',
    'Accept-Encoding': 'identity',
  };
  if (originalContentType && requestBody) {
    commonHeaders['Content-Type'] = originalContentType;
  }

  try {
    let response;
    let redirectCount = 0;

    while (redirectCount < 6) {
      const requestOptions = {
        method,
        headers: { ...commonHeaders },
        body: requestBody,
        redirect: 'manual'
      };

      response = await fetch(currentUrl, requestOptions);
      const currentHost = new URL(currentUrl).hostname;
      if (![301, 302, 303, 307, 308].includes(response.status)) {
        if ((currentHost === 'script.googleusercontent.com' || currentHost === 'script.google.com') && response.status === 200) {
          break;
        }
        break;
      }

      const location = response.headers.get('location');
      if (!location) {
        throw new Error(`Redirect without Location header: ${response.status}`);
      }

      redirectCount += 1;
      currentUrl = new URL(location, currentUrl).toString();

      if ([301, 302, 303].includes(response.status) && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        method = 'GET';
        requestBody = undefined;
        delete commonHeaders['Content-Type'];
      }
    }

    const contentEncoding = (response.headers.get('content-encoding') || '').toLowerCase();
    let responseBody;

    if (['gzip', 'x-gzip', 'deflate', 'br'].some(enc => contentEncoding.includes(enc))) {
      const buffer = Buffer.from(await response.arrayBuffer());
      if (contentEncoding.includes('gzip') || contentEncoding.includes('x-gzip')) {
        const zlib = require('zlib');
        responseBody = zlib.gunzipSync(buffer).toString('utf8');
      } else if (contentEncoding.includes('deflate')) {
        const zlib = require('zlib');
        responseBody = zlib.inflateSync(buffer).toString('utf8');
      } else if (contentEncoding.includes('br')) {
        const zlib = require('zlib');
        responseBody = zlib.brotliDecompressSync(buffer).toString('utf8');
      }
    } else {
      responseBody = await response.text();
    }

    const responseContentType = response.headers.get('content-type') || 'text/plain';

    // If debug flag is provided, return diagnostic JSON including original request body
    const qs = event.queryStringParameters || {};
    if (qs.debug === '1') {
      const originalBody = requestBody || '';
      const origHeaders = event.headers || {};
      const upstreamHeaders = {};
      for (const [k, v] of response.headers.entries()) upstreamHeaders[k] = v;
      return {
        statusCode: 200,
        headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ok: true,
          forwardedTo: currentUrl,
          methodSent: method,
          originalHeaders: origHeaders,
          originalBody: originalBody,
          upstreamStatus: response.status,
          upstreamHeaders: upstreamHeaders,
          upstreamBody: responseBody
        }),
        isBase64Encoded: false
      };
    }

    return {
      statusCode: response.status,
      headers: { ...CORS_HEADERS, 'Content-Type': responseContentType, 'Cache-Control': 'no-cache' },
      body: responseBody,
      isBase64Encoded: false
    };
  } catch (err) {
    console.error('Proxy error:', err);
    return {
      statusCode: 502,
      headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Proxy request failed', detail: err.message })
    };
  }
};
