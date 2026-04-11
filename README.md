# SGMaths Worksheet Generator

Auto-generates printable PDF maths worksheets for Singapore Primary students (P3–P5). Built for [sgmaths.sg](https://sgmaths.sg).

---

## Project Structure

```
sgmaths-worksheet-generator/
├── app.py                  # Flask API server
├── make_worksheet.py       # PDF generation engine (ReportLab)
├── wordpress-embed.html    # Drop-in widget for WordPress
├── requirements.txt
├── Procfile                # For Render / Heroku deployment
└── .gitignore
```

---

## How It Works

1. **`make_worksheet.py`** — Contains the full question bank (P3–P5) and the `build_pdf()` function that renders a styled, branded PDF using ReportLab.
2. **`app.py`** — A Flask server exposing a single `/generate` POST endpoint. Accepts `level`, `topics`, and `include_answers` in JSON; returns a PDF file download.
3. **`wordpress-embed.html`** — A self-contained HTML/CSS/JS widget. Paste it into a WordPress **Custom HTML** block. Lets visitors pick a level, select topics, and download a worksheet directly from the browser.

---

## API

### `POST /generate`

**Request body (JSON):**
```json
{
  "level": "P4",
  "topics": ["Fractions", "Decimals"],
  "include_answers": false
}
```

**Response:** PDF file download.

**Supported levels:** `P3`, `P4`, `P5`

| Level | Available Topics |
|-------|-----------------|
| P3 | Multiplication & Division, Fractions, Angles & Lines, Data & Graphs, Word Problems |
| P4 | Fractions, Angles & Geometry, Whole Numbers, Decimals, Data & Tables, Word Problems |
| P5 | Fractions, Ratio, Percentage, Area & Perimeter, Volume, Word Problems |

---

## Local Development

```bash
# 1. Clone the repo
git clone https://github.com/your-username/sgmaths-worksheet-generator.git
cd sgmaths-worksheet-generator

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
python app.py
# → Listening on http://localhost:5000

# 5. Generate PDFs directly (no server needed)
python make_worksheet.py
```

---

## Deploying to Render (free tier)

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service** → connect your repo.
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Deploy. Your service URL will be something like `https://sgmaths-worksheet.onrender.com`.
5. Update the `SGM_SERVER` variable in `wordpress-embed.html` to match.

---

## WordPress Integration

1. In your WordPress editor, add a **Custom HTML** block.
2. Paste the entire contents of `wordpress-embed.html`.
3. Publish. The widget appears inline on the page — no plugin required.

---

## Customising Questions

All questions live in `make_worksheet.py` in the `P3_QUESTIONS`, `P4_QUESTIONS`, and `P5_QUESTIONS` lists. Each question is a dict:

```python
dict(
    id=1,
    topic="Fractions",
    difficulty="Easy",       # "Easy" | "Medium" | "Hard"
    school="Nan Hua",
    marks=2,
    text="Write 3/4 as a decimal.",
    type="short",            # "short" | "mcq" | "draw"
    answer="0.75"
)
```

For MCQ questions, also include:
```python
opts=["A. 0.25", "B. 0.5", "C. 0.75", "D. 1.0"]
```

Fractions in question text are written as `3/4` or `1 3/4` — they are automatically rendered as stacked fractions in the PDF.

---

## License

MIT — free to use, adapt, and share.
