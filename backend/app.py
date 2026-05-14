from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
import subprocess
import tempfile
import os
import time
import uuid
import json
from datetime import datetime, timedelta
from functools import wraps
import threading

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'codejudge-secret-dev-key-2024')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
CORS(app, supports_credentials=True, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
bcrypt = Bcrypt(app)

# ── Global JSON Error Handlers ─────────────────────────────────────────────────
@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    app.logger.error(traceback.format_exc())
    return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(405)
def handle_405(e):
    return jsonify({'error': 'Method not allowed'}), 405

# ── DB Connection ──────────────────────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'codejudge123'),
        database=os.environ.get('DB_NAME', 'codejudge'),
        autocommit=False,
        connection_timeout=10
    )

# ── Auth Decorator ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

# ── Code Execution Engine ──────────────────────────────────────────────────────
LANGUAGE_CONFIG = {
    'python': {
        'extension': '.py',
        'run_cmd': ['python3', '{file}'],
        'timeout': 10
    },
    'javascript': {
        'extension': '.js',
        'run_cmd': ['node', '{file}'],
        'timeout': 10
    },
    'cpp': {
        'extension': '.cpp',
        'compile_cmd': ['g++', '-o', '{exe}', '{file}', '-std=c++17'],
        'run_cmd': ['{exe}'],
        'timeout': 15
    },
    'java': {
        'extension': '.java',
        'compile_cmd': ['javac', '{file}'],
        'run_cmd': ['java', '-cp', '{dir}', 'Main'],
        'timeout': 15
    }
}

def execute_code(code, language, stdin_input='', timeout=10):
    """Execute code safely with timeout."""
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        return {'status': 'error', 'output': f'Unsupported language: {language}', 'time': 0}

    with tempfile.TemporaryDirectory() as tmpdir:
        ext = config['extension']
        # Java must use Main.java
        filename = 'Main' + ext if language == 'java' else f'solution{ext}'
        filepath = os.path.join(tmpdir, filename)
        exe_path = os.path.join(tmpdir, 'solution')

        with open(filepath, 'w') as f:
            f.write(code)

        # Compile if needed
        if 'compile_cmd' in config:
            compile_cmd = [
                c.replace('{file}', filepath).replace('{exe}', exe_path).replace('{dir}', tmpdir)
                for c in config['compile_cmd']
            ]
            try:
                result = subprocess.run(
                    compile_cmd, capture_output=True, text=True, timeout=30, cwd=tmpdir
                )
                if result.returncode != 0:
                    return {
                        'status': 'compilation_error',
                        'output': result.stderr,
                        'time': 0
                    }
            except subprocess.TimeoutExpired:
                return {'status': 'tle', 'output': 'Compilation timed out', 'time': 0}

        # Run
        run_cmd = [
            c.replace('{file}', filepath).replace('{exe}', exe_path).replace('{dir}', tmpdir)
            for c in config['run_cmd']
        ]

        start = time.time()
        try:
            result = subprocess.run(
                run_cmd,
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=config['timeout'],
                cwd=tmpdir,
                # Security: limit resources
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
            )
            elapsed = round((time.time() - start) * 1000)  # ms

            if result.returncode != 0:
                return {
                    'status': 'runtime_error',
                    'output': result.stderr or result.stdout,
                    'time': elapsed
                }

            return {
                'status': 'success',
                'output': result.stdout,
                'time': elapsed
            }
        except subprocess.TimeoutExpired:
            return {'status': 'tle', 'output': 'Time Limit Exceeded', 'time': config['timeout'] * 1000}
        except Exception as e:
            return {'status': 'error', 'output': str(e), 'time': 0}


VERDICT_MAP = {
    'success': 'AC',
    'runtime_error': 'RE',
    'compilation_error': 'CE',
    'tle': 'TLE',
    'error': 'RE',
}

def judge_submission(code, language, test_cases):
    """Run code against all test cases."""
    results = []
    all_passed = True

    for i, tc in enumerate(test_cases):
        result = execute_code(code, language, tc.get('input', ''))
        expected = tc.get('expected_output', '').strip()
        actual = result.get('output', '').strip()

        passed = result['status'] == 'success' and actual == expected
        if not passed:
            all_passed = False

        tc_verdict = 'AC' if passed else VERDICT_MAP.get(result['status'], 'WA')
        results.append({
            'test_case': i + 1,
            'status': tc_verdict,
            'passed': passed,
            'time': result['time'],
            'expected': expected if not tc.get('hidden', False) else '***',
            'actual': actual if not tc.get('hidden', False) else ('***' if not passed else '***'),
            'input': tc.get('input', '') if not tc.get('hidden', False) else '***'
        })

    overall = 'AC' if all_passed else (results[0]['status'] if results else 'WA')
    return {
        'verdict': overall,
        'all_passed': all_passed,
        'test_results': results,
        'passed_count': sum(1 for r in results if r['passed']),
        'total_count': len(results)
    }


# ── Auth Routes ────────────────────────────────────────────────────────────────
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not all([username, email, password]):
        return jsonify({'error': 'All fields required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    hashed = bcrypt.generate_password_hash(password).decode('utf-8')

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute('SELECT id FROM users WHERE username=%s OR email=%s', (username, email))
        if cursor.fetchone():
            return jsonify({'error': 'Username or email already exists'}), 409

        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
            (username, email, hashed)
        )
        db.commit()
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['username'] = username
        return jsonify({'message': 'Registered successfully', 'user': {'id': user_id, 'username': username}})
    finally:
        cursor.close()
        db.close()


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute('SELECT * FROM users WHERE username=%s OR email=%s', (username, username))
        user = cursor.fetchone()
        if not user or not bcrypt.check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({
            'message': 'Login successful',
            'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}
        })
    finally:
        cursor.close()
        db.close()


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})


@app.route('/api/auth/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({'user': None})
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            'SELECT id, username, email, created_at FROM users WHERE id=%s',
            (session['user_id'],)
        )
        user = cursor.fetchone()
        if user and user.get('created_at'):
            user['created_at'] = user['created_at'].isoformat()
        return jsonify({'user': user})
    finally:
        cursor.close()
        db.close()


# ── Problem Routes ─────────────────────────────────────────────────────────────
@app.route('/api/problems', methods=['GET'])
def get_problems():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        user_id = session.get('user_id')
        if user_id:
            cursor.execute('''
                SELECT p.id, p.title, p.difficulty, p.tags, p.acceptance_rate,
                       MAX(CASE WHEN s.verdict = 'AC' THEN 'AC' ELSE s.verdict END) as user_verdict
                FROM problems p
                LEFT JOIN submissions s ON s.problem_id = p.id AND s.user_id = %s
                WHERE p.is_active = 1
                GROUP BY p.id
                ORDER BY p.id
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT id, title, difficulty, tags, acceptance_rate
                FROM problems WHERE is_active = 1 ORDER BY id
            ''')
        problems = cursor.fetchall()
        for p in problems:
            if p.get('tags'):
                p['tags'] = json.loads(p['tags']) if isinstance(p['tags'], str) else p['tags']
        return jsonify({'problems': problems})
    finally:
        cursor.close()
        db.close()


@app.route('/api/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute('SELECT * FROM problems WHERE id=%s AND is_active=1', (problem_id,))
        problem = cursor.fetchone()
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404

        # Parse JSON fields
        for field in ['tags', 'examples', 'constraints']:
            if problem.get(field) and isinstance(problem[field], str):
                try:
                    problem[field] = json.loads(problem[field])
                except:
                    pass

        # Get non-hidden test cases for display
        cursor.execute(
            'SELECT id, input, expected_output, is_hidden FROM test_cases WHERE problem_id=%s',
            (problem_id,)
        )
        test_cases = cursor.fetchall()
        problem['sample_test_cases'] = [tc for tc in test_cases if not tc['is_hidden']]

        return jsonify({'problem': problem})
    finally:
        cursor.close()
        db.close()


# ── Submission Routes ──────────────────────────────────────────────────────────
@app.route('/api/submit', methods=['POST'])
@login_required
def submit():
    data = request.json
    problem_id = data.get('problem_id')
    code = data.get('code', '')
    language = data.get('language', 'python')

    if not code.strip():
        return jsonify({'error': 'Code cannot be empty'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # Get all test cases
        cursor.execute(
            'SELECT input, expected_output, is_hidden as hidden FROM test_cases WHERE problem_id=%s',
            (problem_id,)
        )
        test_cases = cursor.fetchall()
        if not test_cases:
            return jsonify({'error': 'No test cases found'}), 400

        # Convert is_hidden to bool
        for tc in test_cases:
            tc['hidden'] = bool(tc['hidden'])

        # Judge
        result = judge_submission(code, language, test_cases)

        # Save submission
        cursor.execute('''
            INSERT INTO submissions (user_id, problem_id, code, language, verdict,
                                     passed_cases, total_cases, exec_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            session['user_id'], problem_id, code, language,
            result['verdict'], result['passed_count'], result['total_count'],
            max((r['time'] for r in result['test_results']), default=0)
        ))
        db.commit()
        submission_id = cursor.lastrowid

        # Update acceptance rate
        cursor.execute('''
            UPDATE problems SET
                acceptance_rate = ROUND(
                    (SELECT COUNT(DISTINCT user_id) FROM submissions
                     WHERE problem_id=%s AND verdict='AC') * 100.0 /
                    NULLIF((SELECT COUNT(DISTINCT user_id) FROM submissions WHERE problem_id=%s), 0),
                1)
            WHERE id=%s
        ''', (problem_id, problem_id, problem_id))
        db.commit()

        result['submission_id'] = submission_id
        return jsonify(result)
    finally:
        cursor.close()
        db.close()


@app.route('/api/run', methods=['POST'])
def run_code():
    """Run code with custom input (no judging)."""
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'python')
    stdin = data.get('stdin', '')

    if not code.strip():
        return jsonify({'error': 'Code cannot be empty'}), 400

    result = execute_code(code, language, stdin)
    return jsonify(result)


@app.route('/api/submissions', methods=['GET'])
@login_required
def get_submissions():
    problem_id = request.args.get('problem_id')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        if problem_id:
            cursor.execute('''
                SELECT s.id, s.language, s.verdict, s.passed_cases, s.total_cases,
                       s.exec_time_ms, s.submitted_at, p.title as problem_title
                FROM submissions s JOIN problems p ON p.id = s.problem_id
                WHERE s.user_id=%s AND s.problem_id=%s
                ORDER BY s.submitted_at DESC LIMIT 20
            ''', (session['user_id'], problem_id))
        else:
            cursor.execute('''
                SELECT s.id, s.language, s.verdict, s.passed_cases, s.total_cases,
                       s.exec_time_ms, s.submitted_at, p.title as problem_title, p.id as problem_id
                FROM submissions s JOIN problems p ON p.id = s.problem_id
                WHERE s.user_id=%s
                ORDER BY s.submitted_at DESC LIMIT 50
            ''', (session['user_id'],))

        submissions = cursor.fetchall()
        for s in submissions:
            if s.get('submitted_at'):
                s['submitted_at'] = s['submitted_at'].isoformat()
        return jsonify({'submissions': submissions})
    finally:
        cursor.close()
        db.close()


@app.route('/api/submissions/<int:sub_id>', methods=['GET'])
@login_required
def get_submission(sub_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT s.*, p.title as problem_title
            FROM submissions s JOIN problems p ON p.id = s.problem_id
            WHERE s.id=%s AND s.user_id=%s
        ''', (sub_id, session['user_id']))
        sub = cursor.fetchone()
        if not sub:
            return jsonify({'error': 'Not found'}), 404
        if sub.get('submitted_at'):
            sub['submitted_at'] = sub['submitted_at'].isoformat()
        return jsonify({'submission': sub})
    finally:
        cursor.close()
        db.close()


# ── Leaderboard ────────────────────────────────────────────────────────────────
@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT u.id, u.username,
                   COUNT(DISTINCT s.problem_id) as solved,
                   SUM(p.points) as total_points,
                   MIN(s.submitted_at) as last_solved
            FROM users u
            JOIN submissions s ON s.user_id = u.id AND s.verdict = 'AC'
            JOIN problems p ON p.id = s.problem_id
            GROUP BY u.id, u.username
            ORDER BY solved DESC, total_points DESC, last_solved ASC
            LIMIT 50
        ''')
        rows = cursor.fetchall()
        for i, r in enumerate(rows):
            r['rank'] = i + 1
            if r.get('last_solved'):
                r['last_solved'] = r['last_solved'].isoformat()
        return jsonify({'leaderboard': rows})
    finally:
        cursor.close()
        db.close()


# ── Stats ──────────────────────────────────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def stats():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute('SELECT COUNT(*) as total FROM users')
        users = cursor.fetchone()['total']
        cursor.execute('SELECT COUNT(*) as total FROM problems WHERE is_active=1')
        problems = cursor.fetchone()['total']
        cursor.execute('SELECT COUNT(*) as total FROM submissions')
        submissions = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM submissions WHERE verdict='AC'")
        accepted = cursor.fetchone()['total']
        return jsonify({
            'users': users, 'problems': problems,
            'submissions': submissions, 'accepted': accepted
        })
    finally:
        cursor.close()
        db.close()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)