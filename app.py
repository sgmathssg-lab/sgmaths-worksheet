from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile, os
from make_worksheet import build_pdf, QUESTIONS

app = Flask(__name__)
CORS(app)

LEVELS = {
    "P1": {
        "topics": ["Numbers to 10", "Addition & Subtraction", "Word Problems"],
    },
    "P2": {
        "topics": ["Numbers to 1000", "Addition & Subtraction", "Word Problems"],
    },
    "P3": {
        "topics": ["Multiplication & Division", "Fractions", "Angles & Lines",
                   "Data & Graphs", "Word Problems"],
    },
    "P4": {
        "topics": ["Fractions", "Angles & Geometry", "Whole Numbers",
                   "Decimals", "Data & Tables", "Word Problems"],
    },
    "P5": {
        "topics": ["Triangles & Area", "Volume", "Fractions",
                   "Ratio", "Decimals & Measurement", "3D Solids & Views",
                   "Whole Numbers", "Word Problems"],
    },
    "P6": {
        "topics": ["Whole Numbers", "Fractions", "Decimals", "Percentage",
                   "Ratio", "Algebra", "Average", "Speed", "Measurement",
                   "Volume", "Perimeter & Area", "Geometry", "Data Analysis",
                   "Number Patterns", "Money", "Order of Operations", "Word Problems"],
    },
}

@app.route("/")
def index():
    return "SGMaths Worksheet Generator is running."

@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})

@app.route("/generate", methods=["POST"])
def generate():
    data            = request.get_json(force=True)
    level           = data.get("level", "P4")
    include_answers = data.get("include_answers", False)

    if level not in LEVELS:
        level = "P4"

    all_topics = LEVELS[level]["topics"]
    topics     = data.get("topics", all_topics)
    topics     = [t for t in topics if t in all_topics] or all_topics

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(tmp_fd)

    try:
        build_pdf(tmp_path, level=level,
                  selected_topics=topics,
                  include_answers=include_answers)

        fname = f"sgmaths_{level}_worksheet{'_answers' if include_answers else ''}.pdf"
        return send_file(tmp_path, as_attachment=True,
                         download_name=fname,
                         mimetype="application/pdf")
    except Exception as e:
        os.unlink(tmp_path)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
