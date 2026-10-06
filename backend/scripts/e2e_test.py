"""
SupportIQ -- E2E workflow test against a running backend.
Run with: venv/Scripts/python.exe scripts/e2e_test.py
"""
import sys
import json
import urllib.request
import urllib.error

BASE = 'http://localhost:8000/api/v1'
PASS = []
FAIL = []


def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(label, cond, detail=''):
    if cond:
        PASS.append(label)
        print(f'  [PASS] {label}')
    else:
        FAIL.append(label)
        print(f'  [FAIL] {label}  -- {detail}')


# ── 1. Health ──────────────────────────────────────────────────────────────
try:
    with urllib.request.urlopen('http://localhost:8000/health') as _r:
        _hd = json.loads(_r.read())
    _hs = 200
except Exception:
    _hs = 0
    _hd = {}
check('Health check', _hs == 200 and _hd.get('status') == 'ok', _hd)

# ── 2. Login as customer ───────────────────────────────────────────────────
s, d = req('POST', '/auth/login', {'email': 'customer@supportiq.dev', 'password': 'Customer@123'})
check('Customer login', s == 200 and 'access_token' in d, d)
tok_c = d.get('access_token', '')
user = d.get('user', {})
check('Role is CUSTOMER', user.get('role') == 'CUSTOMER')

# ── 3. Create conversation ─────────────────────────────────────────────────
s, d = req('POST', '/chat/conversations', {'title': 'E2E Test'}, tok_c)
check('Create conversation', s == 201 and 'id' in d, d)
conv_id = d.get('id', '')

# ── 4. Send message → real ML prediction ──────────────────────────────────
s, d = req('POST', '/chat/message', {'conversation_id': conv_id, 'message': 'I want to reset my password'}, tok_c)
check('Send message (200)', s == 200, d)
check('Intent returned', 'intent' in d and bool(d['intent']), d)
check('Confidence is float', isinstance(d.get('confidence'), float), d)
check('Sentiment returned', d.get('sentiment') in ('positive', 'negative', 'neutral'), d)
check('Bot reply non-empty', bool(d.get('bot_message', {}).get('content', '')), d)
print(f'         ML: intent={d.get("intent")} conf={d.get("confidence", 0):.2f} sent={d.get("sentiment")} escalated={d.get("escalated")}')

# ── 5. Escalation trigger ─────────────────────────────────────────────────
s2, d2 = req('POST', '/chat/message', {'conversation_id': conv_id, 'message': 'I want to speak to a human agent now'}, tok_c)
check('Escalation message (200)', s2 == 200, d2)
print(f'         Escalation: intent={d2.get("intent")} escalated={d2.get("escalated")} reason={d2.get("escalation_reason")}')

# ── 6. Create ticket ───────────────────────────────────────────────────────
s, d = req('POST', '/tickets', {'subject': 'Password reset broken', 'description': 'Cannot reset password', 'priority': 'HIGH'}, tok_c)
check('Create ticket (201)', s == 201 and 'ticket_number' in d, d)
ticket_id = d.get('id')
print(f'         Ticket: {d.get("ticket_number")} status={d.get("status")} priority={d.get("priority")}')

# ── 7. List customer tickets ───────────────────────────────────────────────
s, d = req('GET', '/tickets', token=tok_c)
check('Customer ticket list', s == 200 and isinstance(d, list) and len(d) > 0, d)

# ── 8. Login as admin ─────────────────────────────────────────────────────
s, d = req('POST', '/auth/login', {'email': 'admin@supportiq.dev', 'password': 'Admin@123'})
check('Admin login', s == 200 and 'access_token' in d, d)
tok_a = d.get('access_token', '')

# ── 9. Admin stats ────────────────────────────────────────────────────────
s, d = req('GET', '/admin/stats', token=tok_a)
check('Admin stats (200)', s == 200, d)
check('Stats keys present', all(k in d for k in ('total_users', 'total_tickets', 'open_tickets', 'escalated_tickets')), d)
print(f'         Stats: {d}')

# ── 10. Admin user list ───────────────────────────────────────────────────
s, d = req('GET', '/admin/users', token=tok_a)
check('Admin user list', s == 200 and isinstance(d, list) and len(d) >= 2, d)

# ── 11. Knowledge search ──────────────────────────────────────────────────
s, d = req('GET', '/knowledge/search?q=password', token=tok_a)
check('Knowledge search', s == 200 and len(d) > 0, d)
print(f'         Knowledge results: {len(d)}')

# ── 12. Login as agent ────────────────────────────────────────────────────
s, d = req('POST', '/auth/login', {'email': 'agent@supportiq.dev', 'password': 'Agent@123'})
check('Agent login', s == 200 and 'access_token' in d, d)

# ── 13. Admin update ticket status ───────────────────────────────────────
if ticket_id:
    s, d = req('PATCH', f'/tickets/{ticket_id}', {'status': 'IN_PROGRESS'}, tok_a)
    check('Update ticket to IN_PROGRESS', s == 200 and d.get('status') == 'IN_PROGRESS', d)

# ── Results ───────────────────────────────────────────────────────────────
print()
print(f'Results: {len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('Failed:', FAIL)
sys.exit(0 if not FAIL else 1)
