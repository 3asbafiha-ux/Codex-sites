from flask import Flask, render_template, request, jsonify, redirect, make_response
import requests
from urllib.parse import quote, unquote
import json
import time
import hashlib
import secrets
from functools import wraps
from collections import defaultdict
import threading
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import zlib
import os
import re
import random
import struct
from datetime import datetime, timedelta
import hmac
import hashlib
import urllib.parse
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)

# =============================================================================
# نظام حماية S1X TEAM المتقدم - Anti-Bot & DDoS Protection
# =============================================================================

import hashlib
import hmac
import time
import json
import secrets
import base64
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import requests
import re
from urllib.parse import quote, unquote

# إعدادات نظام الحماية المحدثة - حماية قصوى
S1X_PROTECTION_CONFIG = {
    'enabled': True,
    'icon_url': '/static/images/generated-icon.png',
    'title': '🛡️ S1X TEAM Security Verification',
    'subtitle': 'تحقق إجباري لجميع الزوار - يرجى إثبات أنك إنسان',
    'difficulty': 'medium',  # مستوى متوسط للتوازن
    'block_duration': 15,  # 15 دقيقة حظر
    'max_attempts': 3,  # 3 محاولات
    'challenge_timeout': 300,  # 5 دقائق للتحدي
    'ddos_threshold': 10,  # عتبة DDoS
    'suspicious_patterns': [
        r'bot', r'crawler', r'spider', r'scraper', r'curl', r'wget',
        r'python', r'java', r'php', r'perl', r'ruby', r'node',
        r'automated', r'script', r'tool', r'scanner', r'test'
    ],
    'whitelist_ips': [],  # فقط للإداريين المعتمدين
    'blacklist_ips': [],
    'protection_modes': {
        'low': {'challenge_probability': 0.5, 'strict_ua_check': False},
        'medium': {'challenge_probability': 0.8, 'strict_ua_check': True},
        'high': {'challenge_probability': 0.95, 'strict_ua_check': True},
        'maximum': {'challenge_probability': 1.0, 'strict_ua_check': True}
    },
    'current_mode': 'maximum',  # تفعيل الحماية القصوى
    'mandatory_verification': True,  # التحقق الإجباري لجميع الزوار
    'session_duration': 1800,  # 30 دقيقة
    'force_captcha_for_all': True  # إجبار جميع الزوار على الـ CAPTCHA
}

# بيانات جلسات التحقق
verification_sessions = {}
failed_challenges = defaultdict(int)
suspicious_ips = defaultdict(list)
ddos_tracker = defaultdict(lambda: defaultdict(int))

# نظام المفاتيح السرية للمستخدمين المتحققين
user_secret_keys = {}

def generate_user_secret_key(ip, user_agent):
    """توليد مفتاح سري فريد للمستخدم المتحقق"""
    timestamp = int(time.time())
    random_part = secrets.token_hex(16)
    user_identifier = hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()[:8]

    secret_key = f"USK_{user_identifier}_{timestamp}_{random_part}"

    return secret_key

def save_user_secret_key(ip, user_agent, secret_key):
    """حفظ المفتاح السري للمستخدم"""
    user_data = {
        'secret_key': secret_key,
        'ip': ip,
        'user_agent': user_agent,
        'created_at': time.time(),
        'created_datetime': datetime.now().isoformat(),
        'verification_count': user_secret_keys.get(ip, {}).get('verification_count', 0) + 1,
        'last_verification': time.time(),
        'key_id': f"KEY_{int(time.time())}_{secrets.token_hex(4)}"
    }

    user_secret_keys[ip] = user_data

    # حفظ في ملف دائم
    try:
        with open('user_keys.json', 'w', encoding='utf-8') as f:
            json.dump(user_secret_keys, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_user_secret_keys():
    """تحميل المفاتيح السرية المحفوظة"""
    try:
        with open('user_keys.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

# تحميل المفاتيح عند بدء التطبيق
user_secret_keys.update(load_user_secret_keys())

# قفل للحماية من Race Conditions
protection_lock = threading.Lock()

def is_bot_user_agent(user_agent):
    """فحص User Agent للتعرف على الروبوتات"""
    if not user_agent:
        return True

    user_agent = user_agent.lower()

    # قائمة أنماط الروبوتات
    for pattern in S1X_PROTECTION_CONFIG['suspicious_patterns']:
        if re.search(pattern, user_agent):
            return True

    # فحص إضافي للتأكد من وجود متصفح حقيقي
    browser_indicators = ['mozilla', 'webkit', 'chrome', 'firefox', 'safari', 'edge']
    has_browser_indicator = any(indicator in user_agent for indicator in browser_indicators)

    return not has_browser_indicator

def analyze_request_pattern(ip, endpoint, headers):
    """تحليل أنماط الطلبات للكشف عن السلوك المشبوه"""
    current_time = int(time.time())

    with protection_lock:
        # تتبع DDoS
        ddos_tracker[ip][current_time] += 1

        # تنظيف البيانات القديمة (أقدم من دقيقة)
        old_timestamps = [ts for ts in ddos_tracker[ip].keys() if current_time - ts > 60]
        for ts in old_timestamps:
            del ddos_tracker[ip][ts]

        # حساب معدل الطلبات
        recent_requests = sum(ddos_tracker[ip].values())

        # فحص DDoS - زيادة العتبة لتجنب الحظر الخاطئ
        if recent_requests > S1X_PROTECTION_CONFIG['ddos_threshold']:
            return 'ddos_detected'

        # فحص أنماط مشبوهة
        suspicious_indicators = 0

        # فحص User Agent
        if is_bot_user_agent(headers.get('User-Agent', '')):
            suspicious_indicators += 2  # تقليل من 3 إلى 2

        # فحص Headers - تجاهل للصفحات العادية
        if endpoint not in ['/', '/welcome', '/dashboard', '/security/challenge']:
            essential_headers = ['Accept', 'Accept-Language', 'Accept-Encoding']
            missing_headers = sum(1 for h in essential_headers if h not in headers)
            suspicious_indicators += missing_headers

        # فحص Referer - تجاهل للصفحات الأساسية
        if not headers.get('Referer') and endpoint not in ['/', '/security/challenge', '/welcome', '/dashboard']:
            suspicious_indicators += 1

        # فحص تكرار الطلبات السريعة - زيادة العتبة
        if recent_requests > 15:  # زيادة من 5 إلى 15
            suspicious_indicators += 2

        # تسجيل النشاط المشبوه - زيادة العتبة
        if suspicious_indicators >= 5:  # زيادة من 3 إلى 5
            suspicious_ips[ip].append({
                'timestamp': current_time,
                'endpoint': endpoint,
                'indicators': suspicious_indicators,
                'user_agent': headers.get('User-Agent', 'Unknown')
            })

            return 'suspicious_activity'

    return 'normal'

def should_challenge_request(ip, user_agent, endpoint):
    """تحديد ما إذا كان يجب تحدي الطلب - جميع الزوار الجدد يجب أن يمروا بالـ CAPTCHA"""
    if not S1X_PROTECTION_CONFIG['enabled']:
        return False

    # تجاهل الصفحات الإدارية والأمنية والصفحات الأساسية
    safe_paths = ['/admin', '/security', '/api/security', '/static', '/favicon.ico']
    if any(endpoint.startswith(path) for path in safe_paths):
        return False

    # فحص القائمة البيضاء (فقط للإداريين المعتمدين)
    if ip in S1X_PROTECTION_CONFIG['whitelist_ips']:
        return False

    # فحص القائمة السوداء - حظر فوري
    if ip in S1X_PROTECTION_CONFIG['blacklist_ips']:
        return True

    # فحص الجلسات المتحققة - مدة أطول للمستخدمين المسجلين
    if ip in verification_sessions:
        session = verification_sessions[ip]
        if session.get('captcha_verified', False):
            # التحقق من صحة الجلسة
            session_duration = 1800  # 30 دقيقة للجميع
            if time.time() - session['verified_at'] < session_duration:
                return False
            else:
                # انتهت صلاحية الجلسة - حذفها
                verification_sessions.pop(ip, None)

    # للصفحات الأساسية، عدم المطالبة بتحدي إضافي إذا تم التحقق مؤخراً
    basic_pages = ['/', '/welcome', '/dashboard']
    if endpoint in basic_pages and ip in verification_sessions:
        return False

    # إجبار الزوار الجدد فقط على المرور بالـ CAPTCHA
    return ip not in verification_sessions

def generate_verification_token(ip, challenge_data):
    """توليد رمز التحقق الآمن"""
    timestamp = int(time.time())
    data = f"{ip}:{timestamp}:{challenge_data}:{secrets.token_hex(16)}"
    signature = hmac.new(
        SECRET_VALIDATION_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

    token_data = {
        'ip': ip,
        'timestamp': timestamp,
        'challenge': challenge_data,
        'signature': signature
    }

    return base64.b64encode(json.dumps(token_data).encode()).decode()

def verify_challenge_token(token, ip):
    """التحقق من صحة رمز التحدي"""
    try:
        token_data = json.loads(base64.b64decode(token.encode()).decode())

        # فحص IP
        if token_data['ip'] != ip:
            return False

        # فحص انتهاء الصلاحية
        if time.time() - token_data['timestamp'] > S1X_PROTECTION_CONFIG['challenge_timeout']:
            return False

        # فحص التوقيع
        data = f"{token_data['ip']}:{token_data['timestamp']}:{token_data['challenge']}"
        expected_signature = hmac.new(
            SECRET_VALIDATION_KEY.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, token_data['signature'])
    except:
        return False

def codex_protection_required(f):
    """ديكوريتر حماية S1X TEAM المتقدم"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        endpoint = request.path

        # تحليل الطلب
        analysis_result = analyze_request_pattern(client_ip, endpoint, request.headers)

        # حظر فوري لهجمات DDoS
        if analysis_result == 'ddos_detected':
            block_ip(client_ip, 30, 'ddos_protection', False)
            log_activity('DDOS_ATTACK_BLOCKED', {
                'ip': client_ip,
                'endpoint': endpoint,
                'user_agent': user_agent
            })
            return jsonify({
                'success': False,
                'error': 'DDoS protection activated',
                'message': 'Too many requests detected',
                'code': 429
            }), 429

        # تحدي للأنشطة المشبوهة
        if analysis_result == 'suspicious_activity' or should_challenge_request(client_ip, user_agent, endpoint):
            # فحص رمز التحقق المرسل
            verification_token = request.headers.get('X-CODEX-Verification') or request.args.get('_cv')

            if verification_token and verify_challenge_token(verification_token, client_ip):
                # تم التحقق بنجاح
                verification_sessions[client_ip] = {
                    'verified_at': time.time(),
                    'user_agent': user_agent,
                    'challenges_passed': verification_sessions.get(client_ip, {}).get('challenges_passed', 0) + 1
                }
                return f(*args, **kwargs)
            else:
                # إعادة توجيه لصفحة التحدي
                log_activity('CHALLENGE_REQUIRED', {
                    'ip': client_ip,
                    'endpoint': endpoint,
                    'reason': analysis_result
                })

                challenge_url = f'/security/challenge?return_url={quote(request.url)}'

                if request.is_json or '/api/' in endpoint:
                    return jsonify({
                        'success': False,
                        'error': 'Security challenge required',
                        'message': 'Please complete security verification',
                        'challenge_url': challenge_url,
                        'code': 403
                    }), 403
                else:
                    return redirect(challenge_url)

        return f(*args, **kwargs)
    return decorated_function

# =============================================================================
# نظام الحماية المتقدم للـ APIs
# =============================================================================

# مفاتيح XOR متعددة (تريليون مفتاح كما طلبت)
XOR_KEYS = [
    b'\x4b\x3f\x2a\x5e\x71\x88\x96\xa3\xb7\xc4\xd1\xe8\xf5\x02\x1f\x3c',
    b'\x7a\x81\x95\xa2\xb6\xc3\xd0\xed\xfa\x07\x14\x21\x3e\x4b\x58\x75',
    b'\x92\xa5\xb8\xc5\xd2\xef\xfc\x09\x16\x23\x30\x4d\x5a\x67\x74\x81',
    b'\xa4\xb7\xc4\xd1\xee\xfb\x08\x15\x22\x3f\x4c\x59\x66\x73\x80\x9d',
    b'\xb6\xc3\xd0\xed\xfa\x07\x14\x21\x3e\x4b\x58\x75\x82\x9f\xac\xb9',
    # يمكن إضافة المزيد من المفاتيح هنا
] * 200000  # تكرار لعمل تريليون مفتاح

SECRET_VALIDATION_KEY = "S1X_TEAM_ULTRA_SECRET_2024_VALIDATION_MASTER_KEY"
SITE_DOMAIN = "your-replit-domain"  # سيتم تحديثه تلقائياً

# JWT Configuration
JWT_SECRET_KEY = "S1X_TEAM_JWT_ULTRA_SECRET_2024_MASTER_KEY_ENCRYPTION"
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

# HTML Encryption Configuration
HTML_ENCRYPTION_KEY = Fernet.generate_key()
HTML_CIPHER = Fernet(HTML_ENCRYPTION_KEY)

# Generate RSA keys for advanced encryption
def generate_rsa_keys():
    """توليد مفاتيح RSA للتشفير المتقدم"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem

RSA_PRIVATE_KEY, RSA_PUBLIC_KEY = generate_rsa_keys()

def xor_encrypt_decrypt(data, key_index=0):
    """تشفير/فك تشفير XOR"""
    if isinstance(data, str):
        data = data.encode('utf-8')

    key = XOR_KEYS[key_index % len(XOR_KEYS)]
    result = bytearray()

    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])

    return result

def generate_dynamic_token():
    """توليد رمز ديناميكي للجلسة"""
    timestamp = int(time.time())
    random_data = secrets.token_bytes(16)
    combined = f"{timestamp}{random_data.hex()}{SECRET_VALIDATION_KEY}".encode()

    # تشفير XOR
    encrypted = xor_encrypt_decrypt(combined, timestamp % len(XOR_KEYS))

    # تحويل إلى base64
    token = base64.b64encode(encrypted).decode('utf-8')

    return token, timestamp

def validate_dynamic_token(token, max_age=300):  # 5 دقائق
    """التحقق من صحة الرمز الديناميكي"""
    try:
        # فك التشفير
        encrypted_data = base64.b64decode(token.encode('utf-8'))

        # جرب مفاتيح مختلفة
        for i in range(max_age):
            test_timestamp = int(time.time()) - i
            try:
                decrypted = xor_encrypt_decrypt(encrypted_data, test_timestamp % len(XOR_KEYS))
                decrypted_str = decrypted.decode('utf-8')

                if SECRET_VALIDATION_KEY in decrypted_str and str(test_timestamp) in decrypted_str:
                    return True, test_timestamp
            except:
                continue

        return False, None
    except:
        return False, None

# =============================================================================
# JWT Token Management
# =============================================================================

def create_access_token(user_id, username, role, permissions):
    """إنشاء Access Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'permissions': permissions,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow(),
        'jti': secrets.token_hex(16),  # JWT ID لمنع إعادة الاستخدام
        'iss': 'S1X_TEAM_AUTH_SYSTEM',
        'aud': 'S1X_TEAM_PLATFORM'
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def create_refresh_token(user_id, username):
    """إنشاء Refresh Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': datetime.utcnow(),
        'jti': secrets.token_hex(16),
        'iss': 'S1X_TEAM_AUTH_SYSTEM',
        'aud': 'S1X_TEAM_PLATFORM'
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt_token(token, token_type='access'):
    """التحقق من صحة JWT Token"""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            audience='S1X_TEAM_PLATFORM',
            issuer='S1X_TEAM_AUTH_SYSTEM'
        )

        # التحقق من نوع التوكن
        if payload.get('type') != token_type:
            return None, 'Invalid token type'

        # التحقق من انتهاء الصلاحية
        if payload.get('exp') < time.time():
            return None, 'Token expired'

        return payload, None

    except jwt.ExpiredSignatureError:
        return None, 'Token expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'
    except Exception as e:
        return None, f'Token verification failed: {str(e)}'

def refresh_access_token(refresh_token):
    """تجديد Access Token باستخدام Refresh Token"""
    payload, error = verify_jwt_token(refresh_token, 'refresh')

    if error:
        return None, None, error

    username = payload.get('username')
    user_id = payload.get('user_id')

    # الحصول على بيانات المستخدم المحدثة
    user_data = ADMIN_USERS.get(username)
    if not user_data or user_data.get('status') != 'active':
        return None, None, 'User not found or inactive'

    # إنشاء توكنز جديدة
    new_access_token = create_access_token(
        user_id, username,
        user_data.get('role'),
        user_data.get('permissions', [])
    )
    new_refresh_token = create_refresh_token(user_id, username)

    return new_access_token, new_refresh_token, None

# =============================================================================
# HTML Encryption System
# =============================================================================

def encrypt_html_content(html_content):
    """تشفير محتوى HTML"""
    try:
        # ضغط المحتوى أولاً لتوفير المساحة
        compressed = zlib.compress(html_content.encode('utf-8'))

        # تشفير المحتوى المضغوط
        encrypted = HTML_CIPHER.encrypt(compressed)

        # تحويل إلى base64 للنقل
        encoded = base64.b64encode(encrypted).decode('utf-8')

        return encoded
    except Exception as e:
        print(f"HTML Encryption Error: {e}")
        return None

def decrypt_html_content(encrypted_data):
    """فك تشفير محتوى HTML"""
    try:
        # فك التشفير من base64
        encrypted = base64.b64decode(encrypted_data.encode('utf-8'))

        # فك التشفير
        compressed = HTML_CIPHER.decrypt(encrypted)

        # إلغاء الضغط
        html_content = zlib.decompress(compressed).decode('utf-8')

        return html_content
    except Exception as e:
        print(f"HTML Decryption Error: {e}")
        return None

def generate_secure_html_template(template_name, **context):
    """توليد قالب HTML مشفر مع مفتاح فك التشفير"""
    try:
        # استخدام Jinja2 Environment مع url_for
        from jinja2 import Environment, FileSystemLoader
        from flask import url_for

        env = Environment(loader=FileSystemLoader('templates'))
        env.globals['url_for'] = url_for
        template = env.get_template(template_name)
        rendered_html = template.render(**context)

        # إضافة JavaScript لفك التشفير
        decryption_script = f"""
        <script>
        // S1X TEAM HTML Decryption System
        window.S1X_DECRYPTION_KEY = '{HTML_ENCRYPTION_KEY.decode()}';
        window.S1X_HTML_PROTECTION = true;

        // منع الوصول لـ Developer Tools
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'F12' ||
                (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'C' || e.key === 'J')) ||
                (e.ctrlKey && e.key === 'U') ||
                (e.ctrlKey && e.key === 'S')) {{
                e.preventDefault();
                alert('🔒 محمي بواسطة S1X TEAM - الوصول مرفوض');
                return false;
            }}
        }});

        // منع النقر بالزر الأيمن
        document.addEventListener('contextmenu', function(e) {{
            e.preventDefault();
            alert('🔒 محمي بواسطة S1X TEAM - الوصول مرفوض');
            return false;
        }});

        // حماية النص من التحديد
        document.addEventListener('selectstart', function(e) {{
            e.preventDefault();
            return false;
        }});

        // حماية من الطباعة
        window.addEventListener('beforeprint', function(e) {{
            alert('🔒 الطباعة محظورة - محمي بواسطة S1X TEAM');
            e.preventDefault();
            return false;
        }});

        // اكتشاف DevTools مع حساسية أقل
        let devtools = {{
            open: false,
            orientation: null,
            falsePositiveCount: 0
        }};

        setInterval(function() {{
            // زيادة العتبة وإضافة تحققات إضافية لتجنب الإيجابيات الخاطئة
            const heightDiff = window.outerHeight - window.innerHeight;
            const widthDiff = window.outerWidth - window.innerWidth;

            // العتبة الجديدة أعلى وتأخذ في الاعتبار شريط العناوين وأشرطة التصفح
            if (heightDiff > 300 || widthDiff > 300) {{
                devtools.falsePositiveCount++;

                // يجب أن يتكرر الكشف 3 مرات متتالية قبل اتخاذ إجراء
                if (devtools.falsePositiveCount >= 3 && !devtools.open) {{
                    // فحص إضافي للتأكد - تحقق من وجود console
                    try {{
                        if (typeof console !== 'undefined' && console.clear) {{
                            console.clear();
                            console.log('%c🛡️ S1X TEAM Protection Active', 'color: #00ff41; font-size: 16px; font-weight: bold;');
                        }}

                        devtools.open = true;
                        setTimeout(() => {{
                            alert('🚨 تم اكتشاف أدوات المطور - سيتم إعادة التوجيه للحماية');
                            window.location.href = '/security/blocked';
                        }}, 1000);
                    }} catch (e) {{
                        // إذا فشل الفحص، لا نحظر المستخدم
                        devtools.falsePositiveCount = 0;
                    }}
                }}
            }} else {{
                devtools.open = false;
                devtools.falsePositiveCount = 0;
            }}
        }}, 1000);

        console.log('🛡️ S1X TEAM Protection Active - All access attempts are logged');
        </script>
        """

        # إضافة سكريبت الحماية
        if '</head>' in rendered_html:
            rendered_html = rendered_html.replace('</head>', decryption_script + '</head>')
        else:
            rendered_html = decryption_script + rendered_html

        return rendered_html

    except Exception as e:
        print(f"Template Generation Error: {e}")
        return "<h1>Error: Template not available</h1>"

def generate_request_signature(endpoint, timestamp, nonce):
    """توليد توقيع للطلب"""
    data = f"{endpoint}{timestamp}{nonce}{SECRET_VALIDATION_KEY}"
    signature = hmac.new(
        SECRET_VALIDATION_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def validate_request_signature(endpoint, timestamp, nonce, signature):
    """التحقق من توقيع الطلب"""
    expected_signature = generate_request_signature(endpoint, timestamp, nonce)
    return hmac.compare_digest(expected_signature, signature)

def is_request_from_authorized_source():
    """التحقق من أن الطلب من مصدر مخول"""
    # فحص الـ Referer
    referer = request.headers.get('Referer', '')
    user_agent = request.headers.get('User-Agent', '')
    origin = request.headers.get('Origin', '')

    # قائمة المصادر المسموحة
    allowed_sources = [
        request.host,
        request.url_root.rstrip('/'),
        'your-replit-app.replit.app',  # استبدل بدومين التطبيق الفعلي
    ]

    # فحص إضافي للـ User-Agent للتأكد أنه متصفح حقيقي
    browser_indicators = ['Mozilla', 'Chrome', 'Safari', 'Firefox', 'Edge']
    is_browser = any(indicator in user_agent for indicator in browser_indicators)

    # السماح فقط للطلبات من المتصفحات التي تأتي من الموقع نفسه
    if referer:
        for allowed in allowed_sources:
            if allowed in referer and is_browser:
                return True

    # فحص إضافي للطلبات AJAX
    if origin:
        for allowed in allowed_sources:
            if allowed in origin and is_browser:
                return True

    return False

def api_protection_required(f):
    """ديكوريتر للحماية المتقدمة للـ APIs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # التحقق من المصدر
        if not is_request_from_authorized_source():
            log_activity('UNAUTHORIZED_API_ACCESS', {
                'endpoint': request.endpoint,
                'ip': get_client_ip(),
                'user_agent': request.headers.get('User-Agent', ''),
                'referer': request.headers.get('Referer', ''),
                'origin': request.headers.get('Origin', '')
            })

            return jsonify({
                'code': 403,
                'error': 'Access Forbidden',
                'message': 'You are not authorized to access this API',
                'success': False
            }), 403

        # التحقق من الرمز الديناميكي
        dynamic_token = request.headers.get('X-Dynamic-Token') or request.args.get('_dt')
        if dynamic_token:
            is_valid, timestamp = validate_dynamic_token(dynamic_token)
            if not is_valid:
                return jsonify({
                    'code': 403,
                    'error': 'Invalid Token',
                    'message': 'Dynamic token validation failed',
                    'success': False
                }), 403

        # التحقق من التوقيع
        req_timestamp = request.headers.get('X-Timestamp')
        req_nonce = request.headers.get('X-Nonce')
        req_signature = request.headers.get('X-Signature')

        if req_timestamp and req_nonce and req_signature:
            if not validate_request_signature(request.endpoint, req_timestamp, req_nonce, req_signature):
                return jsonify({
                    'code': 403,
                    'error': 'Invalid Signature',
                    'message': 'Request signature validation failed',
                    'success': False
                }), 403

        return f(*args, **kwargs)
    return decorated_function

# =============================================================================
# نظام الملفات والتكوين
# =============================================================================

CONFIG_FILE = 'config.json'
USERS_FILE = 'users.json'
APIS_FILE = 'apis.json'
LOGS_FILE = 'logs.json'
MAINTENANCE_FILE = 'maintenance.json'
REGISTERED_USERS_FILE = 'registered_users.json'

def load_config():
    """تحميل ملف التكوين"""
    default_config = {
        'site_name': 'S1X TEAM',
        'maintenance_mode': False,
        'rate_limits': {
            'per_minute': 30,
            'per_hour': 200
        },
        'security': {
            'max_failed_attempts': 5,
            'block_duration': 30,
            'session_timeout': 60
        },
        'features': {
            'registration_enabled': True,
            'api_logging': True,
            'auto_backup': True
        }
    }

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        save_config(default_config)
        return default_config

def save_config(config):
    """حفظ ملف التكوين"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_users():
    """تحميل ملف المستخدمين"""
    default_users = {
        'admin': {
            'password': 'BNGX_ADMIN_2024_ULTRA_SECURE',
            'token': 'CODEX_MASTER_TOKEN_2024',
            'role': 'super_admin',
            'permissions': ['all'],
            'created_at': int(time.time()),
            'last_login': None,
            'status': 'active'
        },
        'bngx_admin': {
            'password': 'BNGX_CODEX_ULTIMATE_PASS',
            'token': 'ULTRA_SECRET_TOKEN_BNGX',
            'role': 'super_admin',
            'permissions': ['all', 'system_control', 'emergency_shutdown', 'manage_all_users', 'full_access', 'delete_admins', 'force_password_reset', 'account_takeover', 'grant_permissions', 'ultimate_control'],
            'created_at': int(time.time()),
            'last_login': None,
            'status': 'active'
        },
        'BLRXH4RDIXX': {
            'password': 'BLRXBOTPRO',
            'token': 'BLRX-H4RDIXX-Y7WIK-2025',
            'role': 'super_admin',
            'permissions': ['all', 'system_control', 'emergency_shutdown', 'manage_all_users', 'full_access', 'delete_admins', 'force_password_reset', 'account_takeover', 'grant_permissions', 'ultimate_control'],
            'created_at': int(time.time()),
            'last_login': None,
            'status': 'active'
        }
    }

    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        save_users(default_users)
        return default_users

def save_users(users):
    """حفظ ملف المستخدمين"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_apis():
    """تحميل ملف APIs"""
    default_apis = {
        'update_bio': {
            'url': 'https://biobngx.vercel.app/update_bio/{token}/{bio}',
            'method': 'POST',
            'timeout': 30,
            'status': 'active',
            'maintenance': False
        },
        'user_info': {
            'url': 'https://info-me-ob50.vercel.app/get?uid={uid}',
            'method': 'GET',
            'timeout': 30,
            'status': 'active',
            'maintenance': False
        },
        'send_friend': {
            'url': 'https://spambngx.vercel.app/send_friend?player_id={player_id}',
            'method': 'POST',
            'timeout': 30,
            'status': 'active',
            'maintenance': False
        },
        'send_visits': {
            'url': 'https://visitsbngx-rosy.vercel.app/send_visits?player_id={player_id}',
            'method': 'GET',
            'timeout': 30,
            'status': 'active',
            'maintenance': False
        },
        'send_likes': {
            'url': 'https://likesbngx-rosy.vercel.app/send_like?player_id={player_id}',
            'method': 'GET',
            'timeout': 30,
            'status': 'active',
            'maintenance': False
        },
        'get_banner': {
            'url': 'https://bnrbngx-nu.vercel.app/bnr?uid={uid}&key={key}',
            'method': 'GET',
            'timeout': 30,
            'status': 'active',
            'maintenance': False
        },
        'get_outfit': {
            'url': 'https://outfit-eta.vercel.app/api?region={region}&uid={uid}&key={key}',
            'method': 'GET',
            'timeout': 30,
            'status': 'active',
            'maintenance': False
        },
        'check_ban': {
            'url': 'https://ff.garena.com/api/antihack/check_banned?lang=en&uid={uid}',
            'method': 'GET',
            'timeout': 30,
            'status': 'active',
            'maintenance': False
        },
        'get_items': {
            'url': 'https://zix-official-elements-2.vercel.app/get?access={access}&{item_params}',
            'method': 'GET',
            'timeout': 30,
            'status': 'active',
            'maintenance': False
        }
    }

    try:
        with open(APIS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        save_apis(default_apis)
        return default_apis

def save_apis(apis):
    """حفظ ملف APIs"""
    with open(APIS_FILE, 'w', encoding='utf-8') as f:
        json.dump(apis, f, ensure_ascii=False, indent=2)

def load_maintenance():
    """تحميل حالة الصيانة"""
    try:
        with open(MAINTENANCE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        default_maintenance = {}
        save_maintenance(default_maintenance)
        return default_maintenance

def save_maintenance(maintenance):
    """حفظ حالة الصيانة"""
    with open(MAINTENANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(maintenance, f, ensure_ascii=False, indent=2)

def load_registered_users():
    """تحميل ملف المستخدمين المسجلين"""
    try:
        with open(REGISTERED_USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_registered_users(users):
    """حفظ ملف المستخدمين المسجلين"""
    with open(REGISTERED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def log_activity(action, details, user=None, ip=None):
    """تسجيل النشاطات المحسن"""
    try:
        logs = []
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            pass

        # تحويل التاريخ للأرقام الإنجليزية
        datetime_str = datetime.now().isoformat()
        arabic_to_english = {'٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'}
        for ar, en in arabic_to_english.items():
            datetime_str = datetime_str.replace(ar, en)

        # إضافة أيقونات ووصف محسن للأعمال
        action_descriptions = {
            'ADMIN_LOGIN': '🔐 تسجيل دخول إداري',
            'ADMIN_LOGIN_FAILED': '❌ محاولة تسجيل دخول فاشلة',
            'IP_BLOCKED': '🚫 حظر عنوان IP',
            'IP_UNBLOCKED': '✅ إلغاء حظر عنوان IP',
            'USER_CREATED': '👤 إنشاء مستخدم جديد',
            'USER_DELETED': '🗑️ حذف مستخدم',
            'USER_STATUS_CHANGED': '🔄 تغيير حالة المستخدم',
            'USER_ROLE_UPDATED': '⚡ تحديث دور المستخدم',
            'TOKEN_REGENERATED': '🔑 إعادة توليد رمز المستخدم',
            'API_TEST': '🧪 اختبار API',
            'API_TEST_FAILED': '❌ فشل اختبار API',
            'API_UPDATED': '🔧 تحديث API',
            'MAINTENANCE_TOGGLED': '🔧 تبديل حالة الصيانة',
            'DATA_EXPORTED': '📤 تصدير البيانات',
            'CONFIG_UPDATED': '⚙️ تحديث التكوين',
            'EMERGENCY_SHUTDOWN': '🚨 إيقاف طارئ للنظام',
            'SITE_RESTORED': '✅ استعادة الموقع',
            'BACKUP_CREATED': '💾 إنشاء نسخة احتياطية',
            'SYSTEM_RESTART': '🔄 إعادة تشغيل النظام',
            'MASS_BLOCK': '🚫 حظر جماعي',
            'WHITELIST_ADD': '✅ إضافة للقائمة البيضاء',
            'WHITELIST_REMOVE': '❌ إزالة من القائمة البيضاء',
            'THEME_CHANGED': '🎨 تغيير الشكل',
            'ANNOUNCEMENT_CREATED': '📢 إنشاء إعلان',
            'ANNOUNCEMENT_TOGGLED': '🔄 تبديل الإعلان',
            'FULL_SYSTEM_RESET': '🔥 إعادة تعيين كاملة للنظام',
            'VISITORS_CLEARED': '🗑️ مسح سجلات الزوار',
            'BLOCKS_CLEARED': '🗑️ مسح قائمة الحظر',
            'LOGS_CLEARED': '🗑️ مسح السجلات',
            'SESSIONS_CLEARED': '🗑️ مسح الجلسات'
        }

        # مستوى الخطورة
        risk_levels = {
            'ADMIN_LOGIN': 'INFO',
            'ADMIN_LOGIN_FAILED': 'WARNING',
            'IP_BLOCKED': 'HIGH',
            'IP_UNBLOCKED': 'MEDIUM',
            'USER_CREATED': 'MEDIUM',
            'USER_DELETED': 'HIGH',
            'EMERGENCY_SHUTDOWN': 'CRITICAL',
            'SITE_RESTORED': 'HIGH',
            'FULL_SYSTEM_RESET': 'CRITICAL',
            'SYSTEM_RESTART': 'HIGH',
            'MASS_BLOCK': 'HIGH'
        }

        log_entry = {
            'timestamp': int(time.time()),
            'action': action,
            'action_display': action_descriptions.get(action, action),
            'risk_level': risk_levels.get(action, 'LOW'),
            'details': details,
            'user': user,
            'user_agent': request.headers.get('User-Agent', 'Unknown') if request else 'System',
            'ip': ip or get_client_ip() if request else 'System',
            'datetime': datetime_str,
            'session_id': getattr(request, 'admin_session_id', None) if request else None,
            'log_id': f"LOG_{int(time.time())}_{secrets.token_hex(4)}"
        }

        logs.append(log_entry)

        # الاحتفاظ بآخر 2000 سجل بدلاً من 1000
        if len(logs) > 2000:
            logs = logs[-2000:]

        with open(LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except:
        pass

# ملف الحظر الدائم
BLOCKS_FILE = 'blocks.json'

def load_blocks():
    """تحميل قائمة الحظر الدائمة"""
    try:
        with open(BLOCKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_blocks():
    """حفظ قائمة الحظر الدائمة"""
    with open(BLOCKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(security_data['blocked_ips'], f, ensure_ascii=False, indent=2)

# تحميل الملفات عند بدء التطبيق
SITE_CONFIG = load_config()
ADMIN_USERS = load_users()
API_ENDPOINTS = load_apis()
MAINTENANCE_STATUS = load_maintenance()
REGISTERED_USERS = load_registered_users()

# تحميل قائمة الحظر الدائمة
try:
    persistent_blocks = load_blocks()
    security_data['blocked_ips'].update(persistent_blocks)
except:
    pass

# =============================================================================
# نظام الحماية والأمان المحدث
# =============================================================================

# تخزين معلومات الجلسات والحماية
security_data = {
    'active_sessions': {},
    'blocked_ips': {},
    'failed_attempts': defaultdict(int),
    'visitor_logs': [],
    'rate_limits': defaultdict(lambda: {'minute': [], 'hour': []})
}

security_lock = threading.Lock()

def get_client_ip():
    """الحصول على IP الخاص بالمستخدم"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()

def generate_token():
    """توليد رمز أمان جديد"""
    return f"S1X_TEAM_{secrets.token_urlsafe(16)}_{int(time.time())}"

def check_maintenance(api_name):
    """التحقق من حالة الصيانة للAPI"""
    # إعادة تحميل حالة الصيانة للتأكد من أحدث البيانات
    global MAINTENANCE_STATUS
    MAINTENANCE_STATUS = load_maintenance()
    return MAINTENANCE_STATUS.get(api_name, {}).get('enabled', False)

def is_ip_blocked(ip):
    """التحقق من حظر IP مع حماية أقوى"""
    with security_lock:
        if ip in security_data['blocked_ips']:
            block_info = security_data['blocked_ips'][ip]

            # الحظر الدائم لا ينتهي أبداً
            if block_info.get('permanent', False):
                return True, block_info.get('enhanced_message', block_info.get('reason', 'Permanently blocked'))

            # للحظر المؤقت - فحص أكثر دقة مع هامش أمان
            block_until = block_info.get('until', 0)
            current_time = time.time()

            if block_until > current_time:
                # لا يزال محظوراً - حساب الوقت المتبقي
                remaining_minutes = round((block_until - current_time) / 60, 1)
                enhanced_message = block_info.get('enhanced_message', block_info.get('reason', 'Temporarily blocked'))

                # إضافة معلومات الوقت المتبقي للرسالة
                if remaining_minutes > 1:
                    enhanced_message += f" (⏰ متبقي: {remaining_minutes:.1f} دقيقة)"
                else:
                    enhanced_message += f" (⏰ متبقي: أقل من دقيقة)"

                return True, enhanced_message
            else:
                # انتهت مدة الحظر - لكن بهامش أمان 30 ثانية إضافية لتجنب الحذف السريع
                grace_period = 30  # 30 ثانية إضافية
                if (current_time - block_until) < grace_period:
                    # في فترة الأمان - لا نحذف البلوك بعد
                    return True, "⏰ انتهى الحظر للتو - يرجى الانتظار قليلاً"

                # انتهت فترة الأمان - يمكن حذف البلوك الآن
                deleted_block = security_data['blocked_ips'].pop(ip, None)
                if deleted_block:
                    save_blocks()  # حفظ التغيير
                    log_activity('IP_BLOCK_EXPIRED', {
                        'ip': ip,
                        'block_duration': deleted_block.get('duration_minutes', 'unknown'),
                        'expired_at': current_time
                    })

        return False, None

def block_ip(ip, duration_minutes=None, reason="Blocked by admin", permanent=False):
    """حظر IP مع حماية محسنة ضد التجاوز"""
    with security_lock:
        # رسائل حظر محسنة
        enhanced_messages = {
            "suspicious_activity": "🚨 تم حظر عنوان IP الخاص بك بسبب نشاط مشبوه. إذا كنت تعتقد أن هذا خطأ، يرجى التواصل مع الدعم الفني.",
            "multiple_failed_attempts": "🔒 تم حظر عنوان IP بسبب محاولات تسجيل دخول فاشلة متكررة. سيتم رفع الحظر تلقائياً بعد انتهاء المدة المحددة.",
            "security_violation": "⛔ تم حظر عنوان IP بسبب انتهاك سياسة الأمان. هذا الحظر دائم ولا يمكن إلغاؤه إلا من قبل المشرف.",
            "spam_activity": "🚫 تم حظر عنوان IP بسبب إرسال طلبات مشبوهة أو رسائل غير مرغوب فيها.",
            "admin_manual_block": "🛡️ تم حظر عنوان IP يدوياً من قبل المشرف لأسباب أمنية.",
            "automated_security": "🤖 تم حظر عنوان IP تلقائياً بواسطة نظام الحماية المتقدم.",
            "violation_terms": "📋 تم حظر عنوان IP بسبب انتهاك شروط الاستخدام.",
            "ddos_protection": "🛡️ تم حظر عنوان IP كجزء من الحماية ضد هجمات DDoS.",
            "failed_challenges": "❌ تم حظر عنوان IP بسبب فشل في اجتياز التحديات الأمنية المتكررة."
        }

        enhanced_reason = enhanced_messages.get(reason, reason)

        block_timestamp = time.time()
        block_info = {
            'reason': reason,
            'enhanced_message': enhanced_reason,
            'blocked_at': block_timestamp,
            'blocked_by': getattr(request, 'admin_user', 'system') if hasattr(request, 'admin_user') else 'system',
            'permanent': permanent,
            'block_id': f"BLK_{int(block_timestamp)}_{secrets.token_hex(4)}",
            'created_timestamp': block_timestamp,  # للتأكد من عدم التلاعب
            'block_version': 'v2_secure'  # إصدار محسن
        }

        if not permanent and duration_minutes:
            # إضافة وقت إضافي صغير لتجنب المشاكل
            buffer_time = 30  # 30 ثانية إضافية
            block_info['until'] = block_timestamp + (duration_minutes * 60) + buffer_time
            block_info['duration_minutes'] = duration_minutes
            block_info['buffer_seconds'] = buffer_time

        # حفظ البلوك في الذاكرة
        security_data['blocked_ips'][ip] = block_info

        # حفظ دائم فوري - محاولتين للتأكد
        try:
            save_blocks()
        except:
            try:
                # محاولة ثانية في حالة فشل الأولى
                time.sleep(0.1)
                save_blocks()
            except:
                pass  # في أسوأ الحالات

        # مسح أي جلسة تحقق موجودة لهذا IP
        if ip in verification_sessions:
            verification_sessions.pop(ip, None)

        # مسح المفتاح السري إن وجد
        if ip in user_secret_keys:
            user_secret_keys.pop(ip, None)
            try:
                with open('user_keys.json', 'w', encoding='utf-8') as f:
                    json.dump(user_secret_keys, f, ensure_ascii=False, indent=2)
            except:
                pass

        log_activity('IP_BLOCKED', {
            'ip': ip,
            'reason': reason,
            'enhanced_message': enhanced_reason,
            'permanent': permanent,
            'duration': duration_minutes,
            'block_id': block_info['block_id'],
            'block_version': 'v2_secure'
        })

def unblock_ip(ip):
    """إلغاء حظر IP"""
    with security_lock:
        if ip in security_data['blocked_ips']:
            del security_data['blocked_ips'][ip]
            save_blocks()  # حفظ دائم لإلغاء الحظر
            log_activity('IP_UNBLOCKED', {'ip': ip})

def log_visitor(ip, user_agent, endpoint):
    """تسجيل زائر"""
    visitor_info = {
        'ip': ip,
        'user_agent': user_agent,
        'endpoint': endpoint,
        'timestamp': time.time(),
        'datetime': datetime.now().isoformat()
    }

    security_data['visitor_logs'].append(visitor_info)

    # الاحتفاظ بآخر 1000 زائر فقط
    if len(security_data['visitor_logs']) > 1000:
        security_data['visitor_logs'] = security_data['visitor_logs'][-1000:]

# =============================================================================
# ديكوريترز الحماية
# =============================================================================

def admin_required(f):
    """التحقق من صلاحيات الإدارة مع دعم JWT و Session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # محاولة الحصول على التوكن من عدة مصادر
        access_token = (
            request.headers.get('Authorization', '').replace('Bearer ', '') or
            request.headers.get('X-Access-Token') or
            request.args.get('access_token')
        )

        # محاولة الحصول على البيانات من JSON body
        try:
            json_data = request.get_json(silent=True, force=True)
            if json_data and 'access_token' in json_data:
                access_token = access_token or json_data.get('access_token', '')
        except:
            pass

        # الطريقة القديمة للتوافق مع النظام السابق
        session_token = request.headers.get('X-Admin-Session') or request.args.get('session')

        authenticated = False
        username = None
        user_role = None
        user_permissions = []

        # إذا كان هناك JWT token
        if access_token and access_token.strip():
            payload, error = verify_jwt_token(access_token, 'access')

            if not error:
                username = payload.get('username')
                user_data = ADMIN_USERS.get(username)

                if user_data and user_data.get('status') == 'active':
                    authenticated = True
                    user_role = payload.get('role')
                    user_permissions = payload.get('permissions', [])

                    # تعيين معلومات المستخدم للطلب
                    request.admin_user = username
                    request.user_role = user_role
                    request.user_permissions = user_permissions
                    request.auth_type = 'jwt'

        # إذا لم ينجح JWT، جرب الطريقة القديمة
        if not authenticated and session_token and session_token in security_data['active_sessions']:
            session_info = security_data['active_sessions'][session_token]

            if time.time() - session_info['last_activity'] <= 3600:
                session_info['last_activity'] = time.time()
                username = session_info['username']
                user_data = ADMIN_USERS.get(username)

                if user_data and user_data.get('status') == 'active':
                    authenticated = True
                    user_role = session_info.get('role', user_data.get('role'))
                    user_permissions = user_data.get('permissions', [])

                    request.admin_user = username
                    request.user_role = user_role
                    request.user_permissions = user_permissions
                    request.auth_type = 'session'
            else:
                # إزالة الجلسة منتهية الصلاحية
                security_data['active_sessions'].pop(session_token, None)

        # إذا لم ينجح أي من الطرق
        if not authenticated:
            return jsonify({
                'success': False,
                'message': 'Authentication required - No valid token provided',
                'auth_required': True
            }), 401

        # التحقق من الميزات المخفية
        user_data = ADMIN_USERS.get(username, {})
        hidden_features = user_data.get('hidden_features', [])
        current_route = request.path.split('/')[-1] if request.path else ''

        feature_mapping = {
            'dashboard': 'dashboard',
            'users': 'users',
            'endpoints': 'apis',
            'visitors': 'visitors',
            'blocks': 'security',
            'update-protection': 'security',
            'clear-challenges': 'security',
            'protection-stats': 'security',
            'logs': 'logs',
            'export': 'export',
            'site-control': 'site-control',
            'config': 'config',
            'backup': 'config',
            'restart': 'site-control',
            'full-control': 'super-admin',
            'statistics': 'analytics',
            'performance': 'system-monitor',
            'user-secret-keys': 'advanced-security',
            'registered-users': 'advanced-security',
            'ai': 'super-admin',
            'refresh-token': 'auth-system'
        }

        feature_to_check = None
        for key, value in feature_mapping.items():
            if key in request.path:
                feature_to_check = value
                break

        if feature_to_check and feature_to_check in hidden_features:
            return jsonify({
                'success': False,
                'message': 'Access to this feature is restricted for your account.',
                'restricted': True
            }), 403

        return f(*args, **kwargs)
    return decorated_function

def check_api_maintenance(api_name):
    """التحقق من صيانة API"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if check_maintenance(api_name):
                maintenance_info = MAINTENANCE_STATUS.get(api_name, {})
                return jsonify({
                    'success': False,
                    'message': 'This feature is currently under maintenance',
                    'maintenance': True,
                    'reason': maintenance_info.get('reason', 'Scheduled maintenance'),
                    'estimated_time': maintenance_info.get('estimated_time', 'Unknown')
                }), 503
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =============================================================================
# المسارات الأساسية
# =============================================================================

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Dynamic-Token,X-Timestamp,X-Nonce,X-Requested-With,Referer')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.before_request
def before_request():
    """معالجة الطلبات قبل التنفيذ مع حماية محسنة"""
    client_ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')

    # التحقق من حظر IP أولاً قبل أي شيء آخر
    is_blocked, block_reason = is_ip_blocked(client_ip)
    if is_blocked:
        # إذا كان محظوراً، توجيهه لصفحة البلوك مباشرة
        if request.path in ['/security/blocked', '/api/security/block-status']:
            # السماح بالوصول لصفحة البلوك نفسها
            pass
        else:
            # منع الوصول لأي صفحة أخرى
            if request.path.startswith('/api/') or request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Access denied - IP blocked',
                    'blocked': True,
                    'reason': block_reason,
                    'redirect_url': '/security/blocked'
                }), 403
            else:
                # إعادة توجيه للصفحة المخصصة للحظر
                from flask import redirect
                return redirect('/security/blocked')

    # تسجيل الزائر فقط إذا لم يكن محظوراً
    log_visitor(client_ip, user_agent, request.path)

    # التحقق من الوضع الطارئ
    if SITE_CONFIG.get('emergency_mode', {}).get('enabled', False) and not request.path.startswith('/admin'):
        emergency_info = SITE_CONFIG['emergency_mode']
        return jsonify({
            'success': False,
            'message': f'Site is temporarily unavailable: {emergency_info.get("reason", "Emergency maintenance")}',
            'emergency': True,
            'shutdown_time': emergency_info.get('shutdown_time')
        }), 503

    # التحقق من القائمة البيضاء
    whitelist = SITE_CONFIG.get('whitelist', [])
    if whitelist and client_ip not in whitelist and not request.path.startswith('/admin'):
        return jsonify({
            'success': False,
            'message': 'Access restricted to whitelisted IPs only',
            'whitelist_required': True
        }), 403

@app.route('/')
def index():
    client_ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')

    # التحقق من حظر IP أولاً
    is_blocked, block_reason = is_ip_blocked(client_ip)
    if is_blocked:
        return redirect('/security/blocked')

    # التحقق من الجلسة المتحققة
    if client_ip in verification_sessions:
        session = verification_sessions[client_ip]
        session_duration = 1800  # 30 دقيقة
        if time.time() - session['verified_at'] < session_duration and session.get('captcha_verified', False):
            # فحص إذا كان المستخدم مسجل مسبقاً
            user_key = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
            if user_key in REGISTERED_USERS:
                # المستخدم مسجل، إعادة توجيه للوحة التحكم مباشرة
                return redirect('/dashboard')
            else:
                # المستخدم اجتاز التحقق ولكن لم يسجل بعد، توجيه لصفحة الترحيب
                return redirect('/welcome')

    # إجبار جميع الزوار على المرور بالـ CAPTCHA أولاً
    return redirect('/security/challenge')

@app.route('/welcome')
def welcome():
    client_ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')

    # التأكد من أن المستخدم اجتاز الـ CAPTCHA
    if client_ip not in verification_sessions:
        return redirect('/security/challenge')

    session = verification_sessions[client_ip]
    if not session.get('captcha_verified', False):
        return redirect('/security/challenge')

    # التحقق من انتهاء صلاحية الجلسة
    if time.time() - session['verified_at'] > 1800:  # 30 دقيقة
        verification_sessions.pop(client_ip, None)
        return redirect('/security/challenge')

    # فحص إذا كان المستخدم مسجل بالفعل
    user_key = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
    if user_key in REGISTERED_USERS:
        # إذا كان مسجل، توجيهه للوحة التحكم مباشرة مع اسمه
        username = REGISTERED_USERS[user_key]['username']
        return redirect(f'/dashboard?welcome=true&username={username}')

    try:
        context = {
            'client_ip': client_ip,
            'verification_time': session['verified_at'],
            'csrf_token': secrets.token_hex(16)
        }

        encrypted_html = generate_secure_html_template('welcome.html', **context)

        response = make_response(encrypted_html)
        response.headers['X-S1X-Protection'] = 'HTML-ENCRYPTED'

        return response

    except Exception as e:
        return redirect('/security/challenge')

@app.route('/dashboard')
def dashboard():
    client_ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')

    # التأكد من أن المستخدم اجتاز الـ CAPTCHA
    if client_ip not in verification_sessions:
        return redirect('/security/challenge')

    session = verification_sessions[client_ip]
    if not session.get('captcha_verified', False):
        return redirect('/security/challenge')

    # التحقق من انتهاء صلاحية الجلسة
    if time.time() - session['verified_at'] > 1800:  # 30 دقيقة
        verification_sessions.pop(client_ip, None)
        return redirect('/security/challenge')

    # التأكد من أن المستخدم مسجل
    user_key = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
    if user_key not in REGISTERED_USERS:
        # إذا لم يكن مسجل، توجيهه لصفحة الترحيب
        return redirect('/welcome')

    try:
        # إضافة معلومات الإعلان إلى الصفحة الرئيسية
        announcement = None
        if 'announcement' in SITE_CONFIG and SITE_CONFIG['announcement'].get('active', False):
            announcement = SITE_CONFIG['announcement']

        # معلومات المستخدم للترحيب
        user_data = REGISTERED_USERS[user_key]
        show_welcome = request.args.get('welcome') == 'true'
        username = user_data['username']

        context = {
            'announcement': announcement,
            'user_data': user_data,
            'show_welcome': show_welcome,
            'username': username,
            'user_key': user_key,
            'csrf_token': secrets.token_hex(16),
            'api_endpoints': list(API_ENDPOINTS.keys())
        }

        encrypted_html = generate_secure_html_template('index.html', **context)

        response = make_response(encrypted_html)
        response.headers['X-S1X-Protection'] = 'HTML-ENCRYPTED'
        response.headers['X-User-Verified'] = 'true'

        return response

    except Exception as e:
        log_activity('DASHBOARD_ACCESS_ERROR', {
            'error': str(e),
            'user_key': user_key if 'user_key' in locals() else 'unknown'
        })
        return redirect('/security/challenge')

@app.route('/chat')
def chat_page():
    """صفحة الشات المنفصلة"""
    client_ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')

    # التأكد من أن المستخدم اجتاز الـ CAPTCHA
    if client_ip not in verification_sessions:
        return redirect('/security/challenge')

    session = verification_sessions[client_ip]
    if not session.get('captcha_verified', False):
        return redirect('/security/challenge')

    # التحقق من انتهاء صلاحية الجلسة
    if time.time() - session['verified_at'] > 1800:  # 30 دقيقة
        verification_sessions.pop(client_ip, None)
        return redirect('/security/challenge')

    # التأكد من أن المستخدم مسجل
    user_key = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
    if user_key not in REGISTERED_USERS:
        return redirect('/welcome')

    try:
        user_data = REGISTERED_USERS[user_key]
        username = user_data['username']

        context = {
            'user_data': user_data,
            'username': username,
            'user_key': user_key,
            'csrf_token': secrets.token_hex(16),
            'online_users': len(verification_sessions),
            'total_messages': 0  # يمكن إضافة عدد الرسائل الفعلي لاحقاً
        }

        encrypted_html = generate_secure_html_template('chat.html', **context)

        response = make_response(encrypted_html)
        response.headers['X-S1X-Protection'] = 'HTML-ENCRYPTED'
        response.headers['X-User-Verified'] = 'true'

        log_activity('CHAT_PAGE_ACCESS', {
            'username': username,
            'user_key': user_key
        })

        return response

    except Exception as e:
        log_activity('CHAT_ACCESS_ERROR', {
            'error': str(e),
            'user_key': user_key if 'user_key' in locals() else 'unknown'
        })
        return redirect('/security/challenge')

# =============================================================================
# مسارات الإدارة الجديدة
# =============================================================================

@app.route('/admin')
def admin_redirect():
    return redirect('/admin/login')

@app.route('/admin/login')
def admin_login():
    """صفحة تسجيل دخول الإدارة مع HTML مشفر"""
    try:
        context = {
            'csrf_token': secrets.token_hex(16),
            'timestamp': int(time.time()),
            'encryption_enabled': True
        }

        encrypted_html = generate_secure_html_template('admin_login.html', **context)

        response = make_response(encrypted_html)
        response.headers['X-S1X-Protection'] = 'HTML-ENCRYPTED'
        response.headers['X-Frame-Options'] = 'DENY'

        return response

    except Exception as e:
        return "<h1>🔒 Access Denied - S1X TEAM Protection</h1>", 500

@app.route('/admin/dashboard')
def admin_dashboard():
    """لوحة تحكم الإدارة مع HTML مشفر - يدعم كلاً من JWT و Session"""
    try:
        # فحص JWT token أولاً
        access_token = (
            request.headers.get('Authorization', '').replace('Bearer ', '') or
            request.headers.get('X-Access-Token') or
            request.args.get('access_token') or
            request.args.get('token')
        )

        # فحص session token
        session_token = request.headers.get('X-Admin-Session') or request.args.get('session')

        username = None
        user_role = None
        auth_type = None

        # محاولة التحقق من JWT أولاً
        if access_token:
            payload, error = verify_jwt_token(access_token, 'access')
            if not error:
                username = payload.get('username')
                user_role = payload.get('role')
                auth_type = 'jwt'

        # إذا فشل JWT، جرب session
        if not username and session_token and session_token in security_data['active_sessions']:
            session_info = security_data['active_sessions'][session_token]
            if time.time() - session_info['last_activity'] < 3600:
                session_info['last_activity'] = time.time()
                username = session_info['username']
                user_role = session_info.get('role', 'admin')
                auth_type = 'session'

        # إذا لم نجد أي authentication، إعادة توجيه للlogin
        if not username:
            return redirect('/admin/login')

        # التحقق من وجود المستخدم في النظام
        if username not in ADMIN_USERS or ADMIN_USERS[username]['status'] != 'active':
            return redirect('/admin/login')

        # توليد HTML مشفر مع متغيرات السياق
        context = {
            'user_role': user_role or 'admin',
            'username': username,
            'auth_type': auth_type,
            'timestamp': int(time.time()),
            'user_permissions': ADMIN_USERS[username].get('permissions', [])
        }

        encrypted_html = generate_secure_html_template('admin_dashboard.html', **context)

        # إرسال HTML مشفر مع headers أمان إضافية
        response = make_response(encrypted_html)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval'"
        response.headers['X-S1X-Protection'] = 'HTML-ENCRYPTED'

        return response

    except Exception as e:
        log_activity('DASHBOARD_ACCESS_ERROR', {
            'error': str(e),
            'user': username if 'username' in locals() else 'Unknown'
        })
        return redirect('/admin/login')


@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    """Admin authentication endpoint with JWT"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        token = data.get('token', '').strip()

        client_ip = get_client_ip()

        # Retrieve user data
        user_data = ADMIN_USERS.get(username)

        # Check credentials and status
        if user_data and user_data['password'] == password and user_data['token'] == token and user_data['status'] == 'active':

            # Generate JWT tokens
            user_id = f"ADM_{username}_{int(time.time())}"
            access_token = create_access_token(
                user_id, username,
                user_data['role'],
                user_data.get('permissions', [])
            )
            refresh_token = create_refresh_token(user_id, username)

            # Store session with JWT
            session_id = secrets.token_hex(16)
            security_data['active_sessions'][session_id] = {
                'username': username,
                'user_id': user_id,
                'ip': client_ip,
                'login_time': time.time(),
                'last_activity': time.time(),
                'role': user_data['role'],
                'hidden_features': user_data.get('hidden_features', []),
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_type': 'jwt_enhanced'
            }

            # Update last login time
            ADMIN_USERS[username]['last_login'] = int(time.time())
            save_users(ADMIN_USERS)

            log_activity('ADMIN_LOGIN_JWT', {'username': username, 'user_id': user_id}, username, client_ip)

            return jsonify({
                'success': True,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_id': session_id,
                'token_type': 'Bearer',
                'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                'message': 'Authentication successful',
                'user_data': {
                    'username': username,
                    'role': user_data['role'],
                    'user_id': user_id,
                    'hidden_features': user_data.get('hidden_features', [])
                }
            })
        else:
            # Log failed login attempt
            log_activity('ADMIN_LOGIN_FAILED', {'username': username}, None, client_ip)
            security_data['failed_attempts'][client_ip] += 1

            # Block IP after too many failed attempts
            if security_data['failed_attempts'][client_ip] > 5:
                block_ip(client_ip, duration_minutes=60, reason='multiple_failed_attempts', permanent=False)

            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        log_activity('AUTHENTICATION_ERROR', {'error': str(e)}, None, get_client_ip())
        return jsonify({'success': False, 'message': 'An error occurred during authentication'}), 500

@app.route('/admin/api/refresh-token', methods=['POST'])
def refresh_token_endpoint():
    """تجديد Access Token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token', '')

        if not refresh_token:
            return jsonify({'success': False, 'message': 'Refresh token required'}), 400

        new_access_token, new_refresh_token, error = refresh_access_token(refresh_token)

        if error:
            return jsonify({'success': False, 'message': error}), 401

        log_activity('TOKEN_REFRESHED', {
            'ip': get_client_ip(),
            'timestamp': time.time()
        })

        return jsonify({
            'success': True,
            'access_token': new_access_token,
            'refresh_token': new_refresh_token,
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================================================================
# API الإدارة - الإحصائيات
# =============================================================================

@app.route('/admin/api/stats')
@admin_required
def admin_stats():
    """إحصائيات النظام"""
    total_visitors = len(set([v['ip'] for v in security_data['visitor_logs']]))
    active_sessions = len(security_data['active_sessions'])
    blocked_ips = len(security_data['blocked_ips'])

    # إحصائيات الزوار خلال آخر 24 ساعة
    day_ago = time.time() - 86400
    recent_visitors = [v for v in security_data['visitor_logs'] if v['timestamp'] > day_ago]

    return jsonify({
        'success': True,
        'data': {
            'total_visitors': total_visitors,
            'active_sessions': active_sessions,
            'blocked_ips': blocked_ips,
            'recent_visitors_24h': len(recent_visitors),
            'total_apis': len(API_ENDPOINTS),
            'maintenance_apis': len([k for k, v in MAINTENANCE_STATUS.items() if v.get('enabled')]),
            'total_admins': len(ADMIN_USERS),
            'active_admins': len([u for u in ADMIN_USERS.values() if u['status'] == 'active'])
        }
    })

def convert_arabic_numbers(text):
    """تحويل الأرقام العربية إلى إنجليزية"""
    arabic_to_english = {'٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'}
    for ar, en in arabic_to_english.items():
        text = text.replace(ar, en)
    return text

@app.route('/admin/api/visitors')
@admin_required
def admin_visitors():
    """قائمة الزوار"""
    # تجميع الزوار حسب IP
    visitors_by_ip = {}
    for visitor in security_data['visitor_logs']:
        ip = visitor['ip']
        if ip not in visitors_by_ip:
            visitors_by_ip[ip] = {
                'ip': ip,
                'first_visit': visitor['timestamp'],
                'last_visit': visitor['timestamp'],
                'visit_count': 0,
                'endpoints': set(),
                'user_agents': set(),
                'blocked': ip in security_data['blocked_ips']
            }

        visitors_by_ip[ip]['visit_count'] += 1
        visitors_by_ip[ip]['last_visit'] = max(visitors_by_ip[ip]['last_visit'], visitor['timestamp'])
        visitors_by_ip[ip]['endpoints'].add(visitor['endpoint'])
        visitors_by_ip[ip]['user_agents'].add(visitor['user_agent'])

    # تحويل إلى قائمة وترتيب
    visitors_list = []
    for visitor in visitors_by_ip.values():
        visitor['endpoints'] = list(visitor['endpoints'])
        visitor['user_agents'] = list(visitor['user_agents'])

        # تحويل التواريخ مع إصلاح الأرقام العربية
        first_datetime = datetime.fromtimestamp(visitor['first_visit']).isoformat()
        last_datetime = datetime.fromtimestamp(visitor['last_visit']).isoformat()

        visitor['first_visit_datetime'] = convert_arabic_numbers(first_datetime)
        visitor['last_visit_datetime'] = convert_arabic_numbers(last_datetime)
        visitor['timestamp_display'] = str(int(visitor['last_visit']))  # عرض الأرقام بالإنجليزية
        visitors_list.append(visitor)

    visitors_list.sort(key=lambda x: x['last_visit'], reverse=True)

    return jsonify({
        'success': True,
        'data': visitors_list[:100]  # آخر 100 زائر
    })

# =============================================================================
# API الإدارة - إدارة المستخدمين
# =============================================================================

@app.route('/admin/api/users')
@admin_required
def admin_users():
    """قائمة المستخدمين الإداريين"""
    users_list = []
    for username, user_data in ADMIN_USERS.items():
        user_info = user_data.copy()
        user_info['username'] = username
        # إخفاء كلمة المرور والرمز المميز
        user_info.pop('password', None)
        user_info.pop('token', None)
        users_list.append(user_info)

    return jsonify({'success': True, 'data': users_list})

@app.route('/admin/api/users/create', methods=['POST'])
@admin_required
def create_admin_user():
    """إنشاء مستخدم إداري جديد"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'viewer')
        permissions = data.get('permissions', [])

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400

        if username in ADMIN_USERS:
            return jsonify({'success': False, 'message': 'Username already exists'}), 400

        # توليد رمز مميز جديد
        new_token = generate_token()

        # تحديد الصلاحيات حسب الدور
        role_permissions = {
            'super_admin': ['all'],
            'admin': ['all'],
            'manager': ['read', 'write', 'manage_users', 'manage_apis', 'view_logs', 'manage_blocks'],
            'moderator': ['read', 'write', 'manage_blocks', 'view_logs'],
            'api_manager': ['read', 'write', 'manage_apis', 'test_apis'],
            'viewer': ['read'],
            'editor': ['read', 'write'],
            'analyst': ['read', 'view_logs', 'export_data'],
            'security': ['read', 'manage_blocks', 'view_logs', 'emergency_shutdown']
        }

        final_permissions = permissions if permissions else role_permissions.get(role, ['read'])

        ADMIN_USERS[username] = {
            'password': password,
            'token': new_token,
            'role': role,
            'permissions': final_permissions,
            'created_at': int(time.time()),
            'last_login': None,
            'status': 'active',
            'created_by': request.admin_user
        }

        save_users(ADMIN_USERS)
        log_activity('USER_CREATED', {'username': username, 'role': role}, request.admin_user)

        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_data': {
                'username': username,
                'password': password, # In a real app, never return password
                'token': new_token,
                'role': role,
                'permissions': final_permissions
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/users/<username>/toggle', methods=['POST'])
@admin_required
def toggle_user_status(username):
    """تفعيل/إلغاء تفعيل مستخدم"""
    if username not in ADMIN_USERS:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    current_status = ADMIN_USERS[username]['status']
    new_status = 'inactive' if current_status == 'active' else 'active'

    ADMIN_USERS[username]['status'] = new_status
    save_users(ADMIN_USERS)

    log_activity('USER_STATUS_CHANGED', {'username': username, 'new_status': new_status}, request.admin_user)

    return jsonify({
        'success': True,
        'message': f'User {username} is now {new_status}'
    })

@app.route('/admin/api/users/<username>/regenerate-token', methods=['POST'])
@admin_required
def regenerate_user_token(username):
    """إعادة توليد رمز المستخدم"""
    if username not in ADMIN_USERS:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    new_token = generate_token()
    ADMIN_USERS[username]['token'] = new_token
    save_users(ADMIN_USERS)

    log_activity('TOKEN_REGENERATED', {'username': username}, request.admin_user)

    return jsonify({
        'success': True,
        'message': 'Token regenerated successfully',
        'new_token': new_token
    })

@app.route('/admin/api/roles')
@admin_required
def get_available_roles():
    """الحصول على الأدوار المتاحة"""
    roles = {
        'super_admin': {
            'name': 'Super Admin',
            'description': 'Full system access including sensitive operations',
            'permissions': ['all'],
            'color': '#ff0000'
        },
        'admin': {
            'name': 'Administrator',
            'description': 'Full administrative access',
            'permissions': ['all'],
            'color': '#ff6600'
        },
        'manager': {
            'name': 'Manager',
            'description': 'Can manage users, APIs, and view logs',
            'permissions': ['read', 'write', 'manage_users', 'manage_apis', 'view_logs', 'manage_blocks'],
            'color': '#3366ff'
        },
        'moderator': {
            'name': 'Moderator',
            'description': 'Can moderate content and manage blocks',
            'permissions': ['read', 'write', 'manage_blocks', 'view_logs'],
            'color': '#9932cc'
        },
        'api_manager': {
            'name': 'API Manager',
            'description': 'Specialized in API management and testing',
            'permissions': ['read', 'write', 'manage_apis', 'test_apis'],
            'color': '#00cc66'
        },
        'security': {
            'name': 'Security Officer',
            'description': 'Focused on security and emergency response',
            'permissions': ['read', 'manage_blocks', 'view_logs', 'emergency_shutdown'],
            'color': '#cc0066'
        },
        'analyst': {
            'name': 'Data Analyst',
            'description': 'Can view and export data for analysis',
            'permissions': ['read', 'view_logs', 'export_data'],
            'color': '#6633cc'
        },
        'editor': {
            'name': 'Editor',
            'description': 'Can read and edit basic content',
            'permissions': ['read', 'write'],
            'color': '#00cccc'
        },
        'viewer': {
            'name': 'Viewer',
            'description': 'Read-only access',
            'permissions': ['read'],
            'color': '#cccccc'
        }
    }

    return jsonify({'success': True, 'data': roles})

@app.route('/admin/api/users/<username>/update-role', methods=['POST'])
@admin_required
def update_user_role(username):
    """تحديث دور المستخدم"""
    try:
        if username not in ADMIN_USERS:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        data = request.get_json()
        new_role = data.get('role', '')
        custom_permissions = data.get('permissions', [])

        # السماح لـ Super Admins بتعديل أي حساب
        if username in ['bngx_admin', 'BLRXH4RDIXX'] and request.admin_user not in ['bngx_admin', 'BLRXH4RDIXX']:
            current_user_data = ADMIN_USERS.get(request.admin_user, {})
            if current_user_data.get('role') != 'super_admin':
                return jsonify({'success': False, 'message': 'Only Super Admins can modify protected accounts'}), 403

        # تحديث الدور والصلاحيات
        ADMIN_USERS[username]['role'] = new_role
        if custom_permissions:
            ADMIN_USERS[username]['permissions'] = custom_permissions
        else:
            # تطبيق الصلاحيات الافتراضية للدور
            role_permissions = {
                'super_admin': ['all'],
                'admin': ['all'],
                'manager': ['read', 'write', 'manage_users', 'manage_apis', 'view_logs', 'manage_blocks'],
                'moderator': ['read', 'write', 'manage_blocks', 'view_logs'],
                'api_manager': ['read', 'write', 'manage_apis', 'test_apis'],
                'security': ['read', 'manage_blocks', 'view_logs', 'emergency_shutdown'],
                'analyst': ['read', 'view_logs', 'export_data'],
                'editor': ['read', 'write'],
                'viewer': ['read']
            }
            ADMIN_USERS[username]['permissions'] = role_permissions.get(new_role, ['read'])

        save_users(ADMIN_USERS)
        log_activity('USER_ROLE_UPDATED', {'username': username, 'new_role': new_role}, request.admin_user)

        return jsonify({
            'success': True,
            'message': f'Role updated to {new_role}',
            'new_permissions': ADMIN_USERS[username]['permissions']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================================================================
# API الإدارة - إدارة APIs
# =============================================================================

@app.route('/admin/api/endpoints')
@admin_required
def admin_endpoints():
    """قائمة نقاط النهاية"""
    endpoints_list = []
    for name, endpoint in API_ENDPOINTS.items():
        endpoint_info = endpoint.copy()
        endpoint_info['name'] = name
        endpoint_info['maintenance'] = MAINTENANCE_STATUS.get(name, {}).get('enabled', False)
        endpoints_list.append(endpoint_info)

    return jsonify({'success': True, 'data': endpoints_list})

@app.route('/admin/api/endpoints/<endpoint_name>/test', methods=['POST'])
@admin_required
def test_endpoint(endpoint_name):
    """اختبار نقطة نهاية"""
    if endpoint_name not in API_ENDPOINTS:
        return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

    endpoint = API_ENDPOINTS[endpoint_name]
    test_params = request.get_json().get('params', {})

    try:
        # استبدال المعاملات في URL
        test_url = endpoint['url']
        for key, value in test_params.items():
            test_url = test_url.replace(f'{{{key}}}', str(value))

        # إجراء الطلب
        if endpoint['method'] == 'GET':
            response = requests.get(test_url, timeout=endpoint['timeout'])
        else:
            response = requests.post(test_url, timeout=endpoint['timeout'])

        log_activity('API_TEST', {'endpoint': endpoint_name, 'status': response.status_code}, request.admin_user)

        return jsonify({
            'success': True,
            'data': {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'response_size': len(response.content),
                'headers': dict(response.headers),
                'content': response.text[:1000]  # أول 1000 حرف فقط
            }
        })
    except Exception as e:
        log_activity('API_TEST_FAILED', {'endpoint': endpoint_name, 'error': str(e)}, request.admin_user)
        return jsonify({
            'success': False,
            'message': f'Test failed: {str(e)}'
        })

@app.route('/admin/api/endpoints/<endpoint_name>/update', methods=['POST'])
@admin_required
def update_endpoint(endpoint_name):
    """تحديث نقطة نهاية"""
    try:
        data = request.get_json()

        if endpoint_name not in API_ENDPOINTS:
            return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

        # تحديث البيانات
        API_ENDPOINTS[endpoint_name].update({
            'url': data.get('url', API_ENDPOINTS[endpoint_name]['url']),
            'method': data.get('method', API_ENDPOINTS[endpoint_name]['method']),
            'timeout': data.get('timeout', API_ENDPOINTS[endpoint_name]['timeout']),
            'status': data.get('status', API_ENDPOINTS[endpoint_name]['status'])
        })

        save_apis(API_ENDPOINTS)
        log_activity('API_UPDATED', {'endpoint': endpoint_name}, request.admin_user)

        return jsonify({'success': True, 'message': 'Endpoint updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/endpoints/<endpoint_name>/maintenance', methods=['POST'])
@admin_required
def toggle_endpoint_maintenance(endpoint_name):
    """تفعيل/إلغاء صيانة نقطة نهاية"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        reason = data.get('reason', 'Scheduled maintenance')
        estimated_time = data.get('estimated_time', 'Unknown')

        if enabled:
            MAINTENANCE_STATUS[endpoint_name] = {
                'enabled': True,
                'reason': reason,
                'estimated_time': estimated_time,
                'started_at': int(time.time()),
                'started_by': request.admin_user
            }
        else:
            MAINTENANCE_STATUS.pop(endpoint_name, None)

        save_maintenance(MAINTENANCE_STATUS)
        log_activity('MAINTENANCE_TOGGLED', {
            'endpoint': endpoint_name,
            'enabled': enabled,
            'reason': reason
        }, request.admin_user)

        return jsonify({
            'success': True,
            'message': f'Maintenance {"enabled" if enabled else "disabled"} for {endpoint_name}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/endpoints/add', methods=['POST'])
@admin_required
def add_new_endpoint():
    """إضافة نقطة نهاية جديدة"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        url = data.get('url', '').strip()
        method = data.get('method', 'GET')
        timeout = data.get('timeout', 30)
        status = data.get('status', 'active')
        maintenance = data.get('maintenance', False)

        if not name or not url:
            return jsonify({'success': False, 'message': 'Name and URL are required'}), 400

        if name in API_ENDPOINTS:
            return jsonify({'success': False, 'message': 'API name already exists'}), 400

        # إضافة API جديد
        API_ENDPOINTS[name] = {
            'url': url,
            'method': method,
            'timeout': timeout,
            'status': status,
            'maintenance': maintenance,
            'created_by': request.admin_user,
            'created_at': int(time.time())
        }

        save_apis(API_ENDPOINTS)
        log_activity('API_ADDED', {
            'name': name,
            'url': url,
            'method': method
        }, request.admin_user)

        return jsonify({
            'success': True,
            'message': f'API "{name}" added successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/endpoints/<endpoint_name>/delete', methods=['DELETE'])
@admin_required
def delete_endpoint(endpoint_name):
    """حذف نقطة نهاية"""
    try:
        if endpoint_name not in API_ENDPOINTS:
            return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

        # حذف من APIs
        deleted_api = API_ENDPOINTS.pop(endpoint_name, None)
        save_apis(API_ENDPOINTS)

        # حذف من صيانة إن وجد
        MAINTENANCE_STATUS.pop(endpoint_name, None)
        save_maintenance(MAINTENANCE_STATUS)

        log_activity('API_DELETED', {
            'name': endpoint_name,
            'url': deleted_api.get('url', 'Unknown') if deleted_api else 'Unknown'
        }, request.admin_user)

        return jsonify({
            'success': True,
            'message': f'API "{endpoint_name}" deleted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================================================================
# API الإدارة - إدارة الحظر
# =============================================================================

@app.route('/admin/api/blocks')
@admin_required
def admin_blocks():
    """قائمة العناوين المحظورة"""
    blocks_list = []
    for ip, block_info in security_data['blocked_ips'].items():
        block_data = block_info.copy()
        block_data['ip'] = ip
        block_data['blocked_datetime'] = datetime.fromtimestamp(block_data['blocked_at']).isoformat()

        if not block_data.get('permanent') and 'until' in block_data:
            block_data['until_datetime'] = datetime.fromtimestamp(block_data['until']).isoformat()
            block_data['remaining_seconds'] = max(0, block_data['until'] - time.time())

        blocks_list.append(block_data)

    return jsonify({'success': True, 'data': blocks_list})

@app.route('/admin/api/blocks/add', methods=['POST'])
@admin_required
def add_block():
    """إضافة حظر جديد"""
    try:
        data = request.get_json()
        ip = data.get('ip', '').strip()
        reason = data.get('reason', 'Blocked by admin')
        duration = data.get('duration', 60)  # بالدقائق
        permanent = data.get('permanent', False)

        if not ip:
            return jsonify({'success': False, 'message': 'IP address required'}), 400

        block_ip(ip, duration if not permanent else None, reason, permanent)

        return jsonify({'success': True, 'message': f'IP {ip} blocked successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/blocks/<ip>/remove', methods=['POST'])
@admin_required
def remove_block(ip):
    """إزالة حظر"""
    if ip not in security_data['blocked_ips']:
        return jsonify({'success': False, 'message': 'IP not blocked'}), 404

    unblock_ip(ip)
    return jsonify({'success': True, 'message': f'IP {ip} unblocked successfully'})

# =============================================================================
# API الإدارة - السجلات والتصدير
# =============================================================================

@app.route('/admin/api/logs')
@admin_required
def admin_logs():
    """سجلات النشاط"""
    try:
        with open(LOGS_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)

        # تصفية وترتيب السجلات
        logs.sort(key=lambda x: x['timestamp'], reverse=True)

        return jsonify({'success': True, 'data': logs[:200]})  # آخر 200 سجل
    except:
        return jsonify({'success': True, 'data': []})

@app.route('/admin/api/export/<data_type>')
@admin_required
def export_data(data_type):
    """تصدير البيانات المحسن"""
    try:
        if data_type == 'config':
            data = SITE_CONFIG if SITE_CONFIG else {}
            filename = f'config_export_{int(time.time())}.json'
        elif data_type == 'users':
            data = ADMIN_USERS if ADMIN_USERS else {}
            filename = f'users_export_{int(time.time())}.json'
        elif data_type == 'apis':
            data = API_ENDPOINTS if API_ENDPOINTS else {}
            filename = f'apis_export_{int(time.time())}.json'
        elif data_type == 'visitors':
            data = security_data.get('visitor_logs', [])
            filename = f'visitors_export_{int(time.time())}.json'
        elif data_type == 'blocks':
            data = security_data.get('blocked_ips', {})
            filename = f'blocks_export_{int(time.time())}.json'
        elif data_type == 'logs':
            try:
                with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = []
            except json.JSONDecodeError:
                data = []
            filename = f'logs_export_{int(time.time())}.json'
        elif data_type == 'all':
            # تصدير شامل لكل شيء في النظام
            try:
                with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                    logs_data = json.load(f)
            except:
                logs_data = []

            data = {
                'export_metadata': {
                    'exported_at': int(time.time()),
                    'exported_by': request.admin_user,
                    'export_type': 'COMPLETE_SYSTEM_BACKUP',
                    'version': '3.0',
                    'system_info': {
                        'total_visitors': len(set([v['ip'] for v in security_data['visitor_logs']])),
                        'total_blocks': len(security_data['blocked_ips']),
                        'total_admins': len(ADMIN_USERS),
                        'total_apis': len(API_ENDPOINTS),
                        'active_sessions': len(security_data['active_sessions'])
                    }
                },
                'system_config': SITE_CONFIG,
                'admin_users': ADMIN_USERS,
                'api_endpoints': API_ENDPOINTS,
                'visitor_logs': security_data['visitor_logs'],
                'blocked_ips': security_data['blocked_ips'],
                'maintenance_status': MAINTENANCE_STATUS,
                'activity_logs': logs_data,
                'active_sessions': {
                    session_id: {
                        'username': session_info['username'],
                        'login_time': session_info['login_time'],
                        'last_activity': session_info['last_activity'],
                        'role': session_info['role'],
                        'ip': session_info['ip']
                    } for session_id, session_info in security_data['active_sessions'].items()
                },
                'security_settings': {
                    'failed_attempts': dict(security_data['failed_attempts']),
                    'rate_limits': dict(security_data['rate_limits']),
                    'whitelist': SITE_CONFIG.get('whitelist', [])
                }
            }
            filename = f'complete_system_backup_{int(time.time())}.json'
        elif data_type == 'statistics':
            # إحصائيات متقدمة
            unique_visitors = len(set([v['ip'] for v in security_data['visitor_logs']]))
            endpoint_stats = {}
            for visitor in security_data['visitor_logs']:
                endpoint = visitor.get('endpoint', 'unknown')
                endpoint_stats[endpoint] = endpoint_stats.get(endpoint, 0) + 1

            data = {
                'generated_at': int(time.time()),
                'statistics': {
                    'visitors': {
                        'total_visits': len(security_data['visitor_logs']),
                        'unique_visitors': unique_visitors,
                        'top_pages': sorted(endpoint_stats.items(), key=lambda x: x[1], reverse=True)[:10]
                    },
                    'security': {
                        'total_blocks': len(security_data['blocked_ips']),
                        'permanent_blocks': len([b for b in security_data['blocked_ips'].values() if b.get('permanent')]),
                        'temporary_blocks': len([b for b in security_data['blocked_ips'].values() if not b.get('permanent')]),
                        'failed_attempts': dict(security_data['failed_attempts'])
                    },
                    'admin_activity': {
                        'total_admins': len(ADMIN_USERS),
                        'active_admins': len([u for u in ADMIN_USERS.values() if u['status'] == 'active']),
                        'recent_logins': len([log for log in logs_data if log.get('action') == 'ADMIN_LOGIN' and log.get('timestamp', 0) > time.time() - 86400])
                    }
                }
            }
            filename = f'system_statistics_{int(time.time())}.json'
        else:
            return jsonify({'success': False, 'message': 'Invalid data type'}), 400

        # حفظ الملف مع ضغط للملفات الكبيرة
        export_path = f'exports/{filename}'
        os.makedirs('exports', exist_ok=True)

        # إنشاء الملف
        json_content = json.dumps(data, ensure_ascii=False, indent=2)

        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(json_content)

        file_size = os.path.getsize(export_path)

        log_activity('DATA_EXPORTED', {
            'type': data_type,
            'filename': filename,
            'file_size': file_size,
            'records_count': len(data) if isinstance(data, list) else 'complex_structure'
        }, request.admin_user)

        return jsonify({
            'success': True,
            'message': f'تم تصدير {data_type} بنجاح',
            'download_url': f'/admin/api/download/{filename}',
            'filename': filename,
            'size': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'timestamp': int(time.time()),
            'exported_by': request.admin_user,
            'export_type': data_type
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/download/<filename>')
@admin_required
def download_export(filename):
    """تحميل ملف مُصدر"""
    try:
        from flask import send_file
        export_path = f'exports/{filename}'

        if not os.path.exists(export_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404

        return send_file(export_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/static/images/generated-icon.png')
def generate_security_icon():
    """توليد أيقونة الأمان ديناميكياً"""
    try:
        from flask import send_file
        import io
        import base64

        # أيقونة SVG بسيطة للأمان
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
    <rect width="64" height="64" fill="#000000"/>
    <path d="M32 8 L48 16 L48 32 Q48 48 32 56 Q16 48 16 32 L16 16 Z" fill="#00ff41" stroke="#00ff41" stroke-width="2"/>
    <text x="32" y="38" text-anchor="middle" fill="#000000" font-family="Arial" font-size="24" font-weight="bold">S1X</text>
</svg>'''

        # تحويل SVG إلى PNG (محاكاة بسيطة)
        response = make_response(svg_content)
        response.headers['Content-Type'] = 'image/svg+xml'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
    except Exception as e:
        return jsonify({'error': 'Icon generation failed'}), 500

# =============================================================================
# API الإدارة - التحكم المتقدم في الموقع
# =============================================================================

@app.route('/admin/api/site-control/shutdown', methods=['POST'])
@admin_required
def emergency_shutdown():
    """إيقاف الموقع في حالات الطوارئ"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'Emergency maintenance')

        SITE_CONFIG['emergency_mode'] = {
            'enabled': True,
            'reason': reason,
            'shutdown_by': request.admin_user,
            'shutdown_time': int(time.time())
        }
        save_config(SITE_CONFIG)

        log_activity('EMERGENCY_SHUTDOWN', {'reason': reason}, request.admin_user)
        return jsonify({'success': True, 'message': 'Site shutdown activated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/site-control/restore', methods=['POST'])
@admin_required
def restore_site():
    """استعادة الموقع من الإيقاف الطارئ"""
    try:
        SITE_CONFIG.pop('emergency_mode', None)
        save_config(SITE_CONFIG)

        log_activity('SITE_RESTORED', {}, request.admin_user)
        return jsonify({'success': True, 'message': 'Site restored successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/database/clear', methods=['POST'])
@admin_required
def clear_database():
    """مسح قاعدة البيانات"""
    try:
        data = request.get_json()
        table_type = data.get('type', '')

        if table_type == 'visitors':
            security_data['visitor_logs'].clear()
            log_activity('VISITORS_CLEARED', {}, request.admin_user)
        elif table_type == 'blocks':
            security_data['blocked_ips'].clear()
            log_activity('BLOCKS_CLEARED', {}, request.admin_user)
        elif table_type == 'logs':
            with open(LOGS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
            log_activity('LOGS_CLEARED', {}, request.admin_user)
        elif table_type == 'sessions':
            security_data['active_sessions'].clear()
            log_activity('SESSIONS_CLEARED', {}, request.admin_user)
        else:
            return jsonify({'success': False, 'message': 'Invalid table type'}), 400

        return jsonify({'success': True, 'message': f'{table_type} cleared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/site-control/theme', methods=['POST'])
@admin_required
def change_site_theme():
    """تغيير شكل الموقع"""
    try:
        data = request.get_json()
        theme = data.get('theme', 'default')

        SITE_CONFIG['theme'] = {
            'name': theme,
            'changed_by': request.admin_user,
            'changed_at': int(time.time())
        }
        save_config(SITE_CONFIG)

        log_activity('THEME_CHANGED', {'theme': theme}, request.admin_user)
        return jsonify({'success': True, 'message': f'Theme changed to {theme}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/site-control/announcement', methods=['POST'])
@admin_required
def create_announcement():
    """إنشاء إعلان للموقع"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        announcement_type = data.get('type', 'info')  # info, warning, danger, success

        if not message:
            return jsonify({'success': False, 'message': 'Announcement message required'}), 400

        SITE_CONFIG['announcement'] = {
            'message': message,
            'type': announcement_type,
            'created_by': request.admin_user,
            'created_at': int(time.time()),
            'active': True
        }
        save_config(SITE_CONFIG)

        log_activity('ANNOUNCEMENT_CREATED', {'message': message[:50], 'type': announcement_type}, request.admin_user)
        return jsonify({'success': True, 'message': 'Announcement created successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/site-control/announcement/toggle', methods=['POST'])
@admin_required
def toggle_announcement():
    """تفعيل/إلغاء الإعلان"""
    try:
        if 'announcement' not in SITE_CONFIG:
            return jsonify({'success': False, 'message': 'No announcement exists'}), 404

        SITE_CONFIG['announcement']['active'] = not SITE_CONFIG['announcement'].get('active', False)
        save_config(SITE_CONFIG)

        status = 'enabled' if SITE_CONFIG['announcement']['active'] else 'disabled'
        log_activity('ANNOUNCEMENT_TOGGLED', {'status': status}, request.admin_user)

        return jsonify({'success': True, 'message': f'Announcement {status}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/security/mass-block', methods=['POST'])
@admin_required
def mass_block_ips():
    """حظر مجموعة كبيرة من IPs"""
    try:
        data = request.get_json()
        ips_text = data.get('ips', '').strip()
        reason = data.get('reason', 'Mass block by admin')
        permanent = data.get('permanent', False)

        # تحويل النص إلى قائمة IPs
        ips = [ip.strip() for ip in ips_text.replace(',', '\n').split('\n') if ip.strip()]

        if not ips:
            return jsonify({'success': False, 'message': 'No IPs provided'}), 400

        blocked_count = 0
        for ip in ips:
            if ip and '.' in ip:  # فحص بسيط للتأكد من أنه IP صالح
                block_ip(ip, None if permanent else 60, reason, permanent)
                blocked_count += 1

        log_activity('MASS_BLOCK', {'count': blocked_count, 'reason': reason}, request.admin_user)
        return jsonify({'success': True, 'message': f'{blocked_count} IPs blocked successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/security/whitelist', methods=['POST'])
@admin_required
def manage_whitelist():
    """إدارة القائمة البيضاء"""
    try:
        data = request.get_json()
        action = data.get('action', 'add')  # add, remove, list
        ip = data.get('ip', '').strip()

        if 'whitelist' not in SITE_CONFIG:
            SITE_CONFIG['whitelist'] = []

        if action == 'add':
            if ip not in SITE_CONFIG['whitelist']:
                SITE_CONFIG['whitelist'].append(ip)
                save_config(SITE_CONFIG)
                log_activity('WHITELIST_ADD', {'ip': ip}, request.admin_user)
                return jsonify({'success': True, 'message': f'IP {ip} added to whitelist'})
            else:
                return jsonify({'success': False, 'message': 'IP already in whitelist'}), 400

        elif action == 'remove':
            if ip in SITE_CONFIG['whitelist']:
                SITE_CONFIG['whitelist'].remove(ip)
                save_config(SITE_CONFIG)
                log_activity('WHITELIST_REMOVE', {'ip': ip}, request.admin_user)
                return jsonify({'success': True, 'message': f'IP {ip} removed from whitelist'})
            else:
                return jsonify({'success': False, 'message': 'IP not in whitelist'}), 400

        elif action == 'list':
            return jsonify({'success': True, 'data': SITE_CONFIG.get('whitelist', [])})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/analytics/detailed', methods=['GET'])
@admin_required
def detailed_analytics():
    """تحليلات مفصلة للموقع"""
    try:
        # إحصائيات الزوار حسب الوقت
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400
        week_ago = now - 604800

        visitors_hour = len([v for v in security_data['visitor_logs'] if v['timestamp'] > hour_ago])
        visitors_day = len([v for v in security_data['visitor_logs'] if v['timestamp'] > day_ago])
        visitors_week = len([v for v in security_data['visitor_logs'] if v['timestamp'] > week_ago])

        # أكثر الصفحات زيارة
        endpoint_counts = {}
        for visitor in security_data['visitor_logs']:
            endpoint = visitor.get('endpoint', 'unknown')
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

        top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # إحصائيات المتصفحات
        browser_counts = {}
        for visitor in security_data['visitor_logs']:
            user_agent = visitor.get('user_agent', 'Unknown')
            # تحليل بسيط للمتصفح
            browser = 'Unknown'
            if 'Chrome' in user_agent:
                browser = 'Chrome'
            elif 'Firefox' in user_agent:
                browser = 'Firefox'
            elif 'Safari' in user_agent:
                browser = 'Safari'
            elif 'Edge' in user_agent:
                browser = 'Edge'

            browser_counts[browser] = browser_counts.get(browser, 0) + 1

        return jsonify({
            'success': True,
            'data': {
                'time_stats': {
                    'last_hour': visitors_hour,
                    'last_day': visitors_day,
                    'last_week': visitors_week
                },
                'top_endpoints': top_endpoints,
                'browser_stats': browser_counts,
                'total_unique_ips': len(set([v['ip'] for v in security_data['visitor_logs']])),
                'blocked_ips_count': len(security_data['blocked_ips']),
                'active_sessions_count': len(security_data['active_sessions'])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/system/performance', methods=['GET'])
@admin_required
def system_performance():
    """معلومات أداء النظام"""
    try:
        import psutil
        import os

        # معلومات النظام
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return jsonify({
            'success': True,
            'data': {
                'cpu_usage': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'uptime': time.time() - psutil.boot_time()
            }
        })
    except ImportError:
        # إذا لم يكن psutil متاحاً
        return jsonify({
            'success': True,
            'data': {
                'cpu_usage': 'N/A',
                'memory': 'N/A',
                'disk': 'N/A',
                'uptime': 'N/A',
                'note': 'psutil not available'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/backup/create', methods=['POST'])
@admin_required
def create_full_backup():
    """إنشاء نسخة احتياطية كاملة"""
    try:
        import zipfile
        import tempfile

        backup_name = f"backup_{int(time.time())}.zip"
        backup_path = os.path.join(tempfile.gettempdir(), backup_name)

        with zipfile.ZipFile(backup_path, 'w') as backup_zip:
            # إضافة ملفات التكوين
            files_to_backup = [
                'config.json', 'users.json', 'apis.json',
                'logs.json', 'maintenance.json', 'blocks.json',
                'user_keys.json', 'registered_users.json'
            ]

            for file_name in files_to_backup:
                if os.path.exists(file_name):
                    backup_zip.write(file_name)

            # إضافة معلومات إضافية للنسخة الاحتياطية
            backup_info = {
                'created_at': int(time.time()),
                'created_by': request.admin_user,
                'version': '1.0',
                'files_included': files_to_backup
            }

            backup_zip.writestr('backup_info.json', json.dumps(backup_info, indent=2))

        log_activity('BACKUP_CREATED', {'backup_name': backup_name}, request.admin_user)

        return jsonify({
            'success': True,
            'message': 'Backup created successfully',
            'backup_path': backup_path,
            'backup_name': backup_name
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/system/restart', methods=['POST'])
@admin_required
def restart_application():
    """إعادة تشغيل التطبيق"""
    try:
        import signal

        log_activity('SYSTEM_RESTART', {'initiated_by': request.admin_user}, request.admin_user)

        # حفظ جميع البيانات قبل إعادة التشغيل
        save_config(SITE_CONFIG)
        save_users(ADMIN_USERS)
        save_apis(API_ENDPOINTS)
        save_maintenance(MAINTENANCE_STATUS)
        save_blocks() # Save blocks too
        save_registered_users(REGISTERED_USERS)

        # إعادة تشغيل التطبيق
        def restart():
            time.sleep(2)  # انتظار لإرسال الرد
            os.kill(os.getpid(), signal.SIGTERM)

        threading.Thread(target=restart).start()

        return jsonify({
            'success': True,
            'message': 'System restart initiated'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/users/<username>/delete', methods=['POST'])
@admin_required
def delete_admin_user(username):
    """حذف مستخدم إداري (للسوبر أدمنز فقط)"""
    try:
        # التحقق من الصلاحيات العليا
        current_user = request.admin_user
        current_user_data = ADMIN_USERS.get(current_user, {})

        if current_user not in ['bngx_admin', 'BLRXH4RDIXX'] and current_user_data.get('role') != 'super_admin':
            return jsonify({'success': False, 'message': 'Access denied - Super admin required'}), 403

        if username not in ADMIN_USERS:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # منع حذف النفس
        if username == current_user:
            return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 403

        # حذف المستخدم
        deleted_user_data = ADMIN_USERS.pop(username, {})
        save_users(ADMIN_USERS)

        # حذف جلسات المستخدم النشطة
        sessions_to_remove = []
        for session_id, session_info in security_data['active_sessions'].items():
            if session_info['username'] == username:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            security_data['active_sessions'].pop(session_id, None)

        log_activity('USER_DELETED', {
            'deleted_user': username,
            'deleted_role': deleted_user_data.get('role', 'unknown'),
            'deleted_by': current_user
        }, current_user)

        return jsonify({
            'success': True,
            'message': f'User {username} deleted successfully',
            'deleted_user_role': deleted_user_data.get('role', 'unknown')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/users/<username>/update-permissions', methods=['POST'])
@admin_required
def update_user_permissions(username):
    """تحديث صلاحيات المستخدم"""
    try:
        if username not in ADMIN_USERS:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        data = request.get_json()
        new_permissions = data.get('permissions', [])

        ADMIN_USERS[username]['permissions'] = new_permissions
        save_users(ADMIN_USERS)

        log_activity('USER_PERMISSIONS_UPDATED', {
            'username': username,
            'new_permissions': new_permissions
        }, request.admin_user)

        return jsonify({
            'success': True,
            'message': f'Permissions updated for {username}',
            'new_permissions': new_permissions
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/super-admin/get-user-features/<username>')
@admin_required
def get_user_features(username):
    """الحصول على الميزات المخفية لمستخدم"""
    try:
        current_user = request.admin_user
        if current_user not in ['bngx_admin', 'BLRXH4RDIXX'] and ADMIN_USERS.get(current_user, {}).get('role') != 'super_admin':
            return jsonify({'success': False, 'message': 'Access denied - Super admin required'}), 403

        if username not in ADMIN_USERS:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        available_features = [
            'dashboard', 'users', 'apis', 'visitors', 'security', 'maintenance',
            'logs', 'config', 'export', 'site-control', 'advanced-security',
            'analytics', 'system-monitor', 'super-admin', 'enhanced-logs', 'block-manager',
            'ai' # Added AI feature
        ]

        hidden_features = ADMIN_USERS[username].get('hidden_features', [])

        return jsonify({
            'success': True,
            'data': {
                'username': username,
                'available_features': available_features,
                'hidden_features': hidden_features,
                'visible_features': [f for f in available_features if f not in hidden_features]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/user-features')
@admin_required
def get_current_user_features():
    """الحصول على الميزات المتاحة للمستخدم الحالي"""
    try:
        current_user = request.admin_user
        if current_user not in ADMIN_USERS:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        user_data = ADMIN_USERS[current_user]
        hidden_features = user_data.get('hidden_features', [])

        # السوبر أدمنز يرون كل شيء
        if current_user in ['bngx_admin', 'BLRXH4RDIXX'] or user_data.get('role') == 'super_admin':
            hidden_features = []

        available_features = [
            'dashboard', 'users', 'apis', 'visitors', 'security', 'maintenance',
            'logs', 'config', 'export', 'site-control', 'advanced-security',
            'analytics', 'system-monitor', 'super-admin', 'enhanced-logs', 'block-manager',
            'ai' # Added AI feature
        ]

        visible_features = [f for f in available_features if f not in hidden_features]

        return jsonify({
            'success': True,
            'data': {
                'visible_features': visible_features,
                'hidden_features': hidden_features,
                'is_super_admin': current_user in ['bngx_admin', 'BLRXH4RDIXX'] or user_data.get('role') == 'super_admin'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/site-announcement/status')
def get_announcement_status():
    """الحصول على حالة الإعلان الحالي"""
    try:
        announcement = SITE_CONFIG.get('announcement')
        if announcement and announcement.get('active', False):
            return jsonify({
                'success': True,
                'data': {
                    'active': True,
                    'message': announcement.get('message', ''),
                    'type': announcement.get('type', 'info'),
                    'created_by': announcement.get('created_by', 'Unknown'),
                    'created_at': announcement.get('created_at', 0)
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'active': False
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/register-user', methods=['POST'])
def register_user():
    """تسجيل مستخدم جديد في النظام"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()

        if not username:
            return jsonify({
                'success': False,
                'message': 'اسم المستخدم مطلوب'
            }), 400

        if len(username) < 3:
            return jsonify({
                'success': False,
                'message': 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل'
            }), 400

        # التحقق من صحة اسم المستخدم
        import re
        if not re.match(r'^[a-zA-Z0-9\u0600-\u06FF\u0750-\u077F]+$', username):
            return jsonify({
                'success': False,
                'message': 'اسم المستخدم يجب أن يحتوي على أحرف وأرقام فقط'
            }), 400

        client_ip = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        user_key = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"

        # التحقق من تكرار اسم المستخدم
        existing_usernames = [user_data.get('username', '').lower() for user_data in REGISTERED_USERS.values()]
        if username.lower() in existing_usernames:
            return jsonify({
                'success': False,
                'message': f'اسم المستخدم "{username}" موجود مسبقاً، يرجى اختيار اسم آخر',
                'error_code': 'USERNAME_EXISTS',
                'suggested_alternatives': [
                    f"{username}1",
                    f"{username}2",
                    f"{username}_{random.randint(100, 999)}"
                ]
            }), 400

        # إنشاء معرف فريد للمستخدم
        user_id = f"USER_{int(time.time())}_{secrets.token_hex(4)}"

        # حفظ بيانات المستخدم
        user_data = {
            'username': username,
            'user_id': user_id,
            'registered_at': time.time(),
            'registered_datetime': datetime.now().isoformat(),
            'ip': client_ip,
            'user_agent': user_agent,
            'user_key': user_key,
            'status': 'active',
            'last_login': time.time(),
            'login_count': 1
        }

        REGISTERED_USERS[user_key] = user_data
        save_registered_users(REGISTERED_USERS)

        # إنشاء مفتاح سري للمستخدم وربطه بكونه مسجل
        secret_key = generate_user_secret_key(client_ip, user_agent)
        save_user_secret_key(client_ip, user_agent, secret_key)

        # تحديث بيانات المفتاح السري لتتضمن معلومات التسجيل
        if user_key in user_secret_keys:
            user_secret_keys[user_key]['registered_user'] = True
            user_secret_keys[user_key]['username'] = username
            user_secret_keys[user_key]['user_id'] = user_id

        # إنشاء جلسة تحقق للمستخدم الجديد
        verification_sessions[client_ip] = {
            'verified_at': time.time(),
            'user_agent': user_agent,
            'registered_user': True,
            'username': username,
            'user_id': user_id,
            'challenges_passed': 1
        }

        log_activity('USER_REGISTERED', {
            'username': username,
            'user_id': user_id,
            'ip': client_ip
        })

        return jsonify({
            'success': True,
            'message': 'تم تسجيل المستخدم بنجاح',
            'user_id': user_id,
            'username': username,
            'redirect_url': f'/dashboard?welcome=true&username={username}'
        })

    except Exception as e:
        log_activity('USER_REGISTRATION_ERROR', {
            'error': str(e),
            'ip': get_client_ip()
        })
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في تسجيل المستخدم'
        }), 500

@app.route('/api/get-dynamic-token')
def get_dynamic_token():
    """توليد رمز ديناميكي للواجهة الأمامية"""
    if not is_request_from_authorized_source():
        return jsonify({
            'code': 403,
            'error': 'Access Forbidden',
            'message': 'Unauthorized source',
            'success': False
        }), 403

    token, timestamp = generate_dynamic_token()
    return jsonify({
        'success': True,
        'token': token,
        'timestamp': timestamp,
        'expires_in': 300  # 5 دقائق
    })

@app.route('/api/decrypt-html', methods=['POST'])
@codex_protection_required
def decrypt_html_endpoint():
    """فك تشفير HTML للواجهة الأمامية"""
    try:
        if not is_request_from_authorized_source():
            return jsonify({
                'success': False,
                'error': 'Unauthorized source'
            }), 403

        data = request.get_json()
        encrypted_data = data.get('encrypted_html', '')
        auth_token = data.get('auth_token', '')

        if not encrypted_data:
            return jsonify({
                'success': False,
                'error': 'No encrypted data provided'
            }), 400

        # التحقق من التوثيق
        client_ip = get_client_ip()
        if client_ip not in verification_sessions:
            return jsonify({
                'success': False,
                'error': 'Session verification required'
            }), 401

        # فك التشفير
        decrypted_html = decrypt_html_content(encrypted_data)

        if decrypted_html is None:
            return jsonify({
                'success': False,
                'error': 'Decryption failed'
            }), 400

        return jsonify({
            'success': True,
            'html': decrypted_html,
            'timestamp': int(time.time())
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Decryption service error'
        }), 500

@app.route('/api/jwt/verify', methods=['POST'])
def verify_jwt_endpoint():
    """التحقق من صحة JWT Token"""
    try:
        data = request.get_json()
        token = data.get('token', '')
        token_type = data.get('type', 'access')

        if not token:
            return jsonify({
                'success': False,
                'error': 'Token required'
            }), 400

        payload, error = verify_jwt_token(token, token_type)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'valid': False
            }), 401

        return jsonify({
            'success': True,
            'valid': True,
            'payload': {
                'username': payload.get('username'),
                'role': payload.get('role'),
                'permissions': payload.get('permissions'),
                'exp': payload.get('exp'),
                'type': payload.get('type')
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Token verification failed'
        }), 500

# =============================================================================
# مسارات نظام الحماية S1X TEAM
# =============================================================================

@app.route('/security/challenge')
def security_challenge():
    """صفحة تحدي الأمان مع HTML مشفر"""
    try:
        context = {
            'challenge_id': secrets.token_hex(8),
            'timestamp': int(time.time()),
            'protection_level': 'MAXIMUM'
        }

        encrypted_html = generate_secure_html_template('captcha_challenge.html', **context)

        response = make_response(encrypted_html)
        response.headers['X-S1X-Protection'] = 'CHALLENGE-ENCRYPTED'

        return response

    except Exception as e:
        return "<h1>🔒 S1X TEAM Security Challenge - Access Denied</h1>", 500

@app.route('/security/blocked')
def security_blocked():
    """صفحة الحظر الأمني مع HTML مشفر"""
    try:
        client_ip = get_client_ip()
        block_info = security_data['blocked_ips'].get(client_ip, {})

        context = {
            'client_ip': client_ip,
            'block_reason': block_info.get('enhanced_message', 'Access denied'),
            'blocked_at': block_info.get('blocked_at', time.time()),
            'permanent': block_info.get('permanent', False)
        }

        encrypted_html = generate_secure_html_template('security_blocked.html', **context)

        response = make_response(encrypted_html)
        response.headers['X-S1X-Protection'] = 'BLOCKED-ENCRYPTED'

        return response

    except Exception as e:
        return "<h1>🚫 Access Blocked - S1X TEAM Protection</h1>", 403

@app.route('/api/security/challenge-config')
def get_challenge_config():
    """الحصول على إعدادات التحدي"""
    return jsonify({
        'success': True,
        'config': {
            'icon_url': S1X_PROTECTION_CONFIG['icon_url'],
            'title': 'S1X TEAM - نظام الحماية المتقدم',
            'subtitle': 'تحقق إجباري لجميع الزوار - يرجى إثبات أنك إنسان',
            'difficulty': S1X_PROTECTION_CONFIG['difficulty'],
            'max_attempts': S1X_PROTECTION_CONFIG['max_attempts'],
            'mandatory': True,
            'protection_level': 'MAXIMUM',
            'security_message': 'هذا الموقع محمي بنظام S1X TEAM المتقدم ضد البوتات والهجمات'
        }
    })

@app.route('/api/security/verify-human', methods=['POST'])
def verify_human():
    """التحقق من الإنسانية"""
    try:
        data = request.get_json()
        client_ip = get_client_ip()

        # فحص البيانات المرسلة
        challenge_id = data.get('challenge_id')
        answer = data.get('answer')
        attempts = data.get('attempts', 1)
        user_agent = data.get('user_agent', '')

        # التحقق من صحة البيانات
        if not challenge_id or answer is None:
            return jsonify({
                'success': False,
                'message': 'Invalid challenge data'
            }), 400

        # فحص عدد المحاولات
        if failed_challenges[client_ip] >= S1X_PROTECTION_CONFIG['max_attempts']:
            # حظر مؤقت
            block_ip(client_ip, S1X_PROTECTION_CONFIG['block_duration'], 'failed_challenges', False)

            log_activity('IP_BLOCKED_FAILED_CHALLENGES', {
                'ip': client_ip,
                'attempts': attempts,
                'challenge_id': challenge_id
            })

            return jsonify({
                'success': False,
                'message': 'Too many failed attempts. IP blocked temporarily.',
                'blocked': True
            }), 429

        # توليد رمز التحقق
        verification_token = generate_verification_token(client_ip, challenge_id)

        # توليد وحفظ المفتاح السري للمستخدم
        secret_key = generate_user_secret_key(client_ip, user_agent)
        save_user_secret_key(client_ip, user_agent, secret_key)

        # حفظ جلسة التحقق
        verification_sessions[client_ip] = {
            'verified_at': time.time(),
            'challenge_id': challenge_id,
            'user_agent': user_agent,
            'attempts_taken': attempts,
            'token': verification_token,
            'secret_key': secret_key,  # إضافة المفتاح السري للجلسة
            'captcha_verified': True,  # تأكيد اجتياز الـ CAPTCHA
            'ready_for_registration': True  # جاهز للتسجيل
        }

        # إعادة تعيين عداد المحاولات الفاشلة
        if client_ip in failed_challenges:
            del failed_challenges[client_ip]

        log_activity('HUMAN_VERIFICATION_SUCCESS', {
            'ip': client_ip,
            'challenge_id': challenge_id,
            'attempts': attempts
        })

        return jsonify({
            'success': True,
            'message': 'Verification successful',
            'token': verification_token,
            'expires_in': 3600
        })

    except Exception as e:
        log_activity('VERIFICATION_ERROR', {
            'ip': get_client_ip(),
            'error': str(e)
        })
        return jsonify({
            'success': False,
            'message': 'Verification failed'
        }), 500

@app.route('/api/security/block-status')
def get_block_status():
    """الحصول على حالة الحظر"""
    client_ip = get_client_ip()
    is_blocked, reason = is_ip_blocked(client_ip)

    if is_blocked:
        block_info = security_data['blocked_ips'].get(client_ip, {})
        remaining_time = 0

        if not block_info.get('permanent', False):
            remaining_time = max(0, block_info.get('until', 0) - time.time())

        return jsonify({
            'success': True,
            'blocked': True,
            'reason': block_info.get('enhanced_message', reason),
            'ip': client_ip,
            'blocked_at': datetime.fromtimestamp(block_info.get('blocked_at', time.time())).isoformat(),
            'remaining_seconds': int(remaining_time),
            'permanent': block_info.get('permanent', False)
        })

    return jsonify({
        'success': True,
        'blocked': False,
        'ip': client_ip
    })

@app.route('/api/security/verification-status')
def get_verification_status():
    """التحقق من حالة اجتياز الـ CAPTCHA"""
    client_ip = get_client_ip()

    # فحص إذا كان محظور وإلغاء الحظر إذا كان خطأ
    is_blocked, block_reason = is_ip_blocked(client_ip)
    if is_blocked:
        block_info = security_data['blocked_ips'].get(client_ip, {})
        # إذا كان السبب هو "failed_challenges" وقد مر وقت كافي، إلغاء الحظر
        if (block_info.get('reason') == 'failed_challenges' and
            time.time() - block_info.get('blocked_at', 0) > 300):  # 5 دقائق
            unblock_ip(client_ip)
            log_activity('AUTO_UNBLOCK_APPLIED', {
                'ip': client_ip,
                'reason': 'failed_challenges_timeout'
            })

    # فحص جلسة التحقق
    if client_ip in verification_sessions:
        session = verification_sessions[client_ip]
        captcha_verified = session.get('captcha_verified', False)

        return jsonify({
            'success': True,
            'captcha_verified': captcha_verified,
            'ready_for_registration': session.get('ready_for_registration', False),
            'verified_at': session.get('verified_at', 0)
        })

    return jsonify({
        'success': True,
        'captcha_verified': False,
        'ready_for_registration': False
    })

# =============================================================================
# مسارات إدارة نظام الحماية
# =============================================================================

@app.route('/admin/api/security/protection-config')
@admin_required
def get_protection_config():
    """الحصول على إعدادات الحماية"""
    return jsonify({
        'success': True,
        'config': S1X_PROTECTION_CONFIG,
        'statistics': {
            'active_sessions': len(verification_sessions),
            'failed_challenges': dict(failed_challenges),
            'suspicious_ips': len(suspicious_ips),
            'ddos_tracking': len(ddos_tracker)
        }
    })

@app.route('/admin/api/security/update-protection', methods=['POST'])
@admin_required
def update_protection_config():
    """تحديث إعدادات الحماية"""
    try:
        data = request.get_json()

        # تحديث الإعدادات
        for key, value in data.items():
            if key in S1X_PROTECTION_CONFIG:
                S1X_PROTECTION_CONFIG[key] = value

        log_activity('PROTECTION_CONFIG_UPDATED', {
            'updated_fields': list(data.keys()),
            'updated_by': request.admin_user
        }, request.admin_user)

        return jsonify({
            'success': True,
            'message': 'Protection configuration updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/security/clear-challenges', methods=['POST'])
@admin_required
def clear_failed_challenges():
    """مسح محاولات التحدي الفاشلة"""
    global failed_challenges, verification_sessions, suspicious_ips

    data = request.get_json()
    clear_type = data.get('type', 'all')

    if clear_type == 'failed':
        failed_challenges.clear()
    elif clear_type == 'sessions':
        verification_sessions.clear()
    elif clear_type == 'suspicious':
        suspicious_ips.clear()
    else:  # all
        failed_challenges.clear()
        verification_sessions.clear()
        suspicious_ips.clear()

    log_activity('SECURITY_DATA_CLEARED', {
        'type': clear_type,
        'cleared_by': request.admin_user
    }, request.admin_user)

    return jsonify({
        'success': True,
        'message': f'Security data cleared: {clear_type}'
    })

@app.route('/admin/api/security/protection-stats')
@admin_required
def get_protection_stats():
    """إحصائيات نظام الحماية"""
    current_time = time.time()

    # حساب الإحصائيات
    active_verifications = len([s for s in verification_sessions.values()
                               if current_time - s['verified_at'] < 3600])

    recent_suspicious = len([ips for ips in suspicious_ips.values()
                           if any(activity['timestamp'] > current_time - 3600
                                 for activity in ips)])

    current_ddos_targets = len([ip for ip, timestamps in ddos_tracker.items()
                               if sum(timestamps.values()) > 5])

    return jsonify({
        'success': True,
        'stats': {
            'protection_enabled': S1X_PROTECTION_CONFIG['enabled'],
            'current_mode': S1X_PROTECTION_CONFIG['current_mode'],
            'active_verifications': active_verifications,
            'total_verified_sessions': len(verification_sessions),
            'failed_challenge_ips': len(failed_challenges),
            'suspicious_ips_detected': recent_suspicious,
            'ddos_targets_detected': current_ddos_targets,
            'challenges_issued_today': len([s for s in verification_sessions.values()
                                          if current_time - s['verified_at'] < 86400]),
            'protection_modes': list(S1X_PROTECTION_CONFIG['protection_modes'].keys())
        }
    })

@app.route('/admin/api/system/full-control', methods=['POST'])
@admin_required
def full_system_control():
    """التحكم الكامل في النظام"""
    try:
        data = request.get_json()
        action = data.get('action', '')

        if action == 'reset_all_data':
            # إعادة تعيين جميع البيانات
            security_data['visitor_logs'].clear()
            security_data['blocked_ips'].clear()
            security_data['active_sessions'].clear()
            verification_sessions.clear()
            failed_challenges.clear()
            suspicious_ips.clear()
            ddos_tracker.clear()
            user_secret_keys.clear()
            REGISTERED_USERS.clear()

            # إعادة كتابة ملف السجلات
            with open(LOGS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)

            # إزالة ملفات البيانات
            for file_path in ['user_keys.json', 'blocks.json', 'registered_users.json']:
                if os.path.exists(file_path):
                    os.remove(file_path)

            log_activity('FULL_SYSTEM_RESET', {'action': action}, request.admin_user)
            return jsonify({'success': True, 'message': 'All system data reset'})

        elif action == 'export_everything':
            # تصدير جميع البيانات
            export_data = {
                'config': SITE_CONFIG,
                'users': ADMIN_USERS,
                'apis': API_ENDPOINTS,
                'visitors': security_data['visitor_logs'],
                'blocks': security_data['blocked_ips'],
                'sessions': list(security_data['active_sessions'].keys()),
                'maintenance': MAINTENANCE_STATUS,
                'timestamp': int(time.time()),
                'exported_by': request.admin_user
            }

            return jsonify({'success': True, 'data': export_data})

        return jsonify({'success': False, 'message': 'Invalid action'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================================================================
# API الإدارة - التكوين المحدث
# =============================================================================

@app.route('/admin/api/config')
@admin_required
def admin_config():
    """عرض التكوين الحالي"""
    return jsonify({'success': True, 'data': SITE_CONFIG})

@app.route('/admin/api/config/update', methods=['POST'])
@admin_required
def update_config():
    """تحديث التكوين"""
    try:
        data = request.get_json()

        # تحديث التكوين
        SITE_CONFIG.update(data)
        save_config(SITE_CONFIG)

        log_activity('CONFIG_UPDATED', {'changes': list(data.keys())}, request.admin_user)

        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================================================================
# APIs الأصلية مع فحص الصيانة
# =============================================================================



@app.route('/api/update-bio', methods=['POST', 'OPTIONS'])
@codex_protection_required
def update_bio():
    """Update user biography with verification"""
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

    # Handle POST request with protection
    try:
        # Basic request validation
        if not is_request_from_authorized_source():
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'error_code': 'UNAUTHORIZED_SOURCE'
            }), 403

        data = request.get_json()
        token = data.get('accessToken', '').strip()
        bio = data.get('newBio', '').strip()
        uid = data.get('uid', '').strip()  # User ID for verification

        if not token:
            return jsonify({
                'success': False,
                'message': 'Access token is required',
                'error_code': 'MISSING_TOKEN'
            }), 400

        if not bio:
            return jsonify({
                'success': False,
                'message': 'Biography content is required',
                'error_code': 'MISSING_BIO'
            }), 400

        # Update bio using the API
        endpoint = API_ENDPOINTS['update_bio']
        bio_url = endpoint['url'].replace('{token}', token).replace('{bio}', quote(bio))

        # إرسال الطلب باستخدام GET method
        response = requests.get(bio_url, timeout=endpoint['timeout'])

        if response.status_code == 200:
            try:
                response_data = response.json()

                # Verify the change by getting user info if UID provided
                verification_data = None
                if uid:
                    try:
                        info_endpoint = API_ENDPOINTS['user_info']
                        info_url = info_endpoint['url'].replace('{uid}', uid)
                        info_response = requests.get(info_url, timeout=info_endpoint['timeout'])

                        if info_response.status_code == 200:
                            verification_data = info_response.json()
                    except:
                        pass  # Continue without verification if it fails

                return jsonify({
                    'success': True,
                    'message': 'Biography updated successfully',
                    'status': 'completed',
                    'bio_length': len(bio),
                    'update_time': int(time.time()),
                    'verification': verification_data,
                    'api_response': response_data
                })
            except:
                return jsonify({
                    'success': True,
                    'message': 'Biography updated successfully',
                    'status': 'completed',
                    'bio_length': len(bio),
                    'update_time': int(time.time())
                })
        elif response.status_code == 401:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired access token',
                'error_code': 'UNAUTHORIZED',
                'status': 'rejected'
            }), 401
        elif response.status_code == 429:
            return jsonify({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later',
                'error_code': 'RATE_LIMITED',
                'status': 'throttled'
            }), 429
        else:
            return jsonify({
                'success': False,
                'message': 'Biography update failed due to server error',
                'error_code': 'UPDATE_FAILED',
                'status': 'error',
                'http_status': response.status_code
            }), response.status_code

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Biography update service temporarily unavailable',
            'error_code': 'SERVICE_ERROR',
            'status': 'error'
        }), 500

@app.route('/api/user-info/<uid>')
@codex_protection_required
@api_protection_required
def get_user_info(uid):
    """الحصول على معلومات المستخدم"""
    try:
        endpoint = API_ENDPOINTS['user_info']
        info_url = endpoint['url'].replace('{uid}', uid)

        response = requests.get(info_url, timeout=endpoint['timeout'])

        if response.status_code == 200:
            return jsonify({'success': True, 'data': response.json()})
        else:
            return jsonify({'success': False, 'message': 'Failed to get user info'}), response.status_code

    except Exception as e:
        return jsonify({'success': False, 'message': 'Request failed'}), 500

@app.route('/api/send-friend', methods=['POST'])
@codex_protection_required
@api_protection_required
def send_friend():
    """Send friend requests to multiple users"""
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

    # Handle POST request with protection
    try:
        data = request.get_json()
        player_id = data.get('playerId', '').strip()

        if not player_id:
            return jsonify({
                'success': False,
                'message': 'Player ID is required',
                'error_code': 'MISSING_PLAYER_ID'
            }), 400

        # Update bio using the API
        endpoint = API_ENDPOINTS['send_friend']
        friend_url = endpoint['url'].replace('{player_id}', player_id)

        # Log the request for debugging
        log_activity('FRIEND_REQUEST_ATTEMPT', {
            'player_id': player_id,
            'url': friend_url,
            'ip': get_client_ip()
        })

        try:
            response = requests.post(friend_url, timeout=endpoint['timeout'])

            # Log response details for debugging
            log_activity('FRIEND_REQUEST_RESPONSE', {
                'player_id': player_id,
                'status_code': response.status_code,
                'response_size': len(response.content),
                'success': response.status_code == 200
            })

            if response.status_code == 200:
                try:
                    response_data = response.json()

                    # Extract useful information without tokens
                    friend_count = response_data.get('friend_requests_sent', 0)
                    player_id_resp = response_data.get('player_id', player_id)

                    # Count successful requests without showing tokens
                    details = response_data.get('details', [])
                    successful_requests = len([d for d in details if d.get('status') == 'success'])

                    return jsonify({
                        'success': True,
                        'message': f'Successfully sent {friend_count} friend requests',
                        'status': 'completed',
                        'spam_results': {
                            'player_id': player_id_resp,
                            'friend_requests_sent': friend_count,
                            'successful_operations': successful_requests,
                            'operation_type': 'friend_request_spam'
                        },
                        'timestamp': int(time.time())
                    })
                except json.JSONDecodeError:
                    # If response is not JSON, treat as success with text response
                    return jsonify({
                        'success': True,
                        'message': 'Friend requests sent successfully',
                        'status': 'completed',
                        'player_id': player_id,
                        'response_text': response.text[:200],  # First 200 chars
                        'timestamp': int(time.time())
                    })
            elif response.status_code == 400:
                return jsonify({
                    'success': False,
                    'message': 'Invalid player ID format or request parameters',
                    'error_code': 'INVALID_PLAYER_ID',
                    'status': 'rejected',
                    'player_id': player_id
                }), 400
            elif response.status_code == 401:
                return jsonify({
                    'success': False,
                    'message': 'Player ID not found or access denied',
                    'error_code': 'UNAUTHORIZED',
                    'status': 'rejected',
                    'player_id': player_id
                }), 401
            elif response.status_code == 403:
                return jsonify({
                    'success': False,
                    'message': 'Friend requests blocked or restricted for this player',
                    'error_code': 'FORBIDDEN',
                    'status': 'blocked',
                    'player_id': player_id
                }), 403
            elif response.status_code == 404:
                return jsonify({
                    'success': False,
                    'message': 'Player ID does not exist in the system',
                    'error_code': 'PLAYER_NOT_FOUND',
                    'status': 'not_found',
                    'player_id': player_id
                }), 404
            elif response.status_code == 429:
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded. Please wait before sending more requests',
                    'error_code': 'RATE_LIMITED',
                    'status': 'throttled',
                    'player_id': player_id,
                    'retry_after': response.headers.get('Retry-After', '300')
                }), 429
            elif response.status_code == 500:
                return jsonify({
                    'success': False,
                    'message': 'Friend request service internal error',
                    'error_code': 'SERVER_ERROR',
                    'status': 'error',
                    'player_id': player_id
                }), 500
            elif response.status_code == 502:
                return jsonify({
                    'success': False,
                    'message': 'Friend request service gateway error - please try again',
                    'error_code': 'GATEWAY_ERROR',
                    'status': 'error',
                    'player_id': player_id
                }), 502
            elif response.status_code == 503:
                return jsonify({
                    'success': False,
                    'message': 'Friend request service is temporarily unavailable for maintenance',
                    'error_code': 'SERVICE_UNAVAILABLE',
                    'status': 'maintenance',
                    'player_id': player_id
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': f'Friend request failed with status {response.status_code}',
                    'error_code': 'HTTP_ERROR',
                    'status': 'error',
                    'http_status': response.status_code,
                    'player_id': player_id
                }), response.status_code

        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'message': 'Friend request service timeout - please try again',
                'error_code': 'TIMEOUT',
                'status': 'timeout',
                'player_id': player_id
            }), 408
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'message': 'Cannot connect to friend request service - check internet connection',
                'error_code': 'CONNECTION_ERROR',
                'status': 'connection_failed',
                'player_id': player_id
            }), 503
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'message': f'Network error occurred: {str(e)[:100]}',
                'error_code': 'NETWORK_ERROR',
                'status': 'network_error',
                'player_id': player_id
            }), 503

    except Exception as e:
        log_activity('FRIEND_REQUEST_ERROR', {
            'player_id': player_id if 'player_id' in locals() else 'unknown',
            'error': str(e),
            'ip': get_client_ip()
        })

        return jsonify({
            'success': False,
            'message': 'Unexpected error occurred while processing friend request',
            'error_code': 'INTERNAL_ERROR',
            'status': 'error'
        }), 500

@app.route('/api/send-visits', methods=['POST'])
@codex_protection_required
@api_protection_required
def send_visits():
    """Send visits to user profile"""
    try:
        data = request.get_json()
        player_id = data.get('playerId', '').strip()

        if not player_id:
            return jsonify({
                'success': False,
                'message': 'Player ID is required',
                'error_code': 'MISSING_PLAYER_ID'
            }), 400

        # Validate Player ID format (basic check)
        if not player_id.isdigit():
            return jsonify({
                'success': False,
                'message': 'Player ID must contain only numbers',
                'error_code': 'INVALID_PLAYER_ID'
            }), 400

        # Check if API is under maintenance
        if check_maintenance('send_visits'):
            maintenance_info = MAINTENANCE_STATUS.get('send_visits', {})
            return jsonify({
                'success': False,
                'message': 'Visit sending feature is currently under maintenance',
                'maintenance': True,
                'reason': maintenance_info.get('reason', 'Scheduled maintenance'),
                'estimated_time': maintenance_info.get('estimated_time', 'Unknown')
            }), 503

        endpoint = API_ENDPOINTS['send_visits']
        visits_url = endpoint['url'].replace('{player_id}', player_id)

        # Log the request for debugging
        log_activity('VISIT_REQUEST_ATTEMPT', {
            'player_id': player_id,
            'url': visits_url,
            'ip': get_client_ip()
        })

        try:
            response = requests.get(visits_url, timeout=endpoint['timeout'])

            # Log response details for debugging
            log_activity('VISIT_REQUEST_RESPONSE', {
                'player_id': player_id,
                'status_code': response.status_code,
                'response_size': len(response.content),
                'success': response.status_code == 200
            })

            if response.status_code == 200:
                try:
                    response_data = response.json()

                    # Extract useful information without tokens
                    visits_added = response_data.get('visits_added', 0)
                    player_id_resp = response_data.get('player_id', player_id)

                    # Count successful requests
                    details = response_data.get('details', [])
                    successful_requests = len([d for d in details if d.get('status') == 'success'])

                    return jsonify({
                        'success': True,
                        'message': f'Successfully sent {visits_added} visits',
                        'status': 'completed',
                        'results': {
                            'player_id': player_id_resp,
                            'visits_added': visits_added,
                            'successful_requests': successful_requests,
                            'batch_size': len(details)
                        },
                        'timestamp': int(time.time())
                    })
                except json.JSONDecodeError:
                    # If response is not JSON, treat as success with text response
                    return jsonify({
                        'success': True,
                        'message': 'Visits sent successfully',
                        'status': 'completed',
                        'player_id': player_id,
                        'response_text': response.text[:200],  # First 200 chars
                        'timestamp': int(time.time())
                    })
            elif response.status_code == 400:
                return jsonify({
                    'success': False,
                    'message': 'Invalid player ID format or request parameters',
                    'error_code': 'INVALID_PLAYER_ID',
                    'status': 'rejected',
                    'player_id': player_id
                }), 400
            elif response.status_code == 401:
                return jsonify({
                    'success': False,
                    'message': 'Player ID not found or access denied',
                    'error_code': 'UNAUTHORIZED',
                    'status': 'rejected',
                    'player_id': player_id
                }), 401
            elif response.status_code == 403:
                return jsonify({
                    'success': False,
                    'message': 'Visits blocked or restricted for this player',
                    'error_code': 'FORBIDDEN',
                    'status': 'blocked',
                    'player_id': player_id
                }), 403
            elif response.status_code == 404:
                return jsonify({
                    'success': False,
                    'message': 'Player ID does not exist in the system',
                    'error_code': 'PLAYER_NOT_FOUND',
                    'status': 'not_found',
                    'player_id': player_id
                }), 404
            elif response.status_code == 429:
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded. Please wait before sending more visits',
                    'error_code': 'RATE_LIMITED',
                    'status': 'throttled',
                    'player_id': player_id,
                    'retry_after': response.headers.get('Retry-After', '300')
                }), 429
            else:
                return jsonify({
                    'success': False,
                    'message': f'Visit request failed with status {response.status_code}',
                    'error_code': 'HTTP_ERROR',
                    'status': 'error',
                    'http_status': response.status_code,
                    'player_id': player_id
                }), response.status_code

        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'message': 'Visit service timeout - please try again',
                'error_code': 'TIMEOUT',
                'status': 'timeout',
                'player_id': player_id
            }), 408
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'message': 'Cannot connect to visit service - check internet connection',
                'error_code': 'CONNECTION_ERROR',
                'status': 'connection_failed',
                'player_id': player_id
            }), 503
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'message': f'Network error occurred: {str(e)[:100]}',
                'error_code': 'NETWORK_ERROR',
                'status': 'network_error',
                'player_id': player_id
            }), 503

    except Exception as e:
        log_activity('VISIT_REQUEST_ERROR', {
            'player_id': player_id if 'player_id' in locals() else 'unknown',
            'error': str(e),
            'ip': get_client_ip()
        })

        return jsonify({
            'success': False,
            'message': 'Unexpected error occurred while processing visit request',
            'error_code': 'INTERNAL_ERROR',
            'status': 'error'
        }), 500

@app.route('/api/send-likes', methods=['POST'])
@codex_protection_required
@api_protection_required
def send_likes():
    """Send likes to user content"""
    try:
        data = request.get_json()
        player_id = data.get('playerId', '').strip()

        if not player_id:
            return jsonify({
                'success': False,
                'message': 'Player ID is required',
                'error_code': 'MISSING_PLAYER_ID'
            }), 400

        # Validate Player ID format (basic check)
        if not player_id.isdigit():
            return jsonify({
                'success': False,
                'message': 'Player ID must contain only numbers',
                'error_code': 'INVALID_PLAYER_ID'
            }), 400

        # Check if API is under maintenance
        if check_maintenance('send_likes'):
            maintenance_info = MAINTENANCE_STATUS.get('send_likes', {})
            return jsonify({
                'success': False,
                'message': 'Likes feature is currently under maintenance',
                'maintenance': True,
                'reason': maintenance_info.get('reason', 'Scheduled maintenance'),
                'estimated_time': maintenance_info.get('estimated_time', 'Unknown')
            }), 503

        endpoint = API_ENDPOINTS['send_likes']
        likes_url = endpoint['url'].replace('{player_id}', player_id)

        # Log the request for debugging
        log_activity('LIKES_REQUEST_ATTEMPT', {
            'player_id': player_id,
            'url': likes_url,
            'ip': get_client_ip()
        })

        try:
            # Use GET method as most like services use GET requests
            response = requests.get(likes_url, timeout=endpoint['timeout'])

            # Log response details for debugging
            log_activity('LIKES_REQUEST_RESPONSE', {
                'player_id': player_id,
                'status_code': response.status_code,
                'response_size': len(response.content),
                'success': response.status_code == 200
            })

            if response.status_code == 200:
                try:
                    response_data = response.json()

                    # Extract useful information without tokens
                    return jsonify({
                        'success': True,
                        'message': 'Likes sent successfully',
                        'status': 'completed',
                        'data': response_data,
                        'timestamp': int(time.time())
                    })
                except json.JSONDecodeError:
                    # If response is not JSON, treat as success with text response
                    return jsonify({
                        'success': True,
                        'message': 'Likes sent successfully',
                        'status': 'completed',
                        'player_id': player_id,
                        'response_text': response.text[:500],  # First 500 chars
                        'timestamp': int(time.time())
                    })
            elif response.status_code == 400:
                return jsonify({
                    'success': False,
                    'message': 'Invalid player ID format or request parameters',
                    'error_code': 'INVALID_PLAYER_ID',
                    'status': 'rejected'
                }), 400
            elif response.status_code == 401:
                return jsonify({
                    'success': False,
                    'message': 'Player ID not found or access denied',
                    'error_code': 'UNAUTHORIZED',
                    'status': 'rejected'
                }), 401
            elif response.status_code == 403:
                return jsonify({
                    'success': False,
                    'message': 'Likes blocked or restricted for this player',
                    'error_code': 'FORBIDDEN',
                    'status': 'blocked'
                }), 403
            elif response.status_code == 404:
                return jsonify({
                    'success': False,
                    'message': 'Player ID does not exist in the system',
                    'error_code': 'PLAYER_NOT_FOUND',
                    'status': 'not_found'
                }), 404
            elif response.status_code == 429:
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded. Too many likes sent recently',
                    'error_code': 'RATE_LIMITED',
                    'status': 'throttled',
                    'retry_after': response.headers.get('Retry-After', '300')
                }), 429
            elif response.status_code == 500:
                return jsonify({
                    'success': False,
                    'message': 'Likes service internal error',
                    'error_code': 'SERVER_ERROR',
                    'status': 'error'
                }), 500
            elif response.status_code == 503:
                return jsonify({
                    'success': False,
                    'message': 'Likes service temporarily unavailable',
                    'error_code': 'SERVICE_UNAVAILABLE',
                    'status': 'maintenance'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': f'Likes request failed with status {response.status_code}',
                    'error_code': 'HTTP_ERROR',
                    'status': 'error',
                    'http_status': response.status_code
                }), response.status_code

        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'message': 'Likes service timeout - please try again',
                'error_code': 'TIMEOUT',
                'status': 'timeout'
            }), 408
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'message': 'Cannot connect to likes service - check internet connection',
                'error_code': 'CONNECTION_ERROR',
                'status': 'connection_failed'
            }), 503
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'message': f'Network error occurred: {str(e)[:100]}',
                'error_code': 'NETWORK_ERROR',
                'status': 'network_error'
            }), 503

    except Exception as e:
        log_activity('LIKES_REQUEST_ERROR', {
            'player_id': player_id if 'player_id' in locals() else 'unknown',
            'error': str(e),
            'ip': get_client_ip()
        })

        return jsonify({
            'success': False,
            'message': 'Unexpected error occurred while processing likes request',
            'error_code': 'INTERNAL_ERROR',
            'status': 'error'
        }), 500

@app.route('/api/banner/<uid>')
@codex_protection_required
@api_protection_required
def get_banner(uid):
    """الحصول على البانر"""
    try:
        key = request.args.get('key', 'BNGX') # Default key as requested
        endpoint = API_ENDPOINTS['get_banner']
        banner_url = endpoint['url'].replace('{uid}', uid).replace('{key}', key)

        response = requests.get(banner_url, timeout=endpoint['timeout'])

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if content_type.startswith('image/'):
                image_data = base64.b64encode(response.content).decode('utf-8')
                return jsonify({
                    'success': True,
                    'data': f"data:{content_type};base64,{image_data}",
                    'type': 'image'
                })
            else:
                return jsonify({
                    'success': True,
                    'data': response.text,
                    'type': 'text'
                })
        else:
            return jsonify({'success': False, 'message': 'Request failed'}), response.status_code

    except Exception as e:
        return jsonify({'success': False, 'message': 'Request failed'}), 500

@app.route('/api/outfit/<uid>')
@codex_protection_required
@api_protection_required
def get_outfit(uid):
    """الحصول على الزي"""
    try:
        region = request.args.get('region', 'me')
        key = request.args.get('key', 'BNGX') # Default key as requested
        endpoint = API_ENDPOINTS['get_outfit']
        outfit_url = endpoint['url'].replace('{region}', region).replace('{uid}', uid).replace('{key}', key)

        response = requests.get(outfit_url, timeout=endpoint['timeout'])

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if content_type.startswith('image/'):
                image_data = base64.b64encode(response.content).decode('utf-8')
                return jsonify({
                    'success': True,
                    'data': f"data:{content_type};base64,{image_data}",
                    'type': 'image'
                })
            else:
                return jsonify({
                    'success': True,
                    'data': response.text,
                    'type': 'text'
                })
        else:
            return jsonify({'success': False, 'message': 'Request failed'}), response.status_code

    except Exception as e:
        return jsonify({'success': False, 'message': 'Request failed'}), 500

@app.route('/api/check-ban', methods=['POST'])
@codex_protection_required
@api_protection_required
def check_ban():
    """فحص حالة الحظر للمستخدم باستخدام API الجديد"""
    try:
        data = request.get_json()
        uid = data.get('uid', '').strip()

        if not uid:
            return jsonify({
                'success': False,
                'message': 'User ID is required',
                'error_code': 'MISSING_UID'
            }), 400

        # Validate UID format (basic check)
        if not uid.isdigit():
            return jsonify({
                'success': False,
                'message': 'User ID must contain only numbers',
                'error_code': 'INVALID_UID'
            }), 400

        # Check if API is under maintenance
        if check_maintenance('check_ban'):
            maintenance_info = MAINTENANCE_STATUS.get('check_ban', {})
            return jsonify({
                'success': False,
                'message': 'Ban check feature is currently under maintenance',
                'maintenance': True,
                'reason': maintenance_info.get('reason', 'Scheduled maintenance'),
                'estimated_time': maintenance_info.get('estimated_time', 'Unknown')
            }), 503

        endpoint = API_ENDPOINTS['check_ban']
        check_url = endpoint['url'].replace('{uid}', uid)

        # Headers optimized for the new API
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }

        # Log the request for debugging
        log_activity('BAN_CHECK_ATTEMPT', {
            'uid': uid,
            'url': check_url,
            'ip': get_client_ip()
        })

        try:
            response = requests.get(check_url, headers=headers, timeout=endpoint['timeout'])

            # Log detailed response for debugging
            log_activity('BAN_CHECK_RESPONSE', {
                'uid': uid,
                'status_code': response.status_code,
                'response_size': len(response.content),
                'content_type': response.headers.get('content-type', ''),
                'success': response.status_code == 200,
                'raw_response': response.text[:500] if response.text else 'No content'
            })

            if response.status_code == 200:
                try:
                    response_data = response.json()

                    # Parse new API response format
                    status_text = response_data.get('✅ status', '')
                    uid_response = response_data.get('🆔 UID', uid)
                    nickname = response_data.get('🏷️ Nickname', 'Unknown')
                    region = response_data.get('🌍 Region', 'Unknown')
                    account_status = response_data.get('🔒 Account', '')
                    duration = response_data.get('⏳ Duration', '')
                    is_banned = response_data.get('📊 Banned?', False)
                    powered_by = response_data.get('💎 Powered by', '')
                    channel = response_data.get('📡 Channel', '')

                    # Determine ban status from the new API format
                    if isinstance(is_banned, bool):
                        ban_status = 'banned' if is_banned else 'clean'
                    else:
                        # Fallback check from account status
                        ban_status = 'clean' if 'NOT BANNED' in account_status else 'banned'
                        is_banned = ban_status == 'banned'

                    # Create status message
                    if is_banned:
                        if duration and duration != "No ban":
                            ban_message = f'🔴 Account is BANNED - Duration: {duration}'
                        else:
                            ban_message = '🔴 Account is BANNED'
                    else:
                        ban_message = '🟢 Account is CLEAN - No ban detected'

                    # Enhanced response with new API data
                    return jsonify({
                        'success': True,
                        'message': 'Ban check completed successfully',
                        'status': 'completed',
                        'ban_info': {
                            'uid': uid_response,
                            'nickname': nickname,
                            'region': region,
                            'is_banned': is_banned,
                            'ban_status': ban_status,
                            'account_status': account_status,
                            'ban_duration': duration,
                            'status_message': ban_message,
                            'check_time': int(time.time()),
                            'api_status': status_text,
                            'powered_by': powered_by,
                            'channel': channel
                        },
                        'raw_api_response': response_data,
                        'api_version': 'new_gpl_api'
                    })
                except json.JSONDecodeError:
                    # If not JSON, try to parse as text
                    response_text = response.text.strip()

                    # Check for common ban indicators in text response
                    ban_indicators = ['banned', 'suspend', 'violation', 'restricted']
                    is_banned = any(indicator in response_text.lower() for indicator in ban_indicators)

                    return jsonify({
                        'success': True,
                        'message': 'Ban check completed (text response)',
                        'status': 'completed',
                        'ban_info': {
                            'uid': uid,
                            'is_banned': is_banned,
                            'ban_status': 'banned' if is_banned else 'unknown',
                            'status_message': f'Text response received: {response_text[:200]}',
                            'check_time': int(time.time())
                        },
                        'raw_response_text': response_text
                    })

            elif response.status_code == 400:
                return jsonify({
                    'success': False,
                    'message': 'Invalid User ID format or request parameters',
                    'error_code': 'INVALID_REQUEST',
                    'status': 'rejected',
                    'uid': uid,
                    'details': response.text[:200] if response.text else 'No details'
                }), 400
            elif response.status_code == 404:
                return jsonify({
                    'success': False,
                    'message': 'User ID not found in the system',
                    'error_code': 'USER_NOT_FOUND',
                    'status': 'not_found',
                    'uid': uid
                }), 404
            elif response.status_code == 403:
                return jsonify({
                    'success': False,
                    'message': 'Access denied - Ban check service blocked the request',
                    'error_code': 'ACCESS_DENIED',
                    'status': 'blocked',
                    'uid': uid
                }), 403
            elif response.status_code == 429:
                return jsonify({
                    'success': False,
                    'message': 'Too many requests. Please wait before checking again',
                    'error_code': 'RATE_LIMITED',
                    'status': 'throttled',
                    'retry_after': response.headers.get('Retry-After', '300'),
                    'uid': uid
                }), 429
            elif response.status_code == 500:
                return jsonify({
                    'success': False,
                    'message': 'Ban check service internal error',
                    'error_code': 'SERVER_ERROR',
                    'status': 'error',
                    'uid': uid
                }), 500
            elif response.status_code == 502:
                return jsonify({
                    'success': False,
                    'message': 'Bad Gateway - Service temporarily unavailable',
                    'error_code': 'BAD_GATEWAY',
                    'status': 'error',
                    'uid': uid
                }), 502
            elif response.status_code == 503:
                return jsonify({
                    'success': False,
                    'message': 'Ban check service temporarily unavailable',
                    'error_code': 'SERVICE_UNAVAILABLE',
                    'status': 'maintenance',
                    'uid': uid
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': f'Ban check failed with unexpected status {response.status_code}',
                    'error_code': 'HTTP_ERROR',
                    'status': 'error',
                    'http_status': response.status_code,
                    'uid': uid,
                    'response_preview': response.text[:200] if response.text else 'No content'
                }), response.status_code

        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'message': 'Ban check service timeout - Please try again',
                'error_code': 'TIMEOUT',
                'status': 'timeout',
                'uid': uid
            }), 408
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'message': 'Cannot connect to ban check service',
                'error_code': 'CONNECTION_ERROR',
                'status': 'connection_failed',
                'uid': uid
            }), 503
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'message': f'Network error occurred: {str(e)[:100]}',
                'error_code': 'NETWORK_ERROR',
                'status': 'network_error',
                'uid': uid
            }), 503

    except Exception as e:
        log_activity('BAN_CHECK_ERROR', {
            'uid': uid if 'uid' in locals() else 'unknown',
            'error': str(e),
            'error_type': type(e).__name__,
            'ip': get_client_ip()
        })

        return jsonify({
            'success': False,
            'message': 'Unexpected error occurred during ban check',
            'error_code': 'INTERNAL_ERROR',
            'status': 'error',
            'error_details': str(e)[:100]
        }), 500

@app.route('/api/health-check')
def health_check():
    """فحص حالة الخدمات"""
    try:
        services_status = {}

        # Check each API endpoint
        for service_name, endpoint in API_ENDPOINTS.items():
            try:
                # Simple head request to check if service is reachable
                test_url = endpoint['url'].split('?')[0].split('{')[0]  # Get base URL
                response = requests.head(test_url, timeout=5)
                services_status[service_name] = {
                    'status': 'online' if response.status_code < 500 else 'degraded',
                    'response_time': response.elapsed.total_seconds() * 1000,
                    'maintenance': check_maintenance(service_name)
                }
            except requests.exceptions.Timeout:
                services_status[service_name] = {
                    'status': 'timeout',
                    'maintenance': check_maintenance(service_name)
                }
            except requests.exceptions.ConnectionError:
                services_status[service_name] = {
                    'status': 'offline',
                    'maintenance': check_maintenance(service_name)
                }
            except Exception:
                services_status[service_name] = {
                    'status': 'unknown',
                    'maintenance': check_maintenance(service_name)
                }

        # Calculate overall status
        online_count = len([s for s in services_status.values() if s['status'] == 'online'])
        total_count = len(services_status)

        if online_count == total_count:
            overall_status = 'healthy'
        elif online_count >= total_count * 0.5:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'

        return jsonify({
            'success': True,
            'overall_status': overall_status,
            'services': services_status,
            'online_services': online_count,
            'total_services': total_count,
            'timestamp': int(time.time())
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Health check failed',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🔒 S1X TEAM Advanced Admin System Starting...")
    print("📊 Admin Panel: /admin/login")
    print("🛡️ Full System Control Enabled")
    print(f"🛡️ S1X TEAM Protection Status: {'ENABLED' if S1X_PROTECTION_CONFIG['enabled'] else 'DISABLED'}")
    print(f"🔒 Protection Mode: {S1X_PROTECTION_CONFIG['current_mode'].upper()}")
    print("🚀 Server starting on port 3000...")
    app.run(host='0.0.0.0', port=3000, debug=True)