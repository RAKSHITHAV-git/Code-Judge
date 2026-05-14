# ⚡ CodeJudge

A full-stack competitive programming platform — built with **Python (Flask)**, **MySQL**, and vanilla **HTML/CSS/JS** with CodeMirror.

---

## 🚀 Quick Start (Docker)

```bash
chmod +x start.sh
./start.sh
```

Then open **http://localhost:3000**

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + Flask |
| Database | MySQL 8.0 |
| Frontend | Vanilla JS + CodeMirror 5 |
| Code Runner | Subprocess sandboxing |
| Web Server | Nginx (frontend) + Gunicorn (backend) |
| Containers | Docker + Docker Compose |

---

## 📁 Project Structure

```
codejudge/
├── backend/
│   ├── app.py              # Flask API (all routes)
│   ├── schema.sql          # DB schema + 12 seed problems
│   ├── requirements.txt    # Python deps
│   └── Dockerfile
├── frontend/
│   └── index.html          # Full SPA (single file)
├── docker/
│   └── nginx.conf          # Nginx proxy config
├── docker-compose.yml
└── start.sh
```

---

## 🎯 Features

### Problems
- 12 pre-loaded problems (Easy / Medium / Hard)
- Tags, difficulty badges, acceptance rates
- Rich markdown description + examples + constraints
- Filter by difficulty

### Code Editor
- **CodeMirror** editor with Dracula theme
- **4 languages**: Python 3, JavaScript (Node), C++ 17, Java
- Syntax highlighting + bracket matching
- Language-specific starter code templates

### Judge Engine
- Runs code against **all test cases** (hidden + visible)
- Detailed verdicts: **AC, WA, TLE, RE, CE**
- Per-test-case result breakdown
- Execution time measurement (milliseconds)
- Custom input runner (test your code with any input)

### Auth
- Register / Login / Logout
- Session-based auth (Flask sessions)
- Password hashing with bcrypt

### Leaderboard
- Ranked by problems solved, then total points, then time
- Gold/Silver/Bronze badges for top 3

### Submissions
- Full submission history per user
- Per-problem submission history in the editor panel

---

## 🔧 Manual Setup (No Docker)

### 1. MySQL
```sql
mysql -u root -p < backend/schema.sql
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
DB_HOST=localhost DB_USER=root DB_PASSWORD=yourpass python app.py
```

### 3. Frontend
Serve `frontend/index.html` with any static server:
```bash
cd frontend && python -m http.server 3000
```
Update `API` constant in `index.html` to `http://localhost:5000/api`.

---

## 📝 Adding Problems

Insert into MySQL directly:

```sql
INSERT INTO problems (title, slug, description, difficulty, tags, examples, constraints, points)
VALUES (
  'My Problem', 'my-problem',
  'Problem description here...',
  'Medium',
  '["Array", "DP"]',
  '[{"input": "5", "output": "25", "explanation": "5 squared is 25"}]',
  '["1 <= n <= 100"]',
  150
);

-- Add test cases
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden)
VALUES (LAST_INSERT_ID(), '5', '25', 0);
```

---

## ⚠️ Security Notes

This is a **development/demo** setup. For production:
- Run code execution in isolated Docker containers (not subprocess)
- Add rate limiting on `/api/submit` and `/api/run`
- Use proper secrets management (not hardcoded passwords)
- Add CSRF protection
- Enable HTTPS

---

## 🎨 Screenshots

The platform features:
- Dark theme with purple accent colors
- Split-pane editor layout (problem + editor side by side)
- Real-time verdict display with per-test-case breakdown
- Responsive leaderboard with medal badges
