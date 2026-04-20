# ============================================================
# CHANGES NEEDED IN app.py
# ============================================================
# Find wherever you define your LEVELS list/dict and add "P6".
# Example — if you have something like:
#
#   LEVELS = ["P4", "P5"]
#
# Change it to:
#
#   LEVELS = ["P4", "P5", "P6"]
#
# ============================================================
# Then, wherever you build your question pool (e.g. in a
# route like /generate or /worksheet), add a branch for P6:
#
#   from make_worksheet import P6_QUESTIONS   # (adjust import to match your file)
#
#   QUESTION_BANK = {
#       "P4": P4_QUESTIONS,
#       "P5": P5_QUESTIONS,
#       "P6": P6_QUESTIONS,   # <-- ADD THIS
#   }
#
# ============================================================
# If you have per-level topic dropdowns, also add:
#
#   TOPIC_MAP = {
#       "P4": P4_TOPICS,
#       "P5": P5_TOPICS,
#       "P6": P6_TOPICS,    # <-- ADD THIS
#   }
#
# ============================================================
# Minimal Flask route pattern (adapt to your existing style):
# ============================================================

from flask import Flask, request, send_file, jsonify
# from make_worksheet import QUESTION_BANK, TOPIC_MAP  # your existing import

app = Flask(__name__)

@app.route("/topics")
def get_topics():
    level = request.args.get("level", "P6")
    topics = TOPIC_MAP.get(level, [])
    return jsonify(topics)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    level = data.get("level")          # e.g. "P6"
    topic = data.get("topic")          # e.g. "Fractions"
    qtype = data.get("type")           # e.g. "MCQ", "SHORT_ANSWER", "LONG_ANSWER"
    num_q = int(data.get("num_q", 10))

    bank = QUESTION_BANK.get(level, {}).get(qtype, [])
    if topic and topic != "All":
        bank = [q for q in bank if q["topic"] == topic]

    import random
    selected = random.sample(bank, min(num_q, len(bank)))

    # Pass `selected` to your existing PDF generation function
    pdf_path = build_pdf(level, selected)   # your existing function
    return send_file(pdf_path, as_attachment=True)
