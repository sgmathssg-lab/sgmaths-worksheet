from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile, os
from make_worksheet import build_pdf, QUESTIONS

app = Flask(__name__)
CORS(app)   # allows your WordPress site to call this server

ALL_TOPICS = ["Fractions", "Angles & Geometry", "Whole Numbers",
              "Decimals", "Data & Tables", "Word Problems"]

@app.route("/")
def index():
    return "SGMaths Worksheet Generator is running."

@app.route("/generate", methods=["POST"])
def generate():
    data           = request.get_json(force=True)
    topics         = data.get("topics", ALL_TOPICS)        # list of topic strings
    include_answers = data.get("include_answers", False)   # bool

    # Validate topics
    topics = [t for t in topics if t in ALL_TOPICS]
    if not topics:
        topics = ALL_TOPICS

    # Generate PDF into a temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmp_path = f.name

    try:
        build_pdf(tmp_path, selected_topics=topics, include_answers=include_answers)
        filename = "sgmaths_worksheet_answers.pdf" if include_answers else "sgmaths_worksheet.pdf"
        return send_file(tmp_path, as_attachment=True,
                         download_name=filename,
                         mimetype="application/pdf")
    finally:
        # Clean up temp file after sending
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
